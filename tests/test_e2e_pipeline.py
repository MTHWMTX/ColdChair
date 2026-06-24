from __future__ import annotations

import json
from pathlib import Path

from python.runtime.action_queue import ActionQueue, RuntimeSafetyConfig
from python.runtime.e2e_pipeline import E2EPipeline
from python.runtime.executor import IntentExecutor


def test_e2e_pipeline_executes_scenario() -> None:
    pipeline = E2EPipeline()
    sample_path = Path(__file__).parent.parent / "examples" / "sample_states.json"

    summary, logs, telemetry = pipeline.run_scenario(str(sample_path))

    assert summary is not None
    assert summary.total_states == 2
    assert len(logs) == 2
    assert telemetry.total_events >= 3


def test_e2e_pipeline_collects_telemetry() -> None:
    pipeline = E2EPipeline()
    sample_path = Path(__file__).parent.parent / "examples" / "sample_states.json"

    summary, logs, telemetry = pipeline.run_scenario(str(sample_path))

    events = pipeline.get_telemetry()
    assert len(events) > 0
    assert any(e["event_type"] == "scenario_loaded" for e in events)


def test_e2e_pipeline_with_inactive_window() -> None:
    queue = ActionQueue(RuntimeSafetyConfig(max_actions_per_second=1000000.0, online_mode_enabled=False))
    queue.set_active_window_ok(False)
    executor = IntentExecutor(dry_run=True)

    pipeline = E2EPipeline(queue=queue, executor=executor)
    sample_path = Path(__file__).parent.parent / "examples" / "sample_states.json"

    summary, logs, telemetry = pipeline.run_scenario(str(sample_path))

    assert summary is not None
    assert summary.blocked_states > 0
