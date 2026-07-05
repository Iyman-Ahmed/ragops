"""Vector store — a thin wrapper over ChromaDB.

Kept deliberately small and swappable (the README's "what this proves" leans on the
production wrapper, not on retrieval cleverness). Responsibilities:

* PersistentClient by default → ingested data survives a process/container restart.
  (The original scaffold used EphemeralClient, so every /ingest evaporated on restart
  and a multi-worker deploy answered queries from an empty index.)
* Deterministic chunk ids + upsert → re-ingesting the same corpus is idempotent; no
  duplicate chunks silently polluting top-k after a restart.
* Embedding function chosen by name → the eval calibration harness can inject an
  "embedding swap" regression and confirm the gate fires.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from chromadb.utils import embedding_functions

from app.chunking import chunk_document
from app.config import settings


def _embedding_fn(model: str):
    """Map a model name to a Chroma embedding function.

    Default is the ONNX MiniLM (no torch, ~80 MB, cached) so CI is light and
    deterministic. `hash-<dim>` is an intentionally weak deterministic embedding used
    only by the calibration harness to simulate an embedding-quality regression.
    """
    if model.startswith("hash-"):
        return _HashEmbeddingFunction(int(model.split("-", 1)[1]))
    return embedding_functions.ONNXMiniLM_L6_V2()


class _HashEmbeddingFunction(EmbeddingFunction):
    """Deterministic hashed bag-of-tokens embedding. Semantically weak on purpose — used
    by the calibration harness to prove the retrieval gate catches an embedding regression.
    Uses a stable hash (not Python's salted hash) so results are reproducible across runs."""
    def __init__(self, dim: int = 64):
        self._dim = dim

    def name(self) -> str:
        return f"hash-{self._dim}"

    def get_config(self) -> dict:
        return {"dim": self._dim}

    @staticmethod
    def build_from_config(config: dict) -> _HashEmbeddingFunction:
        return _HashEmbeddingFunction(config["dim"])

    def __call__(self, input: Documents) -> Embeddings:
        vecs = []
        for text in input:
            v = [0.0] * self._dim
            for tok in text.lower().split():
                bucket = int(hashlib.md5(tok.encode()).hexdigest(), 16) % self._dim
                v[bucket] += 1.0
            norm = sum(x * x for x in v) ** 0.5 or 1.0
            vecs.append([x / norm for x in v])
        return vecs


@dataclass
class Retrieved:
    text: str
    source: str
    start: int
    end: int


class Store:
    def __init__(self, path: str | None = None, collection: str | None = None,
                 embed_model: str | None = None, persistent: bool = True):
        model = embed_model or settings.embed_model
        self._ef = _embedding_fn(model)
        if persistent:
            self._client = chromadb.PersistentClient(path=path or settings.chroma_path)
        else:
            self._client = chromadb.EphemeralClient()      # tests only
        self._collection = self._client.get_or_create_collection(
            collection or settings.collection, embedding_function=self._ef,
            metadata={"embed_model": model})

    def ingest_document(self, text: str, source: str,
                        size: int | None = None) -> int:
        chunks = chunk_document(text, source, size or settings.chunk_chars,
                                settings.chunk_overlap_sentences)
        if not chunks:
            return 0
        self._collection.upsert(
            ids=[c.id() for c in chunks],
            documents=[c.text for c in chunks],
            metadatas=[{"source": c.source, "start": c.start, "end": c.end}
                       for c in chunks],
        )
        return len(chunks)

    def ingest(self, documents: list[str], sources: list[str] | None = None) -> int:
        sources = sources or [f"doc-{i}" for i in range(len(documents))]
        return sum(self.ingest_document(d, s)
                   for d, s in zip(documents, sources, strict=True))

    def query(self, question: str, k: int | None = None) -> list[Retrieved]:
        k = k or settings.top_k
        n = self._collection.count()
        if n == 0:
            return []
        res = self._collection.query(query_texts=[question], n_results=min(k, n),
                                     include=["documents", "metadatas"])
        docs = res.get("documents") or [[]]
        metas = res.get("metadatas") or [[]]
        out = []
        for text, meta in zip(docs[0], metas[0], strict=True):
            out.append(Retrieved(text, meta.get("source", ""),
                                 int(meta.get("start", 0)), int(meta.get("end", 0))))
        return out

    def count(self) -> int:
        return self._collection.count()

    def reset(self) -> None:
        self._client.delete_collection(self._collection.name)
        self._collection = self._client.get_or_create_collection(
            self._collection.name, embedding_function=self._ef)
