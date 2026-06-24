from __future__ import annotations

import json
from pathlib import Path

from python.runtime.generate_health_report import main


def test_generate_health_report_finds_reports(tmp_path: Path, monkeypatch) -> None:
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    (reports_dir / "scenario_report.json").write_text(json.dumps({"test": "data"}), encoding="utf-8")
    (reports_dir / "local_loop_report.json").write_text(json.dumps({"test": "data"}), encoding="utf-8")

    out_path = tmp_path / "health.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "generate_health_report.py",
            "--reports-dir",
            str(reports_dir),
            "--out",
            str(out_path),
        ],
    )

    code = main()
    assert out_path.exists()

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(payload["reports_found"]) == 2
    assert len(payload["missing_reports"]) == 2
    assert payload["overall_status"] == "degraded"
