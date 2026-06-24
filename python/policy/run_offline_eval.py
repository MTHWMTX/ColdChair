from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from python.policy.evaluator import OfflinePolicyEvaluator
from python.replay.sample_loader import load_state_samples


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run offline policy evaluation over state samples")
    parser.add_argument("--samples", required=True, help="Path to JSON/JSONL game-state samples")
    parser.add_argument(
        "--out",
        default="reports/offline_eval.json",
        help="Output path for evaluation summary JSON",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    samples = load_state_samples(args.samples)
    evaluator = OfflinePolicyEvaluator()
    summary = evaluator.evaluate(samples)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(asdict(summary), indent=2), encoding="utf-8")

    print(json.dumps(asdict(summary), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
