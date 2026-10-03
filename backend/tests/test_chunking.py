from __future__ import annotations

from app.chunking import chunk_markdown, load_documents

from .conftest import DOCS

SAMPLE = """# Billing

Intro paragraph about billing.

## Refunds

You can ask for a refund within 14 days.

### Annual plans

Annual plans are refundable in the first 14 days only.

- item one
- item two
"""


def test_headings_become_a_path():
    chunks = chunk_markdown(SAMPLE, "billing.md")
    headings = [c.heading for c in chunks]
    assert "Billing" in headings
    assert "Billing > Refunds" in headings
    assert "Billing > Refunds > Annual plans" in headings


def test_title_comes_from_first_heading():
    assert chunk_markdown(SAMPLE, "billing.md")[0].doc_title == "Billing"


def test_ids_are_unique_and_stable():
    first = chunk_markdown(SAMPLE, "billing.md")
    second = chunk_markdown(SAMPLE, "billing.md")
    assert [c.id for c in first] == [c.id for c in second]
    assert len({c.id for c in first}) == len(first)


def test_lists_stay_with_their_paragraph():
    chunk = next(c for c in chunk_markdown(SAMPLE, "billing.md") if "item one" in c.text)
    assert "item two" in chunk.text


def test_long_sections_are_split_under_the_limit():
    body = "\n\n".join(f"Paragraph {i}. " + "word " * 60 for i in range(12))
    chunks = chunk_markdown(f"# Long\n\n{body}", "long.md", max_chars=700, overlap_chars=0)
    assert len(chunks) > 1
    assert all(len(c.text) <= 700 for c in chunks)


def test_a_single_huge_paragraph_is_split_on_sentences():
    paragraph = " ".join(f"Sentence number {i} is here." for i in range(80))
    chunks = chunk_markdown(f"# Big\n\n{paragraph}", "big.md", max_chars=400)
    assert len(chunks) > 1
    assert all(len(c.text) <= 400 for c in chunks)


def test_no_empty_chunks_and_no_text_is_lost():
    chunks = chunk_markdown(SAMPLE, "billing.md")
    assert all(c.text.strip() for c in chunks)
    joined = " ".join(c.text for c in chunks)
    assert "14 days" in joined and "item two" in joined


def test_sample_docs_load():
    chunks = load_documents(DOCS)
    assert len({c.source for c in chunks}) == 9
    assert all(len(c.text) <= 900 for c in chunks)
