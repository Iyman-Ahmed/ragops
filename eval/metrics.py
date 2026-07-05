"""Eval metrics — deterministic and defensible.

Design decisions (each is here because the naive version embarrasses you in an interview):

* Answer matching canonicalizes number words ("three" -> "3") and matches aliases on WORD
  boundaries, so "99" no longer matches "499" and a model that says "3" is not marked
  wrong for a gold answer of "three". Each alias may be an alternation ("3|three").
* Retrieval is scored by SPAN OVERLAP against a gold quote's location, not by "is a
  keyword somewhere in the concatenated context" (which saturates at 1.0 on a small
  corpus and can never fail). recall@k and MRR are computed with no LLM in the loop.
* Thresholds are compared against the WILSON lower bound of the observed rate, so the gate
  fails only on a statistically distinguishable regression, not on sampling noise.
"""
from __future__ import annotations

import math
import re

_NUMBER_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
    "six": "6", "seven": "7", "eight": "8", "nine": "9", "ten": "10",
    "eleven": "11", "twelve": "12",
}


def canonicalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\$\s*", "", text)                      # "$99" -> "99"
    text = re.sub(r"[,]", "", text)
    for word, digit in _NUMBER_WORDS.items():
        text = re.sub(rf"\b{word}\b", digit, text)
    return re.sub(r"\s+", " ", text).strip()


def _alias_matches(answer_canon: str, alias: str) -> bool:
    """An alias is a `|`-separated set of acceptable options; match any, on a word
    boundary so short numeric answers do not match inside larger tokens."""
    for opt in canonicalize(alias).split("|"):
        opt = opt.strip()
        if not opt:
            continue
        # Boundaries: not glued to a word char on either side, and not the head of a
        # decimal (so "99" rejects "99.9"/"499") — but a trailing sentence period is a
        # delimiter, so "AES-256." and "99." still match.
        if re.search(rf"(?<![\w.]){re.escape(opt)}(?!\w)(?!\.\d)", answer_canon):
            return True
    return False


def answer_correct(answer: str, aliases: list[str]) -> bool:
    """Correct iff EVERY required alias group is satisfied."""
    if not aliases:
        return False
    canon = canonicalize(answer)
    return all(_alias_matches(canon, a) for a in aliases)


REFUSAL_MARKERS = ["i don't know", "i do not know", "not contained in the context",
                   "not in the provided context", "cannot answer", "unable to answer"]


def is_refusal(answer: str) -> bool:
    canon = canonicalize(answer)
    return any(m in canon for m in REFUSAL_MARKERS)


def recall_at_k(gold_source: str, gold_span: tuple[int, int], retrieved: list) -> int:
    """1 if any retrieved chunk is from the gold document AND overlaps the gold span."""
    return int(any(_overlaps(r, gold_source, gold_span) for r in retrieved))


def reciprocal_rank(gold_source: str, gold_span: tuple[int, int], retrieved: list) -> float:
    for i, r in enumerate(retrieved, start=1):
        if _overlaps(r, gold_source, gold_span):
            return 1.0 / i
    return 0.0


def _overlaps(retrieved, gold_source: str, span: tuple[int, int]) -> bool:
    # Offsets are per-document, so a hit requires the SAME document, not just numerically
    # overlapping character ranges (which would credit a chunk from another file).
    return (retrieved.source == gold_source
            and retrieved.start < span[1] and span[0] < retrieved.end)


def wilson_lower_bound(successes: int, n: int, z: float = 1.96) -> float:
    """Lower bound of the Wilson score interval — the honest number to gate on.
    Answers "how do I know 0.78 vs 0.80 isn't noise?" with one whiteboard-derivable formula."""
    if n == 0:
        return 0.0
    p = successes / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (centre - margin) / denom)


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    idx = min(len(values) - 1, int(round((p / 100) * (len(values) - 1))))
    return values[idx]
