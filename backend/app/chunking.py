from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

HEADING = re.compile(r"^(#{1,4})\s+(.*\S)\s*$")


@dataclass(frozen=True)
class Chunk:
    id: str
    source: str
    doc_title: str
    heading: str
    text: str


def _split_long(paragraph: str, max_chars: int) -> list[str]:
    if len(paragraph) <= max_chars:
        return [paragraph]
    sentences = re.split(r"(?<=[.!?])\s+", paragraph)
    pieces: list[str] = []
    current = ""
    for sentence in sentences:
        if current and len(current) + 1 + len(sentence) > max_chars:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    return pieces


def _pack(paragraphs: list[str], max_chars: int, overlap_chars: int) -> list[str]:
    pieces = [p for para in paragraphs for p in _split_long(para, max_chars)]
    chunks: list[str] = []
    current: list[str] = []
    size = 0
    for piece in pieces:
        added = len(piece) + (2 if current else 0)
        if current and size + added > max_chars:
            chunks.append("\n\n".join(current))
            tail = current[-1]
            current = [tail] if len(tail) <= overlap_chars else []
            size = len(tail) if current else 0
            added = len(piece) + (2 if current else 0)
        current.append(piece)
        size += added
    if current:
        chunks.append("\n\n".join(current))
    return chunks


def chunk_markdown(
    text: str,
    source: str,
    max_chars: int = 900,
    overlap_chars: int = 160,
) -> list[Chunk]:
    doc_title = Path(source).stem.replace("-", " ").title()
    stack: list[tuple[int, str]] = []
    sections: list[tuple[str, list[str]]] = []
    paragraph: list[str] = []
    paragraphs: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            paragraphs.append("\n".join(paragraph).strip())
            paragraph.clear()

    def close_section() -> None:
        flush_paragraph()
        body = [p for p in paragraphs if p]
        if body:
            path = " > ".join(title for _, title in stack) or doc_title
            sections.append((path, list(body)))
        paragraphs.clear()

    for line in text.splitlines():
        match = HEADING.match(line)
        if match:
            close_section()
            level, title = len(match.group(1)), match.group(2)
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            if level == 1:
                doc_title = title
            continue
        if not line.strip():
            flush_paragraph()
        else:
            paragraph.append(line.rstrip())
    close_section()

    chunks: list[Chunk] = []
    for heading, body in sections:
        for piece in _pack(body, max_chars, overlap_chars):
            chunks.append(
                Chunk(
                    id=f"{source}#{len(chunks)}",
                    source=source,
                    doc_title=doc_title,
                    heading=heading,
                    text=piece,
                )
            )
    return chunks


def load_documents(docs_dir: Path, max_chars: int = 900) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(docs_dir.glob("*")):
        if path.suffix.lower() not in {".md", ".txt"} or not path.is_file():
            continue
        chunks.extend(
            chunk_markdown(path.read_text(encoding="utf-8"), path.name, max_chars)
        )
    return chunks
