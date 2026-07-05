"""Sentence-aware chunking with character offsets.

Two properties the eval gate depends on:

1. Deterministic — same input always yields the same chunks and the same ids, so a
   PersistentClient re-ingest is idempotent (upsert, no duplicate chunks).
2. Offset-carrying — every chunk knows its [start, end) span in the *normalized* source
   document. Gold answers in the eval set are labeled as spans, so retrieval quality is
   scored by span overlap (recall@k / MRR) with no LLM in the loop.

Fixed-character slicing (the original scaffold) split words and facts mid-token
("...responses wit|hin 48 hours"), which silently hurt retrieval. We pack whole
sentences instead.
"""
import hashlib
import re
from dataclasses import dataclass

_WS = re.compile(r"\s+")
# Split after ., !, ? or a newline, keeping the delimiter with the sentence.
_SENT = re.compile(r"[^.!?\n]*[.!?\n]|[^.!?\n]+$")


@dataclass(frozen=True)
class Chunk:
    text: str
    start: int          # inclusive offset into the normalized doc
    end: int            # exclusive
    source: str         # document id (e.g. filename)

    def id(self) -> str:
        """Content+position hash → stable id, so re-ingesting upserts in place."""
        h = hashlib.sha1(f"{self.source}:{self.start}:{self.end}:{self.text}".encode())
        return h.hexdigest()[:16]

    def overlaps(self, span: tuple[int, int]) -> bool:
        return self.start < span[1] and span[0] < self.end


def normalize(text: str) -> str:
    """Collapse whitespace. Chunk offsets and gold spans are computed on THIS form,
    so producers and scorers agree on a single coordinate system."""
    return _WS.sub(" ", text).strip()


def _sentences(norm: str) -> list[tuple[str, int, int]]:
    out = []
    for m in _SENT.finditer(norm):
        s = m.group().strip()
        if s:
            out.append((s, m.start(), m.end()))
    return out


def chunk_document(text: str, source: str, size: int,
                   overlap_sentences: int = 1) -> list[Chunk]:
    """Pack sentences greedily up to `size` chars; carry `overlap_sentences` across
    boundaries so a fact split across a boundary is still retrievable from one chunk."""
    norm = normalize(text)
    sents = _sentences(norm)
    if not sents:
        return []

    chunks: list[Chunk] = []
    cur: list[tuple[str, int, int]] = []
    cur_len = 0
    for sent in sents:
        s_len = len(sent[0]) + 1
        if cur and cur_len + s_len > size:
            start, end = cur[0][1], cur[-1][2]
            chunks.append(Chunk(norm[start:end].strip(), start, end, source))
            cur = cur[-overlap_sentences:] if overlap_sentences else []
            cur_len = sum(len(s[0]) + 1 for s in cur)
        cur.append(sent)
        cur_len += s_len
    if cur:
        start, end = cur[0][1], cur[-1][2]
        chunks.append(Chunk(norm[start:end].strip(), start, end, source))
    return chunks


def find_span(text: str, quote: str) -> tuple[int, int] | None:
    """Locate a gold quote inside a document, in normalized coordinates.
    Used at eval-load time to turn a human-authored quote into a [start, end) span."""
    norm = normalize(text)
    q = normalize(quote)
    i = norm.find(q)
    return (i, i + len(q)) if i >= 0 else None
