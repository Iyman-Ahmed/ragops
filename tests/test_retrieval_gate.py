"""Locks the centerpiece: the deterministic retrieval gate passes on a clean pipeline and
fires on an injected embedding regression. This is the eval-gate promise as a unit test."""
from eval.harness import RunConfig, run_retrieval
from eval.retrieval_gate import THRESHOLDS


def _fires(metrics):
    return [k for k, thr in THRESHOLDS.items() if metrics[k] < thr]


def test_gate_passes_on_clean_pipeline():
    assert _fires(run_retrieval(RunConfig())) == []


def test_gate_fires_on_embedding_swap():
    metrics = run_retrieval(RunConfig(embed_model="hash-64"))
    assert _fires(metrics)                       # a real regression must not pass silently


def test_gate_fires_on_corpus_truncation():
    metrics = run_retrieval(RunConfig(max_docs=4))
    assert _fires(metrics)
