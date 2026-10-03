from __future__ import annotations

import pytest

from app.chunking import load_documents
from app.retrieval import BM25Index, stem, tokenize

from .conftest import DOCS

EVAL_SET = [
    ("How long do I have to ask for a refund?", "04-refunds"),
    ("What does the Pro plan cost per seat if I pay annually?", "02-plans"),
    ("Can I cancel my annual plan and get money back?", "04-refunds"),
    ("How do I rotate an API key without downtime?", "05-api"),
    ("What is the rate limit on the Business plan?", "05-api"),
    ("How many times are failed webhooks retried?", "06-webhooks"),
    ("How do I verify the webhook signature?", "06-webhooks"),
    ("Does Fernhill support SAML single sign on?", "07-security"),
    ("Which plan includes audit logs?", "07-security"),
    ("Where is my data stored, can I pick the region?", "07-security"),
    ("How long does workspace deletion take?", "08-data"),
    ("How do I export my run history as CSV?", "08-data"),
    ("Why do I get a 403 error from the API?", "09-trouble"),
    ("My pipeline is stuck in queued, why?", "09-trouble"),
    ("What happens if my card payment fails?", "03-billing"),
    ("Can I get a PDF invoice with my VAT number?", "03-billing"),
    ("What roles are there for team members?", "01-getting"),
    ("How many concurrent runs on Free?", "02-plans"),
]

JUNK = [
    "What is the weather in Paris today?",
    "Write me a poem about cats",
    "tell me a joke",
    "How do I bake sourdough bread?",
    "hello",
    "Who won the football world cup?",
]


@pytest.fixture(scope="module")
def index() -> BM25Index:
    return BM25Index(load_documents(DOCS))


def rank_of(index: BM25Index, question: str, prefix: str) -> int | None:
    sources = [h.chunk.source for h in index.search(question, 4)]
    return next((i for i, s in enumerate(sources) if s.startswith(prefix)), None)


def test_top3_accuracy_is_perfect_on_the_eval_set(index):
    ranks = [rank_of(index, q, want) for q, want in EVAL_SET]
    misses = [q for (q, _), r in zip(EVAL_SET, ranks) if r is None or r > 2]
    assert not misses, f"not in top 3: {misses}"


def test_top1_accuracy_is_high_on_the_eval_set(index):
    top1 = sum(rank_of(index, q, want) == 0 for q, want in EVAL_SET)
    assert top1 / len(EVAL_SET) >= 0.9


@pytest.mark.parametrize("question", JUNK)
def test_obvious_junk_finds_nothing(index, question):
    assert index.search(question, 4) == []


def test_specific_number_questions_find_the_right_fact(index):
    top = index.search("How long is the refund window", 1)[0].chunk
    assert "14 day" in top.text


def test_scores_are_sorted_descending(index):
    scores = [h.score for h in index.search("api key scopes and rate limits", 4)]
    assert scores == sorted(scores, reverse=True)


def test_empty_index_returns_nothing():
    assert BM25Index([]).search("anything") == []


def test_tokenizer_drops_stopwords_and_stems():
    assert tokenize("How are the webhooks retried?") == ["webhook", "retry"]
    assert stem("invoices") == stem("invoice") == "invoice"
    assert stem("retried") == stem("retries") == stem("retry") == "retry"
    assert stem("access") == "access"
    assert tokenize("the and of") == []
