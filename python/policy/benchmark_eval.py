from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from statistics import mean
from time import perf_counter

from python.policy.evaluator import OfflinePolicyEvaluator
from python.replay.sample_loader import load_state_samples


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Benchmark offline policy evaluation")
    parser.add_argument("--samples", required=True, help="Path to JSON/JSONL game-state samples")
    parser.add_argument("--runs", type=int, default=20, help="Number of benchmark runs")
    parser.add_argument(
        "--out",
        default="reports/eval_benchmark.json",
        help="Output path for benchmark summary",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    samples = load_state_samples(args.samples)
    evaluator = OfflinePolicyEvaluator()

    durations_ms: list[float] = []
    summary_payload = None

    for _ in range(args.runs):
        start = perf_counter()
        summary = evaluator.evaluate(samples)
        elapsed_ms = (perf_counter() - start) * 1000.0
        durations_ms.append(elapsed_ms)
        summary_payload = asdict(summary)

    payload = {
        "runs": args.runs,
        "sample_count": len(samples),
        "latency_ms": {
            "mean": mean(durations_ms) if durations_ms else 0.0,
            "min": min(durations_ms) if durations_ms else 0.0,
            "max": max(durations_ms) if durations_ms else 0.0,
        },
        "summary": summary_payload,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
