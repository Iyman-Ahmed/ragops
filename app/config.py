"""Runtime settings, read from the environment (12-factor).

Everything the pipeline needs is here so a regression demo is a one-line env change
(e.g. CHUNK_CHARS or TOP_K) — which is exactly what the eval gate is designed to catch.
"""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # LLM (OpenAI-compatible — works with OpenAI, LM Studio, vLLM, Ollama, …)
    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:1234/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "not-needed")
    llm_model: str = os.getenv("LLM_MODEL", "")           # "" = auto-detect first model
    llm_timeout: float = float(os.getenv("LLM_TIMEOUT", "60"))

    # Retrieval
    embed_model: str = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")  # wired into the store
    top_k: int = int(os.getenv("TOP_K", "4"))
    chunk_chars: int = int(os.getenv("CHUNK_CHARS", "700"))
    chunk_overlap_sentences: int = int(os.getenv("CHUNK_OVERLAP_SENTENCES", "1"))

    # Storage — PersistentClient so /ingest survives a restart (see store.py).
    chroma_path: str = os.getenv("CHROMA_PATH", "./chroma_db")
    collection: str = os.getenv("COLLECTION", "ragops")
    corpus_dir: str = os.getenv("CORPUS_DIR", "eval/corpus")

    # Ops
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    mlflow_uri: str = os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns")


settings = Settings()
