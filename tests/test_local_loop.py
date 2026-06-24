from __future__ import annotations

import json
from pathlib import Path

from python.runtime.action_queue import ActionQueue, RuntimeSafetyConfig
from python.runtime.local_loop import LocalLoopRunner
from python.runtime.run_local_loop import main


def test_local_loop_executes_actions() -> None:
    states = [
        {
            "resources": {"gold": 200, "lumber": 60},
            "supply": {"used": 10, "cap": 20},
            "units": [{"owner": "self", "id": "a", "type": "peasant", "hp": 100, "position": {"x": 1, "y": 1}}],
        },
        {
            "resources": {"gold": 20, "lumber": 0},
            "supply": {"used": 9, "cap": 20},
            "units": [{"owner": "self", "id": "b", "type": "footman", "hp": 300, "position": {"x": 3, "y": 4}}],
        },
    ]

    queue = ActionQueue(RuntimeSafetyConfig(max_actions_per_second=1000000.0, online_mode_enabled=False))
    runner = LocalLoopRunner(queue=queue)
    summary, logs = runner.run_states(states)

    assert summary.total_states == 2
    assert summary.executed_actions == 2
    assert summary.blocked_states == 0
    assert logs[0]["status"] == "executed"
    assert logs[0]["command"]["op"] == "key_press"
    assert logs[0]["dry_run"] is True


def test_local_loop_blocks_when_window_inactive() -> None:
    states = [
        {
            "resources": {"gold": 200, "lumber": 60},
            "supply": {"used": 10, "cap": 20},
            "units": [{"owner": "self", "id": "a", "type": "peasant", "hp": 100, "position": {"x": 1, "y": 1}}],
        }
    ]

    queue = ActionQueue(RuntimeSafetyConfig(max_actions_per_second=1000000.0, online_mode_enabled=False))
    queue.set_active_window_ok(False)
    runner = LocalLoopRunner(queue=queue)
    summary, _ = runner.run_states(states)

    assert summary.executed_actions == 0
    assert summary.blocked_states == 1


def test_local_loop_cli_writes_report(tmp_path: Path, monkeypatch) -> None:
    sample_path = tmp_path / "samples.json"
    out_path = tmp_path / "loop_report.json"

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
            "run_local_loop.py",
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
    assert payload["summary"]["total_states"] == 1
    assert payload["summary"]["executed_actions"] == 1
    assert payload["logs"][0]["dry_run"] is True
