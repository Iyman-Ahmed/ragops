from fastapi.testclient import TestClient

from app import rag
from app.main import app

client = TestClient(app)


def test_health(mem_store):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ingest_then_query(mem_store, monkeypatch):
    monkeypatch.setattr(rag, "answer", lambda q, k=None: {
        "answer": "42", "contexts": ["c"], "num_contexts": 1, "latency_ms": 1.0})
    ingest = client.post("/ingest", json={"documents": ["hello world"], "sources": ["a.md"]})
    assert ingest.status_code == 200 and ingest.json()["chunks_indexed"] >= 1
    r = client.post("/query", json={"question": "what?"})
    assert r.status_code == 200
    body = r.json()
    assert body["answer"] == "42" and "retrieved" not in body   # dataclasses not leaked


def test_metrics_exposed(mem_store):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "ragops_requests_total" in r.text
