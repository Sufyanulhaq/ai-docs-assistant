from __future__ import annotations

import math
import re
from collections.abc import Iterator

from ..retrieval import Hit, tokenize

NOTICE = (
    "Offline mode: no LLM API key is configured, so these are the most relevant "
    "passages from the documentation rather than a written answer.\n\n"
)


def _sentences(text: str) -> list[str]:
    lines = [ln.strip("-• \t") for ln in text.splitlines() if ln.strip()]
    sentences: list[str] = []
    for line in lines:
        sentences.extend(s.strip() for s in re.split(r"(?<=[.!?])\s+", line) if s.strip())
    return sentences


class OfflineProvider:
    name = "offline"
    model = None

    def __init__(self, max_passages: int = 3) -> None:
        self.max_passages = max_passages

    def stream(
        self,
        question: str,
        history: list[dict[str, str]],
        hits: list[Hit],
    ) -> Iterator[str]:
        query_terms = set(tokenize(question))
        candidates: list[tuple[int, float, int, str]] = []
        for number, hit in enumerate(hits, start=1):
            for sentence in _sentences(hit.chunk.text):
                overlap = len(query_terms & set(tokenize(sentence)))
                if overlap:
                    candidates.append((overlap, hit.score, number, sentence))
        if candidates:
            floor = math.ceil(max(c[0] for c in candidates) * 0.6)
            candidates = [c for c in candidates if c[0] >= floor]
        candidates.sort(key=lambda c: (c[0], c[1]), reverse=True)

        chosen: list[tuple[int, str]] = []
        seen: set[str] = set()
        for _, _, number, sentence in candidates:
            if sentence not in seen:
                seen.add(sentence)
                chosen.append((number, sentence))
            if len(chosen) == self.max_passages:
                break

        body = "\n".join(f"- {sentence} [{number}]" for number, sentence in chosen)
        text = NOTICE + (body or "No passage matched closely enough.")
        for word in re.findall(r"\S+\s*", text):
            yield word
