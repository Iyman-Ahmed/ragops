"""L2 — behavioral contracts on the RAG core, with the LLM stubbed (deterministic)."""
from app import rag


def test_answer_grounds_the_llm_in_retrieved_context(mem_store, fake_llm):
    mem_store.ingest_document("The Team plan costs 99 dollars per month.", "billing.md")
    fake_llm["reply"] = "The Team plan costs 99 dollars."
    out = rag.answer("how much is the team plan?")
    # the model was handed the retrieved context, not just the bare question
    assert "99 dollars per month" in fake_llm["user"]
    assert out["num_contexts"] >= 1
    assert out["latency_ms"] >= 0


def test_answer_on_empty_store_passes_no_context_marker(mem_store, fake_llm):
    fake_llm["reply"] = "I don't know based on the provided context."
    out = rag.answer("unknown question?")
    assert out["num_contexts"] == 0
    assert "(no context found)" in fake_llm["user"]


def test_retrieve_returns_ranked_sources(mem_store, fake_llm):
    mem_store.ingest_document("Data is encrypted at rest with AES-256.", "storage.md")
    mem_store.ingest_document("The Starter plan costs 29 dollars.", "billing.md")
    hits = rag.retrieve("how is data encrypted?", k=2)
    assert hits[0].source == "storage.md"
