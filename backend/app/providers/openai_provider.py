from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import openai

from ..prompts import build_messages, build_system
from ..retrieval import Hit
from .base import ProviderError


class OpenAIProvider:
    name = "openai"

    def __init__(
        self,
        model: str,
        company: str,
        max_history: int = 6,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.system = build_system(company)
        self.max_history = max_history
        self.client = client or openai.OpenAI()

    def stream(
        self,
        question: str,
        history: list[dict[str, str]],
        hits: list[Hit],
    ) -> Iterator[str]:
        messages = [
            {"role": "system", "content": self.system},
            *build_messages(question, history, hits, self.max_history),
        ]
        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, stream=True
            )
            for chunk in response:
                if not chunk.choices:
                    continue
                text = chunk.choices[0].delta.content
                if text:
                    yield text
        except openai.AuthenticationError as exc:
            raise ProviderError("The OpenAI API key was rejected.") from exc
        except openai.RateLimitError as exc:
            raise ProviderError("The model is rate limited right now. Try again shortly.") from exc
        except openai.APIConnectionError as exc:
            raise ProviderError("Could not reach the model API.") from exc
        except openai.APIStatusError as exc:
            raise ProviderError(f"The model API returned an error ({exc.status_code}).") from exc
