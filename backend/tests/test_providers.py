from __future__ import annotations

from types import SimpleNamespace

import anthropic
import openai
import pytest

from app.chunking import load_documents
from app.prompts import build_messages, build_system, format_context
from app.providers import build_provider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import ProviderError
from app.providers.offline import OfflineProvider
from app.providers.openai_provider import OpenAIProvider
from app.retrieval import BM25Index

from .conftest import DOCS, make_settings

try:
    import httpx2 as http
except ImportError:  # pragma: no cover
    import httpx as http


def hits_for(question: str):
    return BM25Index(load_documents(DOCS)).search(question, 3)


def fake_request():
    return http.Request("POST", "https://api.example.test/v1/messages")


def fake_response(status: int):
    return http.Response(status, request=fake_request())


class FakeStream:
    def __init__(self, texts, stop_reason="end_turn"):
        self.texts = texts
        self.stop_reason = stop_reason

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    @property
    def text_stream(self):
        return iter(self.texts)

    def get_final_message(self):
        return SimpleNamespace(stop_reason=self.stop_reason)


class FakeAnthropic:
    def __init__(self, stream=None, error=None):
        self.calls = []
        self._stream = stream
        self._error = error
        self.messages = SimpleNamespace(stream=self._stream_call)

    def _stream_call(self, **kwargs):
        self.calls.append(kwargs)
        if self._error:
            raise self._error
        return self._stream


# ---- prompts ---------------------------------------------------------------


def test_context_blocks_are_numbered_and_carry_their_source():
    context = format_context(hits_for("How long is the refund window?"))
    assert context.startswith("<context>") and context.endswith("</context>")
    assert '<source id="1" file="04-refunds-and-cancellation.md"' in context


def test_system_prompt_enforces_grounding_and_names_the_company():
    system = build_system("Acme")
    assert "Acme" in system
    assert "only" in system.lower() and "Do not guess" in system
    assert "never fill gaps" in system.lower()


def test_history_is_trimmed_and_starts_with_a_user_turn():
    history = [
        {"role": "user", "content": "q1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "q2"},
        {"role": "assistant", "content": "a2"},
    ]
    messages = build_messages("q3", history, hits_for("refund window"), max_history=3)
    # last 3 are [a1, q2, a2]; the leading assistant turn is dropped so the chat starts with a user turn
    assert [m["content"] for m in messages[:2]] == ["q2", "a2"]
    assert len(messages) == 3
    assert messages[-1]["role"] == "user" and "Question: q3" in messages[-1]["content"]


def test_zero_history_sends_only_the_final_message():
    messages = build_messages("q", [{"role": "user", "content": "old"}], hits_for("refund"), 0)
    assert len(messages) == 1


# ---- anthropic -------------------------------------------------------------


def test_anthropic_provider_streams_text_and_builds_the_request():
    fake = FakeAnthropic(FakeStream(["Refunds ", "last 14 days [1]."]))
    provider = AnthropicProvider("claude-opus-5-5", "Fernhill Cloud", client=fake)
    out = list(provider.stream("How long is the refund window?", [], hits_for("refund window")))
    assert "".join(out) == "Refunds last 14 days [1]."
    call = fake.calls[0]
    assert call["model"] == "claude-opus-5-5"
    assert call["output_config"] == {"effort": "low"}
    assert "Fernhill Cloud" in call["system"]
    assert call["messages"][-1]["role"] == "user"
    assert "<context>" in call["messages"][-1]["content"]
    assert "thinking" not in call and "temperature" not in call


def test_anthropic_provider_omits_effort_for_models_that_reject_it():
    fake = FakeAnthropic(FakeStream(["ok"]))
    provider = AnthropicProvider("claude-haiku-4-5", "Fernhill Cloud", client=fake)
    list(provider.stream("q", [], hits_for("refund window")))
    assert "output_config" not in fake.calls[0]


def test_anthropic_refusal_becomes_a_clean_error():
    fake = FakeAnthropic(FakeStream(["..."], stop_reason="refusal"))
    provider = AnthropicProvider("claude-opus-5-5", "Fernhill Cloud", client=fake)
    with pytest.raises(ProviderError, match="declined"):
        list(provider.stream("q", [], hits_for("refund window")))


@pytest.mark.parametrize(
    ("error", "fragment"),
    [
        (anthropic.AuthenticationError("bad key", response=fake_response(401), body=None), "rejected"),
        (anthropic.RateLimitError("slow down", response=fake_response(429), body=None), "rate limited"),
        (anthropic.APIConnectionError(request=fake_request()), "reach"),
        (anthropic.InternalServerError("boom", response=fake_response(500), body=None), "500"),
    ],
)
def test_anthropic_api_errors_are_translated(error, fragment):
    provider = AnthropicProvider("claude-opus-5-5", "Fernhill Cloud", client=FakeAnthropic(error=error))
    with pytest.raises(ProviderError, match=fragment):
        list(provider.stream("q", [], hits_for("refund window")))


# ---- openai ----------------------------------------------------------------


class FakeOpenAI:
    def __init__(self, chunks=None, error=None):
        self.calls = []
        self._chunks = chunks or []
        self._error = error
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self._error:
            raise self._error
        return iter(self._chunks)


def delta(text):
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text))])


def test_openai_provider_streams_deltas_and_skips_empty_ones():
    fake = FakeOpenAI([delta("Hello "), delta(None), SimpleNamespace(choices=[]), delta("there")])
    provider = OpenAIProvider("some-model", "Fernhill Cloud", client=fake)
    assert "".join(provider.stream("q", [], hits_for("refund window"))) == "Hello there"
    call = fake.calls[0]
    assert call["stream"] is True and call["model"] == "some-model"
    assert call["messages"][0]["role"] == "system"


def test_openai_errors_are_translated():
    error = openai.APIConnectionError(request=fake_request())
    provider = OpenAIProvider("some-model", "Fernhill Cloud", client=FakeOpenAI(error=error))
    with pytest.raises(ProviderError, match="reach"):
        list(provider.stream("q", [], hits_for("refund window")))


# ---- offline + factory -----------------------------------------------------


def test_offline_provider_quotes_the_docs_with_citations():
    hits = hits_for("How many times are failed webhooks retried?")
    text = "".join(OfflineProvider().stream("How many times are failed webhooks retried?", [], hits))
    assert text.startswith("Offline mode")
    assert "8 times" in text and "[1]" in text


def test_offline_provider_drops_passages_that_only_match_by_accident():
    question = "How long do I have to ask for a refund?"
    text = "".join(OfflineProvider().stream(question, [], hits_for(question)))
    assert "14 days" in text
    assert "Large date ranges" not in text


def test_offline_provider_is_deterministic():
    hits = hits_for("What is the rate limit on the Business plan?")
    q = "What is the rate limit on the Business plan?"
    assert list(OfflineProvider().stream(q, [], hits)) == list(OfflineProvider().stream(q, [], hits))


def test_factory_picks_the_configured_provider():
    assert build_provider(make_settings(provider="offline")).name == "offline"
    with pytest.raises(RuntimeError, match="OPENAI_MODEL"):
        build_provider(make_settings(provider="openai", openai_model=None))
    with pytest.raises(RuntimeError, match="Unknown"):
        build_provider(make_settings(provider="nope"))
