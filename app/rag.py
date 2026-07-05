"""RAG pipeline: chunk -> embed -> retrieve -> grounded generate.

The retrieval core stays small and swappable on purpose; the value of this repo is the
production wrapper around it (eval gate, CI, tracking, monitoring, IaC). Retrieval now
returns span metadata so the eval gate can score recall@k against gold spans with no LLM.
"""
import time

from app import llm
from app.prompts import SYSTEM_PROMPT, build_user_prompt
from app.store import Retrieved, Store

_store: Store | None = None


def get_store() -> Store:
    """Lazily create the process-wide persistent store."""
    global _store
    if _store is None:
        _store = Store()
    return _store


def set_store(store: Store) -> None:
    """Dependency injection for tests and the eval harness."""
    global _store
    _store = store


def ingest(documents: list[str], sources: list[str] | None = None) -> int:
    return get_store().ingest(documents, sources)


def retrieve(question: str, k: int | None = None) -> list[Retrieved]:
    return get_store().query(question, k)


def answer(question: str, k: int | None = None) -> dict:
    """Return {answer, contexts, retrieved, num_contexts, latency_ms}."""
    t0 = time.perf_counter()
    retrieved = retrieve(question, k)
    contexts = [r.text for r in retrieved]
    text = llm.complete(SYSTEM_PROMPT, build_user_prompt(question, contexts))
    return {
        "answer": text.strip(),
        "contexts": contexts,
        "retrieved": retrieved,
        "num_contexts": len(contexts),
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
    }
