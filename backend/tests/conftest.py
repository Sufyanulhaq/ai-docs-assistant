from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.providers.base import ProviderError
from app.retrieval import Hit

DOCS = Path(__file__).resolve().parents[2] / "docs"


def make_settings(**overrides) -> Settings:
    values = dict(
        docs_dir=DOCS,
        provider="offline",
        anthropic_model="claude-opus-5-5",
        openai_model=None,
        company_name="Fernhill Cloud",
        top_k=4,
        min_score=2.0,
        min_coverage=0.34,
        max_history_messages=6,
        rate_limit_per_minute=1000,
        cors_origins=["http://localhost:3000"],
        admin_token=None,
    )
    values.update(overrides)
    return Settings(**values)


class StubProvider:
    name = "stub"
    model = "stub-model"

    def __init__(self, pieces=("Hello ", "world"), error: Exception | None = None):
        self.pieces = pieces
        self.error = error
        self.calls: list[dict] = []

    def stream(self, question: str, history: list, hits: list[Hit]) -> Iterator[str]:
        self.calls.append({"question": question, "history": history, "hits": hits})
        for piece in self.pieces:
            yield piece
        if self.error:
            raise self.error


def parse_sse(body: str) -> list[tuple[str, object]]:
    events = []
    for block in body.strip().split("\n\n"):
        lines = block.split("\n")
        name = lines[0].removeprefix("event: ")
        data = json.loads(lines[1].removeprefix("data: "))
        events.append((name, data))
    return events


@pytest.fixture
def settings() -> Settings:
    return make_settings()


@pytest.fixture
def client(settings) -> TestClient:
    return TestClient(create_app(settings))


@pytest.fixture
def stub_client(settings):
    stub = StubProvider()
    return TestClient(create_app(settings, provider=stub)), stub


__all__ = ["ProviderError", "StubProvider", "make_settings", "parse_sse"]
