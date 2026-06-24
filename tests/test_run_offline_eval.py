from __future__ import annotations

import json
from pathlib import Path

from python.policy.run_offline_eval import main


def test_run_offline_eval_writes_report(tmp_path: Path, monkeypatch) -> None:
    sample_path = tmp_path / "samples.json"
    out_path = tmp_path / "report.json"

    sample_path.write_text(
        """[
  {
    \"resources\": {\"gold\": 200, \"lumber\": 60},
    \"supply\": {\"used\": 10, \"cap\": 20},
    \"units\": [{\"owner\": \"self\", \"id\": \"a\", \"type\": \"peasant\", \"hp\": 100, \"position\": {\"x\": 1, \"y\": 1}}]
  }
]""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "run_offline_eval.py",
            "--samples",
            str(sample_path),
            "--out",
            str(out_path),
        ],
    )

    code = main()
    assert code == 0
    assert out_path.exists()

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["total_states"] == 1
    assert payload["train_unit_rate"] == 1.0
    assert payload["gate"]["passed"] is False
    assert "gather_rate below threshold" in payload["gate"]["reasons"][0]
