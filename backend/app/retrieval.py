from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from .chunking import Chunk

TOKEN = re.compile(r"[a-z0-9_]+")

STOPWORDS = frozenset(
    """a about after all also am an and any are as at be been before but by can could
    did do does doing for from get got had has have how i if in into is it its just
    me my of on or our out so than that the their them then there these they this to
    up us was we were what when where which who why will with would you your
    tell write show give please help want need like know say make find name""".split()
)


_SUFFIXES = (
    ("ations", ""),
    ("ation", ""),
    ("ies", "y"),
    ("ied", "y"),
    ("sses", "ss"),
    ("xes", "x"),
    ("ches", "ch"),
    ("shes", "sh"),
    ("ing", ""),
    ("edly", ""),
    ("ed", ""),
    ("ly", ""),
    ("s", ""),
)


def stem(word: str) -> str:
    if len(word) <= 3 or word.isdigit():
        return word
    for suffix, replacement in _SUFFIXES:
        if suffix == "s" and word.endswith("ss"):
            continue
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)] + replacement
    return word


def tokenize(text: str) -> list[str]:
    return [
        stem(t)
        for t in TOKEN.findall(text.lower())
        if t not in STOPWORDS and len(t) > 1
    ]


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float
    coverage: float


class BM25Index:
    def __init__(self, chunks: list[Chunk], k1: float = 1.5, b: float = 0.75) -> None:
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self._term_freqs: list[Counter[str]] = []
        self._lengths: list[int] = []
        doc_freq: Counter[str] = Counter()
        for chunk in chunks:
            tokens = tokenize(chunk.text) + tokenize(chunk.heading) * 2 + tokenize(chunk.doc_title)
            counts = Counter(tokens)
            self._term_freqs.append(counts)
            self._lengths.append(len(tokens))
            doc_freq.update(counts.keys())
        n = len(chunks)
        self._avg_len = (sum(self._lengths) / n) if n else 0.0
        self._idf = {
            term: math.log(1 + (n - df + 0.5) / (df + 0.5)) for term, df in doc_freq.items()
        }

    def knows_any(self, text: str) -> bool:
        return any(term in self._idf for term in tokenize(text))

    def search(self, query: str, k: int = 4) -> list[Hit]:
        terms = list(dict.fromkeys(tokenize(query)))
        known = [t for t in terms if t in self._idf]
        if not known:
            return []
        scored: list[tuple[float, float, int]] = []
        for index, counts in enumerate(self._term_freqs):
            length = self._lengths[index] or 1
            score = 0.0
            matched = 0
            for term in known:
                tf = counts.get(term, 0)
                if not tf:
                    continue
                matched += 1
                norm = tf * (self.k1 + 1) / (
                    tf + self.k1 * (1 - self.b + self.b * length / self._avg_len)
                )
                score += self._idf[term] * norm
            if score > 0:
                scored.append((score, matched / len(terms), index))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [Hit(self.chunks[i], round(s, 3), round(c, 3)) for s, c, i in scored[:k]]
