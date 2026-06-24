from __future__ import annotations

from pathlib import Path

import pytest

from python.runtime.generate_dashboard import aggregate_dashboard


def test_generate_dashboard_empty_reports(tmp_path: Path) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    dashboard = aggregate_dashboard(reports_dir)

    assert dashboard["system_status"] == "initializing"
    assert len(dashboard["alerts"]) == 0


def test_generate_dashboard_with_health_report(tmp_path: Path) -> None:
    import json

    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    health_data = {
        "overall_status": "healthy",
        "reports_found": [{"name": "test.json"}],
        "missing_reports": [],
    }
    (reports_dir / "health_report.json").write_text(json.dumps(health_data), encoding="utf-8")

    dashboard = aggregate_dashboard(reports_dir)

    assert "health" in dashboard["components"]
    assert dashboard["metrics"]["pipeline_health"]["overall_status"] == "healthy"
