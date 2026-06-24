from __future__ import annotations

import json
from pathlib import Path

import pytest

from python.runtime.run_scenarios import main


def test_run_scenarios_writes_aggregate_report(tmp_path: Path, monkeypatch) -> None:
    scenario_dir = tmp_path / "scenarios"
    scenario_dir.mkdir(parents=True, exist_ok=True)

    (scenario_dir / "scenario_a.json").write_text(
        """[
  {
    \"resources\": {\"gold\": 200, \"lumber\": 60},
    \"supply\": {\"used\": 10, \"cap\": 20},
    \"units\": [{\"owner\": \"self\", \"id\": \"a\", \"type\": \"peasant\", \"hp\": 100, \"position\": {\"x\": 1, \"y\": 1}}]
  }
]""",
        encoding="utf-8",
    )

    out_path = tmp_path / "scenario_report.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "run_scenarios.py",
            "--scenario-dir",
            str(scenario_dir),
            "--out",
            str(out_path),
        ],
    )

    code = main()
    assert code == 0
    assert out_path.exists()

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["scenario_count"] == 1
    assert payload["results"][0]["summary"]["total_states"] == 1
    assert payload["results"][0]["metrics"]["executed_rate"] == 1.0


def test_run_scenarios_reports_drift_against_baseline(tmp_path: Path, monkeypatch) -> None:
    scenario_dir = tmp_path / "scenarios"
    scenario_dir.mkdir(parents=True, exist_ok=True)

    (scenario_dir / "scenario_a.json").write_text(
        """[
  {
    \"resources\": {\"gold\": 200, \"lumber\": 60},
    \"supply\": {\"used\": 10, \"cap\": 20},
    \"units\": [{\"owner\": \"self\", \"id\": \"a\", \"type\": \"peasant\", \"hp\": 100, \"position\": {\"x\": 1, \"y\": 1}}]
  }
]""",
        encoding="utf-8",
    )

    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps(
            {
                "results": [
                    {
                        "scenario": "scenario_a.json",
                        "summary": {
                            "total_states": 1,
                            "executed_actions": 0,
                            "blocked_states": 1,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    out_path = tmp_path / "scenario_report.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "run_scenarios.py",
            "--scenario-dir",
            str(scenario_dir),
            "--baseline",
            str(baseline_path),
            "--max-drift",
            "0.2",
            "--out",
            str(out_path),
        ],
    )

    code = main()
    assert code == 0

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["baseline_compared"] is True
    assert payload["drift_summary"]["fail_count"] == 1
    assert payload["results"][0]["drift"]["pass"] is False


def test_run_scenarios_fail_on_drift_returns_non_zero(tmp_path: Path, monkeypatch) -> None:
    scenario_dir = tmp_path / "scenarios"
    scenario_dir.mkdir(parents=True, exist_ok=True)

    (scenario_dir / "scenario_a.json").write_text(
        """[
  {
    \"resources\": {\"gold\": 200, \"lumber\": 60},
    \"supply\": {\"used\": 10, \"cap\": 20},
    \"units\": [{\"owner\": \"self\", \"id\": \"a\", \"type\": \"peasant\", \"hp\": 100, \"position\": {\"x\": 1, \"y\": 1}}]
  }
]""",
        encoding="utf-8",
    )

    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(
        json.dumps(
            {
                "results": [
                    {
                        "scenario": "scenario_a.json",
                        "summary": {
                            "total_states": 1,
                            "executed_actions": 0,
                            "blocked_states": 1,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    out_path = tmp_path / "scenario_report.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "run_scenarios.py",
            "--scenario-dir",
            str(scenario_dir),
            "--baseline",
            str(baseline_path),
            "--max-drift",
            "0.2",
            "--fail-on-drift",
            "--out",
            str(out_path),
        ],
    )

    code = main()
    assert code == 2


def test_run_scenarios_require_baseline_match_fails_missing(tmp_path: Path, monkeypatch) -> None:
    scenario_dir = tmp_path / "scenarios"
    scenario_dir.mkdir(parents=True, exist_ok=True)

    (scenario_dir / "scenario_a.json").write_text(
        """[
  {
    \"resources\": {\"gold\": 200, \"lumber\": 60},
    \"supply\": {\"used\": 10, \"cap\": 20},
    \"units\": [{\"owner\": \"self\", \"id\": \"a\", \"type\": \"peasant\", \"hp\": 100, \"position\": {\"x\": 1, \"y\": 1}}]
  }
]""",
        encoding="utf-8",
    )

    baseline_path = tmp_path / "baseline.json"
    baseline_path.write_text(json.dumps({"results": []}), encoding="utf-8")

    out_path = tmp_path / "scenario_report.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "run_scenarios.py",
            "--scenario-dir",
            str(scenario_dir),
            "--baseline",
            str(baseline_path),
            "--require-baseline-match",
            "--out",
            str(out_path),
        ],
    )

    code = main()
    assert code == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["drift_summary"]["fail_count"] == 1
    assert payload["results"][0]["drift"]["reason"] == "missing_baseline_scenario"


def test_run_scenarios_ignores_report_files_in_scenario_dir(tmp_path: Path, monkeypatch) -> None:
    scenario_dir = tmp_path / "scenarios"
    scenario_dir.mkdir(parents=True, exist_ok=True)

    (scenario_dir / "scenario_a.json").write_text(
        """[
  {
    \"resources\": {\"gold\": 200, \"lumber\": 60},
    \"supply\": {\"used\": 10, \"cap\": 20},
    \"units\": [{\"owner\": \"self\", \"id\": \"a\", \"type\": \"peasant\", \"hp\": 100, \"position\": {\"x\": 1, \"y\": 1}}]
  }
]""",
        encoding="utf-8",
    )

    (scenario_dir / "baseline_report.json").write_text(json.dumps({"results": []}), encoding="utf-8")

    out_path = tmp_path / "scenario_report.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "run_scenarios.py",
            "--scenario-dir",
            str(scenario_dir),
            "--out",
            str(out_path),
        ],
    )

    code = main()
    assert code == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["scenario_count"] == 1
    assert payload["results"][0]["scenario"] == "scenario_a.json"
