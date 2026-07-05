"""Shared eval harness — used by evaluate.py, retrieval_gate.py and calibrate.py.

Splits cleanly into a DETERMINISTIC retrieval pass (no LLM, safe to block every PR) and a
generation pass (needs an LLM endpoint, reported but only blocks on a catastrophe floor).
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field

from app import llm
from app.chunking import find_span
from app.config import settings
from app.prompts import SYSTEM_PROMPT, build_user_prompt
from app.store import Store
from eval import metrics

HERE = pathlib.Path(__file__).parent


@dataclass
class Example:
    id: str
    type: str
    question: str
    source: str | None
    gold_span: tuple[int, int] | None
    answer_aliases: list[str]

    @property
    def answerable(self) -> bool:
        return self.gold_span is not None


@dataclass
class RunConfig:
    """A regression is just a non-default RunConfig — that is the whole point of the gate."""
    chunk_chars: int = field(default_factory=lambda: settings.chunk_chars)
    top_k: int = field(default_factory=lambda: settings.top_k)
    embed_model: str = field(default_factory=lambda: settings.embed_model)
    corpus_dir: str = field(default_factory=lambda: settings.corpus_dir)
    max_docs: int | None = None      # truncate the corpus (simulates a lost-documents regression)


def load_corpus(corpus_dir: str) -> dict[str, str]:
    root = pathlib.Path(corpus_dir)
    if not root.is_absolute():
        root = (HERE.parent / corpus_dir)
    return {p.name: p.read_text() for p in sorted(root.glob("*.md"))}


def load_dataset(corpus: dict[str, str]) -> list[Example]:
    rows = [json.loads(line) for line in (HERE / "dataset.jsonl").read_text().splitlines()
            if line.strip()]
    examples = []
    for r in rows:
        span = None
        if r["source"]:
            doc = corpus.get(r["source"])
            if doc is None:
                raise ValueError(f"{r['id']}: source {r['source']} not in corpus")
            span = find_span(doc, r["gold_quote"])
            if span is None:
                raise ValueError(
                    f"{r['id']}: gold_quote not found in {r['source']} — fix the label")
        examples.append(Example(r["id"], r["type"], r["question"], r["source"],
                                span, r["answer_aliases"]))
    return examples


def build_store(cfg: RunConfig) -> Store:
    """Fresh in-memory store ingested with the corpus under `cfg`. Isolated per run (unique
    collection name) so a regression config never collides with another run's embeddings."""
    import uuid

    corpus = load_corpus(cfg.corpus_dir)
    store = Store(embed_model=cfg.embed_model, persistent=False,
                  collection=f"eval-{uuid.uuid4().hex[:12]}")
    items = list(corpus.items())
    if cfg.max_docs is not None:
        items = items[:cfg.max_docs]
    for name, text in items:
        store.ingest_document(text, name, size=cfg.chunk_chars)
    return store


def run_retrieval(cfg: RunConfig) -> dict:
    """Deterministic. recall@k + MRR over gold spans. No LLM."""
    corpus = load_corpus(cfg.corpus_dir)
    dataset = load_dataset(corpus)
    store = build_store(cfg)
    answerable = [e for e in dataset if e.answerable]
    hits_k = hits_1 = 0
    rr_sum = 0.0
    for ex in answerable:
        retrieved = store.query(ex.question, cfg.top_k)
        rr = metrics.reciprocal_rank(ex.source, ex.gold_span, retrieved)
        rr_sum += rr
        hits_1 += int(rr == 1.0)                       # gold retrieved at rank 1
        hits_k += metrics.recall_at_k(ex.source, ex.gold_span, retrieved)
    n = len(answerable)
    return {
        # recall@1 is the primary gated metric: binomial (Wilson-gateable) and sensitive to
        # rank quality, so it moves when embeddings/chunking degrade even if recall@k saturates.
        "recall_at_1": round(hits_1 / n, 4),
        "recall_at_1_wilson_lb": round(metrics.wilson_lower_bound(hits_1, n), 4),
        "recall_at_k": round(hits_k / n, 4),
        "mrr": round(rr_sum / n, 4),
        "recall_1_hits": hits_1,
        "n_answerable": n,
        "top_k": cfg.top_k,
    }


def run_generation(cfg: RunConfig) -> dict:
    """Needs an LLM endpoint. answer accuracy on answerable, refusal accuracy on
    unanswerable, p95 latency. Stochastic — reported always, blocks only at a low floor."""
    import time

    corpus = load_corpus(cfg.corpus_dir)
    dataset = load_dataset(corpus)
    store = build_store(cfg)
    answerable = [e for e in dataset if e.answerable]
    unanswerable = [e for e in dataset if not e.answerable]

    correct = 0
    latencies = []
    for ex in answerable:
        contexts = [r.text for r in store.query(ex.question, cfg.top_k)]
        t0 = time.perf_counter()
        ans = llm.complete(SYSTEM_PROMPT, build_user_prompt(ex.question, contexts))
        latencies.append((time.perf_counter() - t0) * 1000)
        if metrics.answer_correct(ans, ex.answer_aliases):
            correct += 1

    refused = 0
    for ex in unanswerable:
        contexts = [r.text for r in store.query(ex.question, cfg.top_k)]
        ans = llm.complete(SYSTEM_PROMPT, build_user_prompt(ex.question, contexts))
        if metrics.is_refusal(ans):
            refused += 1

    na, nu = len(answerable), len(unanswerable)
    return {
        "answer_accuracy": round(correct / na, 4) if na else 0.0,
        "answer_wilson_lb": round(metrics.wilson_lower_bound(correct, na), 4),
        "refusal_accuracy": round(refused / nu, 4) if nu else 0.0,
        "p95_latency_ms": round(metrics.percentile(latencies, 95), 1),
        "answer_correct": correct,
        "n_answerable": na,
        "n_unanswerable": nu,
    }
