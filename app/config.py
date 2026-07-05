"""Runtime settings, read from the environment (12-factor).

Everything the pipeline needs is here so a regression demo is a one-line env change
(e.g. CHUNK_CHARS or TOP_K) — which is exactly what the eval gate is designed to catch.
"""
import os
from dataclasses import dataclass


def _env(name: str, default: str) -> str:
    """Read an env var, treating an empty string as unset. CI wires unset repo
    vars/secrets as "" (e.g. LLM_API_KEY: ${{ secrets.LLM_API_KEY }}); an empty api_key
    would make the OpenAI client raise at import, so empty must fall back to the default."""
    return os.getenv(name) or default


@dataclass(frozen=True)
class Settings:
    # LLM (OpenAI-compatible — works with OpenAI, LM Studio, vLLM, Ollama, …)
    llm_base_url: str = _env("LLM_BASE_URL", "http://localhost:1234/v1")
    llm_api_key: str = _env("LLM_API_KEY", "not-needed")
    llm_model: str = os.getenv("LLM_MODEL", "")           # "" = auto-detect first model
    llm_timeout: float = float(_env("LLM_TIMEOUT", "60"))

    # Retrieval
    embed_model: str = _env("EMBED_MODEL", "all-MiniLM-L6-v2")  # wired into the store
    top_k: int = int(_env("TOP_K", "4"))
    chunk_chars: int = int(_env("CHUNK_CHARS", "700"))
    chunk_overlap_sentences: int = int(_env("CHUNK_OVERLAP_SENTENCES", "1"))

    # Storage — PersistentClient so /ingest survives a restart (see store.py).
    chroma_path: str = _env("CHROMA_PATH", "./chroma_db")
    collection: str = _env("COLLECTION", "ragops")
    corpus_dir: str = _env("CORPUS_DIR", "eval/corpus")

    # Ops
    log_level: str = _env("LOG_LEVEL", "INFO")
    mlflow_uri: str = _env("MLFLOW_TRACKING_URI", "file:./mlruns")


settings = Settings()
