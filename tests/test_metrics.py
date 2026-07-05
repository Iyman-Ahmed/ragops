from dataclasses import dataclass

from eval import metrics


@dataclass
class R:
    source: str
    start: int
    end: int


def test_number_word_canonicalization():
    assert metrics.answer_correct("It fails three times", ["3"])
    assert metrics.answer_correct("It fails 3 times", ["3|three"])


def test_numeric_alias_respects_word_boundary():
    # "99" must not match inside "499" — the classic keyword-metric embarrassment.
    assert not metrics.answer_correct("The Enterprise plan costs 499 dollars", ["99"])
    assert metrics.answer_correct("The Team plan costs 99 dollars", ["99"])


def test_all_alias_groups_required():
    assert metrics.answer_correct("three failures in 90 seconds", ["3|three", "90"])
    assert not metrics.answer_correct("three failures", ["3|three", "90"])


def test_refusal_detection():
    assert metrics.is_refusal("I don't know based on the provided context.")
    assert not metrics.is_refusal("The answer is AES-256.")


def test_recall_requires_same_document():
    # A chunk from another file that merely shares character offsets is NOT a hit.
    gold_source, gold_span = "billing.md", (0, 40)
    wrong_doc = [R("cli.md", 0, 40)]
    right_doc = [R("billing.md", 10, 50)]
    assert metrics.recall_at_k(gold_source, gold_span, wrong_doc) == 0
    assert metrics.recall_at_k(gold_source, gold_span, right_doc) == 1


def test_reciprocal_rank_uses_position():
    gold_source, gold_span = "d.md", (0, 10)
    retrieved = [R("other.md", 0, 10), R("d.md", 0, 10)]
    assert metrics.reciprocal_rank(gold_source, gold_span, retrieved) == 0.5


def test_wilson_lower_bound_is_below_point_estimate():
    lb = metrics.wilson_lower_bound(32, 38)
    assert 0.0 < lb < 32 / 38
