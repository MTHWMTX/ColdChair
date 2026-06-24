from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from python.replay.sample_loader import load_state_samples
from python.runtime.e2e_pipeline import E2EPipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run end-to-end pipeline on state samples")
    parser.add_argument("--samples", required=True, help="Path to JSON/JSONL game-state samples")
    parser.add_argument(
        "--out",
        default="reports/e2e_report.json",
        help="Output path for end-to-end report",
    )
    parser.add_argument(
        "--telemetry",
        default=None,
        help="Optional output path for detailed telemetry events",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    samples = load_state_samples(args.samples)
    pipeline = E2EPipeline()

    all_logs = []
    summary_data = {
        "total_samples": len(samples),
        "scenarios_executed": 0,
        "total_executed_actions": 0,
        "total_blocked_states": 0,
    }

    for state in samples:
        summary, logs, telemetry = pipeline.run_scenario(args.samples)
        if summary is None:
            continue

        all_logs.extend(logs)
        summary_data["scenarios_executed"] += 1
        summary_data["total_executed_actions"] += summary.executed_actions
        summary_data["total_blocked_states"] += summary.blocked_states

    payload = {
        "summary": summary_data,
        "telemetry_summary": asdict(pipeline._get_telemetry_summary()),
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.telemetry:
        telemetry_path = Path(args.telemetry)
        telemetry_path.parent.mkdir(parents=True, exist_ok=True)
        telemetry_path.write_text(json.dumps(pipeline.get_telemetry(), indent=2), encoding="utf-8")
        print(f"telemetry written to {telemetry_path}")

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
