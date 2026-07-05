"""Shared fixtures. Tests are fully offline: no LLM endpoint, no persistent store."""
import uuid

import pytest

from app import llm, rag
from app.store import Store


@pytest.fixture
def mem_store():
    """An isolated in-memory store (unique collection so embedding configs never clash)."""
    store = Store(persistent=False, collection=f"test-{uuid.uuid4().hex[:12]}")
    rag.set_store(store)
    yield store
    rag.set_store(None)


@pytest.fixture
def fake_llm(monkeypatch):
    """Deterministic LLM stub — records prompts, returns a canned answer."""
    calls = {}

    def _complete(system, user, **kw):
        calls["system"] = system
        calls["user"] = user
        return calls.get("reply", "stubbed answer")

    monkeypatch.setattr(llm, "complete", _complete)
    return calls
