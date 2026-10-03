from __future__ import annotations

import hmac
import json
import logging
import threading
import time
from collections import defaultdict, deque
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, field_validator

from .chunking import load_documents
from .config import Settings, load_settings
from .providers import Provider, ProviderError, build_provider
from .retrieval import BM25Index, Hit, tokenize

logger = logging.getLogger("docs-assistant")

NO_ANSWER = (
    "I could not find that in the documentation, so I would rather not guess. "
    "Try rephrasing the question, or contact support if it is urgent."
)
SNIPPET_CHARS = 300


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    history: list[HistoryMessage] = Field(default_factory=list, max_length=20)

    @field_validator("question")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("question must not be blank")
        return value


class SlidingWindowLimiter:
    def __init__(self, limit: int, window_seconds: float = 60.0) -> None:
        self.limit = limit
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> float | None:
        """Return None if allowed, otherwise the seconds to wait."""
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                return max(1.0, self.window - (now - hits[0]))
            hits.append(now)
            return None


def sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def sources_payload(hits: list[Hit]) -> list[dict[str, object]]:
    return [
        {
            "id": number,
            "file": hit.chunk.source,
            "title": hit.chunk.doc_title,
            "section": hit.chunk.heading,
            "snippet": hit.chunk.text[:SNIPPET_CHARS],
            "score": hit.score,
        }
        for number, hit in enumerate(hits, start=1)
    ]


def retrieval_query(
    question: str, history: list[HistoryMessage], index: BM25Index | None = None
) -> str:
    """Short follow-ups like "and annual?" borrow the previous question for retrieval,
    but only if they contain a term the docs know. Otherwise an off-topic message
    would inherit the previous topic and wrongly get an answer."""
    if len(tokenize(question)) >= 3:
        return question
    if index is not None and not index.knows_any(question):
        return question
    for message in reversed(history):
        if message.role == "user":
            return f"{message.content} {question}"
    return question


def select_hits(index: BM25Index, query: str, settings: Settings) -> list[Hit]:
    hits = index.search(query, settings.top_k)
    if not hits:
        return []
    best = hits[0]
    if best.score < settings.min_score or best.coverage < settings.min_coverage:
        return []
    return [hit for hit in hits if hit.score >= best.score * 0.4]


@dataclass
class State:
    index: BM25Index
    provider: Provider


def create_app(settings: Settings | None = None, provider: Provider | None = None) -> FastAPI:
    settings = settings or load_settings()
    state = State(
        index=BM25Index(load_documents(settings.docs_dir)),
        provider=provider or build_provider(settings),
    )
    limiter = SlidingWindowLimiter(settings.rate_limit_per_minute)

    app = FastAPI(title="AI Docs Assistant", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", "X-Admin-Token"],
    )

    @app.get("/api/health")
    def health() -> dict[str, object]:
        return {
            "status": "ok",
            "provider": state.provider.name,
            "model": state.provider.model,
            "documents": len({c.source for c in state.index.chunks}),
            "chunks": len(state.index.chunks),
        }

    @app.get("/api/sources")
    def sources() -> list[dict[str, object]]:
        counts: dict[str, int] = defaultdict(int)
        titles: dict[str, str] = {}
        for chunk in state.index.chunks:
            counts[chunk.source] += 1
            titles.setdefault(chunk.source, chunk.doc_title)
        return [{"file": f, "title": titles[f], "chunks": n} for f, n in counts.items()]

    @app.post("/api/chat", response_model=None)
    def chat(body: ChatRequest, request: Request) -> StreamingResponse | JSONResponse:
        client_key = request.client.host if request.client else "unknown"
        wait = limiter.check(client_key)
        if wait is not None:
            return JSONResponse(
                {"detail": "Too many requests. Please slow down."},
                status_code=429,
                headers={"Retry-After": str(int(wait))},
            )

        index, active = state.index, state.provider
        history = [{"role": m.role, "content": m.content} for m in body.history]

        def events() -> Iterator[str]:
            hits = select_hits(index, retrieval_query(body.question, body.history, index), settings)
            if not hits:
                yield sse("sources", [])
                yield sse("token", {"text": NO_ANSWER})
                yield sse("done", {"grounded": False})
                return
            yield sse("sources", sources_payload(hits))
            try:
                for piece in active.stream(body.question, history, hits):
                    yield sse("token", {"text": piece})
            except ProviderError as exc:
                yield sse("error", {"message": str(exc)})
                return
            except Exception:
                logger.exception("answer generation failed")
                yield sse("error", {"message": "Something went wrong while writing the answer."})
                return
            yield sse("done", {"grounded": True})

        return StreamingResponse(
            events(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    @app.post("/api/reindex")
    def reindex(x_admin_token: str | None = Header(default=None)) -> dict[str, int]:
        if not settings.admin_token:
            raise HTTPException(status_code=403, detail="Reindexing is disabled.")
        if not x_admin_token or not hmac.compare_digest(x_admin_token, settings.admin_token):
            raise HTTPException(status_code=401, detail="Invalid admin token.")
        chunks = load_documents(settings.docs_dir)
        state.index = BM25Index(chunks)
        return {"documents": len({c.source for c in chunks}), "chunks": len(chunks)}

    return app


app = create_app()
