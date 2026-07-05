"""RAGOps API — a production-shaped RAG service.

Endpoints:
  GET  /health   liveness/readiness probe (used by ECS + k8s)
  POST /ingest   index documents
  POST /query    ask a question (grounded answer + contexts + latency)
  GET  /metrics  Prometheus metrics
"""
import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel

from app import rag
from app.config import settings
from app.observability import RETRIEVED, Timer, get_logger

log = get_logger()


def _load_corpus() -> None:
    """Warm the persistent store from CORPUS_DIR on first boot. Idempotent (deterministic
    chunk ids upsert), so restarts don't duplicate chunks and the index is never empty."""
    store = rag.get_store()
    corpus = pathlib.Path(settings.corpus_dir)
    if store.count() > 0 or not corpus.is_dir():
        log.info("corpus_load_skip", extra={"extra": {"chunks": store.count()}})
        return
    docs, sources = [], []
    for p in sorted(corpus.glob("*.md")):
        docs.append(p.read_text())
        sources.append(p.name)
    if docs:
        n = store.ingest(docs, sources)
        log.info("corpus_loaded", extra={"extra": {"docs": len(docs), "chunks": n}})


@asynccontextmanager
async def lifespan(app: FastAPI):
    _load_corpus()
    yield


app = FastAPI(title="RAGOps", version="0.2.0", lifespan=lifespan,
              description="Eval-gated RAG service (eval + CI/CD + IaC + monitoring)")


class IngestBody(BaseModel):
    documents: list[str]
    sources: list[str] | None = None


class QueryBody(BaseModel):
    question: str
    k: int | None = None


@app.get("/health")
def health():
    return {"status": "ok", "chunks": rag.get_store().count()}


@app.post("/ingest")
def ingest(body: IngestBody):
    with Timer("ingest"):
        n = rag.ingest(body.documents, body.sources)
    log.info("ingested", extra={"extra": {"chunks": n, "docs": len(body.documents)}})
    return {"chunks_indexed": n}


@app.post("/query")
def query(body: QueryBody):
    with Timer("query"):
        result = rag.answer(body.question, body.k)
    RETRIEVED.observe(result["num_contexts"])
    log.info("query", extra={"extra": {
        "latency_ms": result["latency_ms"], "contexts": result["num_contexts"]}})
    return {
        "answer": result["answer"],
        "contexts": result["contexts"],
        "num_contexts": result["num_contexts"],
        "latency_ms": result["latency_ms"],
    }


@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)
