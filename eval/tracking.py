"""Thin MLflow wrapper. Every eval/gate run logs params + metrics so regressions are
visible as a trend in the MLflow UI (`mlflow ui`), not just a one-off console number.

Degrades gracefully: if MLflow is missing or its backend errors, the run still completes
and prints metrics — the quality gate must never be blocked by the tracking layer.
"""
from __future__ import annotations

import contextlib
import os

from app.config import settings


@contextlib.contextmanager
def track(experiment: str, params: dict):
    log = lambda metrics: None  # noqa: E731 — default no-op if tracking is unavailable
    try:
        # The file store is in "maintenance mode" on recent MLflow and raises unless opted
        # in; keep the simple `file:./mlruns` backend that `mlflow ui` reads out of the box.
        os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
        import mlflow

        mlflow.set_tracking_uri(settings.mlflow_uri)
        mlflow.set_experiment(experiment)
        with mlflow.start_run():
            mlflow.log_params(params)
            yield lambda metrics: mlflow.log_metrics(
                {k: float(v) for k, v in metrics.items() if isinstance(v, (int, float))})
        return
    except Exception as exc:  # tracking is best-effort, never fatal
        print(f"[tracking] MLflow disabled ({type(exc).__name__}: {exc}); continuing")
        yield log
