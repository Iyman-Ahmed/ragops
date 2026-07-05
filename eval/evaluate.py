"""Full evaluation report — retrieval (always) + generation (if an endpoint is reachable).

This is the human-facing report; the blocking CI gates live in retrieval_gate.py (L1) and
answer_gate.py (L3). Everything is logged to MLflow so you can watch quality as a trend.

Run:  python -m eval.evaluate
"""
import json

from app import llm
from app.config import settings
from eval.harness import RunConfig, run_generation, run_retrieval
from eval.tracking import track


def _endpoint_reachable() -> bool:
    try:
        llm._client.with_options(timeout=5).models.list()
        return True
    except Exception:
        return False


def main() -> int:
    cfg = RunConfig()
    report = {"config": {"embed_model": cfg.embed_model, "top_k": cfg.top_k,
                         "chunk_chars": cfg.chunk_chars}}

    with track("ragops-eval", report["config"]) as log:
        retrieval = run_retrieval(cfg)
        report["retrieval"] = retrieval
        log(retrieval)

        if _endpoint_reachable():
            generation = run_generation(cfg)
            report["generation"] = generation
            log(generation)
        else:
            report["generation"] = f"skipped — no LLM at {settings.llm_base_url}"

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
