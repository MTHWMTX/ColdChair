from __future__ import annotations

import json
from pathlib import Path

from python.runtime.create_scenario_baseline import main


def test_create_scenario_baseline_writes_output(tmp_path: Path, monkeypatch) -> None:
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

    out_path = tmp_path / "baseline_report.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "create_scenario_baseline.py",
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
