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
    parser.add_argument(
        "--baseline",
        default=None,
        help="Optional path to a previous scenario report for drift comparison",
    )
    parser.add_argument(
        "--max-drift",
        type=float,
        default=0.15,
        help="Maximum allowed executed-rate drift versus baseline",
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

    baseline_rates: dict[str, float] = {}
    if args.baseline:
        baseline_payload = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
        for item in baseline_payload.get("results", []):
            scenario = item.get("scenario")
            summary = item.get("summary", {})
            if not scenario:
                continue
            total = int(summary.get("total_states", 0))
            executed = int(summary.get("executed_actions", 0))
            baseline_rates[str(scenario)] = (executed / total) if total > 0 else 0.0

    for file_path in files:
        states = load_state_samples(file_path)
        summary, _ = runner.run_states(states)
        executed_rate = (summary.executed_actions / summary.total_states) if summary.total_states > 0 else 0.0

        drift_payload = None
        baseline_rate = baseline_rates.get(file_path.name)
        if baseline_rate is not None:
            drift = abs(executed_rate - baseline_rate)
            drift_payload = {
                "baseline_executed_rate": baseline_rate,
                "current_executed_rate": executed_rate,
                "drift": drift,
                "pass": drift <= args.max_drift,
            }

        scenario_results.append(
            {
                "scenario": file_path.name,
                "summary": asdict(summary),
                "metrics": {
                    "executed_rate": executed_rate,
                },
                "drift": drift_payload,
            }
        )

    pass_count = len([r for r in scenario_results if r.get("drift") and r["drift"]["pass"]])
    fail_count = len([r for r in scenario_results if r.get("drift") and not r["drift"]["pass"]])

    payload = {
        "scenario_count": len(scenario_results),
        "baseline_compared": args.baseline is not None,
        "max_drift": args.max_drift,
        "drift_summary": {
            "pass_count": pass_count,
            "fail_count": fail_count,
        },
        "results": scenario_results,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
