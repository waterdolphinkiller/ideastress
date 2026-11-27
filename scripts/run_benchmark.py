"""Standalone runner script for the 10-case IdeaStress Benchmark Suite."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ideastress.benchmarks.suite import run_benchmark_suite

if __name__ == "__main__":
    report = run_benchmark_suite()
    print(json.dumps(report, indent=2))
    if report["pass_rate_pct"] < 100.0 or report["unsupported_verified_claim_rate_pct"] > 0.0:
        sys.exit(1)
