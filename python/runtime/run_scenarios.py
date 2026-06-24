from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from python.replay.sample_loader import load_state_samples
from python.runtime.local_loop import LocalLoopRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run supervised local loop across scenario packs"
    )
    parser.add_argument(
        "--scenario-dir",
        default="scenarios/local_ai",
        help="Directory containing JSON or JSONL scenario files",
    )
    parser.add_argument(
        "--out",
        default="reports/scenario_report.json",
        help="Output path for scenario aggregate report",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    scenario_dir = Path(args.scenario_dir)
    if not scenario_dir.exists():
        raise FileNotFoundError(f"Scenario directory not found: {scenario_dir}")

    files = sorted(
        [p for p in scenario_dir.iterdir() if p.is_file() and p.suffix.lower() in {".json", ".jsonl"}]
    )

    runner = LocalLoopRunner()
    scenario_results = []

    for file_path in files:
        states = load_state_samples(file_path)
        summary, _ = runner.run_states(states)
        scenario_results.append(
            {
                "scenario": file_path.name,
                "summary": asdict(summary),
            }
        )

    payload = {
        "scenario_count": len(scenario_results),
        "results": scenario_results,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
