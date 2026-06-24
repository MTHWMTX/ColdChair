from __future__ import annotations

import json
from pathlib import Path

from python.policy.benchmark_eval import main


def test_benchmark_eval_writes_report(tmp_path: Path, monkeypatch) -> None:
    sample_path = tmp_path / "samples.json"
    out_path = tmp_path / "benchmark.json"

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
            "benchmark_eval.py",
            "--samples",
            str(sample_path),
            "--runs",
            "3",
            "--out",
            str(out_path),
        ],
    )

    code = main()
    assert code == 0
    assert out_path.exists()

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["runs"] == 3
    assert payload["sample_count"] == 1
    assert payload["summary"]["total_states"] == 1
