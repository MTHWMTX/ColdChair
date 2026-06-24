from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a health report for all pipeline artifacts")
    parser.add_argument(
        "--reports-dir",
        default="reports",
        help="Directory containing output reports from all pipeline runs",
    )
    parser.add_argument(
        "--out",
        default="reports/health_report.json",
        help="Output path for health report",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    reports_dir = Path(args.reports_dir)
    if not reports_dir.exists():
        print(f"Reports directory not found: {reports_dir}")
        return 1

    health = {
        "timestamp": Path(args.out).parent.name,
        "reports_found": [],
        "missing_reports": [],
        "overall_status": "unknown",
    }

    expected_reports = [
        "scenario_report.json",
        "local_loop_report.json",
        "offline_eval_from_replay.json",
        "eval_benchmark.json",
    ]

    for report_name in expected_reports:
        report_path = reports_dir / report_name
        if report_path.exists():
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            health["reports_found"].append(
                {
                    "name": report_name,
                    "exists": True,
                    "size_bytes": report_path.stat().st_size,
                }
            )
        else:
            health["missing_reports"].append(report_name)

    if not health["missing_reports"]:
        health["overall_status"] = "healthy"
    else:
        health["overall_status"] = "degraded"

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(health, indent=2), encoding="utf-8")

    print(json.dumps(health, indent=2))
    return 0 if health["overall_status"] == "healthy" else 1


if __name__ == "__main__":
    raise SystemExit(main())
