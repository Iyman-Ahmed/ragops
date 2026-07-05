"""L1 — the deterministic retrieval quality gate. THE CENTERPIECE.

Runs on every PR (including forks): no LLM, no secrets, no network beyond the cached
embedding model. Scores recall@1 and recall@k against gold spans and FAILS THE BUILD when
the Wilson lower bound of recall@1 falls below threshold — i.e. only on a statistically
distinguishable regression, not on sampling noise.

Thresholds are calibrated from the observed baseline (see eval/calibrate.py and
docs/gate_calibration.md). Run:  python -m eval.retrieval_gate
"""
import json
import sys

from eval.harness import RunConfig, run_retrieval
from eval.tracking import track

# Baseline on this corpus: recall@1 = 0.842 (Wilson LB 0.696), recall@k = 1.00.
# Gate below these with margin so a real regression fails but sampling noise does not.
# The margin is wide by design: measured regressions land at Wilson LB <= 0.17 and
# recall@k <= 0.45, far under these floors (see docs/gate_calibration.md).
THRESHOLDS = {
    "recall_at_1_wilson_lb": 0.55,   # rank-quality floor (catches embedding/rank regressions)
    "recall_at_k": 0.90,             # retrieval-coverage floor (catches lost docs, low top_k)
}


def main() -> int:
    cfg = RunConfig()
    with track("ragops-retrieval-gate", {
            "embed_model": cfg.embed_model, "top_k": cfg.top_k,
            "chunk_chars": cfg.chunk_chars}) as log:
        metrics = run_retrieval(cfg)
        log(metrics)

    print(json.dumps(metrics, indent=2))
    failed = [k for k, thr in THRESHOLDS.items() if metrics[k] < thr]
    if failed:
        for k in failed:
            print(f"  {k} = {metrics[k]} < {THRESHOLDS[k]}", file=sys.stderr)
        print(f"RETRIEVAL GATE FAILED: {failed}", file=sys.stderr)
        return 1
    print(f"RETRIEVAL GATE PASSED (thresholds {THRESHOLDS})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
