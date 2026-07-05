"""Observability: structured JSON logging + Prometheus metrics.
This is the 'production' signal recruiters look for — every request is measured."""
import json
import logging
import sys
import time

from prometheus_client import Counter, Histogram

from app.config import settings


# --- structured logging ---------------------------------------------------
class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if hasattr(record, "extra"):
            payload.update(record.extra)  # type: ignore[attr-defined]
        return json.dumps(payload)


def get_logger(name: str = "ragops") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(_JsonFormatter())
        logger.addHandler(h)
        logger.setLevel(settings.log_level)
    return logger


# --- Prometheus metrics ---------------------------------------------------
REQUESTS = Counter("ragops_requests_total", "RAG requests", ["endpoint", "status"])
LATENCY = Histogram("ragops_latency_seconds", "Request latency", ["endpoint"])
RETRIEVED = Histogram("ragops_contexts_retrieved", "Contexts retrieved per query",
                      buckets=(0, 1, 2, 3, 4, 5, 8))


class Timer:
    """`with Timer('query') as t:` — records latency + a request count."""
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
        self.status = "ok"

    def __enter__(self):
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, *_):
        if exc_type:
            self.status = "error"
        LATENCY.labels(self.endpoint).observe(time.perf_counter() - self._t0)
        REQUESTS.labels(self.endpoint, self.status).inc()
        return False
