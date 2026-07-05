"""L3 — generation quality gate. Endpoint-gated and honest about it.

Answer quality needs a live LLM, which is stochastic and not always available in CI. So
this layer:

* runs and BLOCKS when an LLM endpoint is reachable (answer accuracy + refusal accuracy),
  gated at a low CATASTROPHE floor via the Wilson lower bound — it catches collapses
  (model swap, context-ignoring prompt), not 2-point wobble;
* when NO endpoint is reachable, prints a loud DISARMED banner and exits 0. It never
  silently passes: the CI log shows in bold that the generation gate did not run, so a
  green build is never mistaken for "generation verified".

Run:  python -m eval.answer_gate
"""
import json
import sys

from app import llm
from app.config import settings
from eval.harness import RunConfig, run_generation
from eval.tracking import track

THRESHOLDS = {
    "answer_wilson_lb": 0.50,     # catastrophe floor — a healthy small model clears this easily
    "refusal_accuracy": 0.50,     # must refuse most unanswerable questions
}


def _endpoint_reachable() -> bool:
    try:
        llm._client.with_options(timeout=5).models.list()
        return True
    except Exception:
        return False


def _disarmed_banner() -> None:
    print("=" * 72, file=sys.stderr)
    print("  GENERATION GATE DISARMED — no LLM endpoint reachable at "
          f"{settings.llm_base_url}", file=sys.stderr)
    print("  Retrieval gate (L1) and prompt/contract tests (L2) still enforced.", file=sys.stderr)
    print("  Set LLM_BASE_URL to a reachable OpenAI-compatible server to ARM this gate.",
          file=sys.stderr)
    print("=" * 72, file=sys.stderr)


def main() -> int:
    if not _endpoint_reachable():
        _disarmed_banner()
        return 0

    cfg = RunConfig()
    with track("ragops-answer-gate", {
            "llm_model": settings.llm_model or "auto", "embed_model": cfg.embed_model,
            "top_k": cfg.top_k}) as log:
        metrics = run_generation(cfg)
        log(metrics)

    print(json.dumps(metrics, indent=2))
    failed = [k for k, thr in THRESHOLDS.items() if metrics[k] < thr]
    if failed:
        print(f"ANSWER GATE FAILED: {failed} below {THRESHOLDS}", file=sys.stderr)
        return 1
    print("ANSWER GATE PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
