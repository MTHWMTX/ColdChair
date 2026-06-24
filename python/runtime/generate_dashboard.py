from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from python.bn_readiness.readiness import BattleNetReadiness
from python.runtime.generate_health_report import main as generate_health


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate comprehensive system dashboard")
    parser.add_argument(
        "--reports-dir",
        default="reports",
        help="Directory containing pipeline reports",
    )
    parser.add_argument(
        "--out",
        default="reports/system_dashboard.json",
        help="Output path for dashboard JSON",
    )
    return parser


def aggregate_dashboard(reports_dir: str | Path) -> dict[str, Any]:
    """Aggregate all system metrics into a comprehensive dashboard."""
    reports_dir = Path(reports_dir)

    dashboard: dict[str, Any] = {
        "timestamp": "2026-06-24",
        "system_status": "unknown",
        "components": {},
        "metrics": {
            "test_suite": {"status": "unknown"},
            "pipeline_health": {"status": "unknown"},
            "readiness": {"status": "unknown"},
        },
        "alerts": [],
    }

    # Load test metrics
    if (reports_dir / "test_results.json").exists():
        test_data = json.loads((reports_dir / "test_results.json").read_text())
        dashboard["metrics"]["test_suite"] = test_data
        dashboard["components"]["test_suite"] = "✓"

    # Load health report
    if (reports_dir / "health_report.json").exists():
        health_data = json.loads((reports_dir / "health_report.json").read_text())
        dashboard["metrics"]["pipeline_health"] = health_data
        dashboard["components"]["health"] = "✓"
        if health_data.get("overall_status") == "healthy":
            dashboard["components"]["health_status"] = "healthy"
        else:
            dashboard["components"]["health_status"] = "degraded"
            dashboard["alerts"].append("Pipeline health is degraded - check missing reports")

    # Load readiness
    if (reports_dir / "bn_readiness.json").exists():
        readiness_data = json.loads((reports_dir / "bn_readiness.json").read_text())
        dashboard["metrics"]["readiness"] = readiness_data
        dashboard["components"]["readiness"] = "✓"
        progress = readiness_data.get("overall_progress", {})
        if progress.get("overall_readiness_percent", 0) == 100:
            dashboard["components"]["readiness_status"] = "complete"
        else:
            dashboard["components"]["readiness_status"] = f"{progress.get('overall_readiness_percent', 0):.0f}%"

    # Load experiment results
    if (reports_dir / "experiment_result.json").exists():
        exp_data = json.loads((reports_dir / "experiment_result.json").read_text())
        dashboard["components"]["experiment"] = "✓"
        if not exp_data.get("gate_passed", False):
            dashboard["alerts"].append("Last experiment did not pass gate thresholds")

    # Load scenario results
    if (reports_dir / "scenario_report.json").exists():
        scenario_data = json.loads((reports_dir / "scenario_report.json").read_text())
        dashboard["components"]["scenarios"] = f"{scenario_data.get('scenario_count', 0)} scenarios"
        pass_count = scenario_data.get("drift_summary", {}).get("pass_count", 0)
        fail_count = scenario_data.get("drift_summary", {}).get("fail_count", 0)
        if fail_count > 0:
            dashboard["alerts"].append(f"Scenario regression detected: {fail_count} failures")

    # Determine overall status
    component_count = len(dashboard["components"])
    if component_count == 0:
        dashboard["system_status"] = "initializing"
    elif len(dashboard["alerts"]) == 0:
        dashboard["system_status"] = "healthy"
    else:
        dashboard["system_status"] = "degraded"

    return dashboard


def main() -> int:
    args = build_parser().parse_args()

    dashboard = aggregate_dashboard(args.reports_dir)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(dashboard, indent=2), encoding="utf-8")

    print(json.dumps(dashboard, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
