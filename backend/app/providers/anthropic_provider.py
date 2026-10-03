from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import anthropic

from ..prompts import build_messages, build_system
from ..retrieval import Hit
from .base import ProviderError

EFFORT_MODELS = (
    "claude-opus-5",
    "claude-sonnet-5",
    "claude-fable",
    "claude-opus-4-6",
    "claude-opus-4-7",
    "claude-opus-4-8",
    "claude-sonnet-4-6",
)


class AnthropicProvider:
    name = "anthropic"

    def __init__(
        self,
        model: str,
        company: str,
        max_history: int = 6,
        max_tokens: int = 2048,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.system = build_system(company)
        self.max_history = max_history
        self.max_tokens = max_tokens
        self.client = client or anthropic.Anthropic()

    def _request(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        request: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "system": self.system,
            "messages": messages,
        }
        if self.model.startswith(EFFORT_MODELS):
            request["output_config"] = {"effort": "low"}
        return request

    def stream(
        self,
        question: str,
        history: list[dict[str, str]],
        hits: list[Hit],
    ) -> Iterator[str]:
        messages = build_messages(question, history, hits, self.max_history)
        try:
            with self.client.messages.stream(**self._request(messages)) as stream:
                for text in stream.text_stream:
                    yield text
                final = stream.get_final_message()
        except anthropic.AuthenticationError as exc:
            raise ProviderError("The Anthropic API key was rejected.") from exc
        except anthropic.RateLimitError as exc:
            raise ProviderError("The model is rate limited right now. Try again shortly.") from exc
        except anthropic.APIConnectionError as exc:
            raise ProviderError("Could not reach the model API.") from exc
        except anthropic.APIStatusError as exc:
            raise ProviderError(f"The model API returned an error ({exc.status_code}).") from exc
        if final.stop_reason == "refusal":
            raise ProviderError("The model declined to answer this request.")
