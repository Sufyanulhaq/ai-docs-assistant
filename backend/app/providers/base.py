from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from ..retrieval import Hit


class ProviderError(Exception):
    """An error whose message is safe to show to the end user."""


class Provider(Protocol):
    name: str
    model: str | None

    def stream(
        self,
        question: str,
        history: list[dict[str, str]],
        hits: list[Hit],
    ) -> Iterator[str]: ...
