"""Locks the centerpiece: the deterministic retrieval gate passes on a clean pipeline and
fires on injected regressions.

These tests pin an explicit config so they exercise the gate *mechanism* deterministically,
independent of the live TOP_K/EMBED_MODEL defaults. That separation is deliberate: the unit
tests verify the harness on known-good inputs, while `eval/retrieval_gate.py` runs against
the live config — so a config regression (e.g. top_k 4->1) turns the gate RED without also
tripping the test suite. That's the whole point: tests stay green, the quality gate blocks."""
from eval.harness import RunConfig, run_retrieval
from eval.retrieval_gate import THRESHOLDS

GOOD = dict(top_k=4, embed_model="all-MiniLM-L6-v2", chunk_chars=700)


def _fires(metrics):
    return [k for k, thr in THRESHOLDS.items() if metrics[k] < thr]


def test_gate_passes_on_clean_pipeline():
    assert _fires(run_retrieval(RunConfig(**GOOD))) == []


def test_gate_fires_on_embedding_swap():
    metrics = run_retrieval(RunConfig(**{**GOOD, "embed_model": "hash-64"}))
    assert _fires(metrics)                       # a real regression must not pass silently


def test_gate_fires_on_corpus_truncation():
    metrics = run_retrieval(RunConfig(**{**GOOD, "max_docs": 4}))
    assert _fires(metrics)
