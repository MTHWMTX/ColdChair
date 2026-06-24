from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from python.replay.sample_loader import load_state_samples
from python.runtime.action_queue import ActionQueue, RuntimeSafetyConfig
from python.runtime.e2e_pipeline import E2EPipeline
from python.runtime.executor import IntentExecutor
from python.policy.decision_engine import DecisionEngine


class TestE2EIntegration:
    """Integration tests for complete end-to-end pipeline workflows."""

    def test_e2e_full_pipeline_on_sample_states(self) -> None:
        """Test complete pipeline from state loading through execution."""
        pipeline = E2EPipeline()
        sample_path = Path(__file__).parent.parent / "examples" / "sample_states.json"

        summary, logs, telemetry = pipeline.run_scenario(str(sample_path))

        assert summary is not None
        assert summary.total_states == 2
        assert summary.executed_actions == 2
        assert summary.blocked_states == 0
        assert len(logs) == 2

    def test_e2e_pipeline_with_rate_limiting(self) -> None:
        """Test pipeline with rate-limited action queue."""
        queue = ActionQueue(RuntimeSafetyConfig(max_actions_per_second=1.0, online_mode_enabled=False))
        pipeline = E2EPipeline(queue=queue)
        sample_path = Path(__file__).parent.parent / "examples" / "sample_states.json"

        summary, logs, telemetry = pipeline.run_scenario(str(sample_path))

        assert summary is not None
        assert len(logs) == 2

    def test_e2e_pipeline_with_window_blocked(self) -> None:
        """Test that pipeline respects window-inactive blocking."""
        queue = ActionQueue(RuntimeSafetyConfig(max_actions_per_second=1000000.0, online_mode_enabled=False))
        queue.set_active_window_ok(False)
        executor = IntentExecutor(dry_run=True)

        pipeline = E2EPipeline(queue=queue, executor=executor)
        sample_path = Path(__file__).parent.parent / "examples" / "sample_states.json"

        summary, logs, telemetry = pipeline.run_scenario(str(sample_path))

        assert summary is not None
        assert summary.blocked_states > 0

    def test_e2e_pipeline_telemetry_accuracy(self) -> None:
        """Test that telemetry accurately tracks pipeline stages."""
        pipeline = E2EPipeline()
        sample_path = Path(__file__).parent.parent / "examples" / "sample_states.json"

        summary, logs, telemetry = pipeline.run_scenario(str(sample_path))

        events = pipeline.get_telemetry()
        assert len(events) > 0

        # Check that we have load and execution events
        event_types = [e["event_type"] for e in events]
        assert "scenario_loaded" in event_types
        assert "executed" in event_types

        # Verify telemetry summary matches event count
        assert telemetry.total_events == len(events)

    def test_e2e_pipeline_with_custom_engine(self) -> None:
        """Test pipeline with custom decision engine."""
        engine = DecisionEngine()
        pipeline = E2EPipeline(engine=engine)
        sample_path = Path(__file__).parent.parent / "examples" / "sample_states.json"

        summary, logs, telemetry = pipeline.run_scenario(str(sample_path))

        assert summary is not None
        assert len(logs) >= 2

    def test_e2e_pipeline_dry_run_mode(self) -> None:
        """Test pipeline in dry-run executor mode."""
        executor = IntentExecutor(dry_run=True)
        pipeline = E2EPipeline(executor=executor)
        sample_path = Path(__file__).parent.parent / "examples" / "sample_states.json"

        summary, logs, telemetry = pipeline.run_scenario(str(sample_path))

        # In dry-run, all actions should be recorded as "executed" with dry_run=true
        assert summary is not None
        assert all(log.get("dry_run", False) for log in logs)

    def test_e2e_pipeline_invalid_sample_path(self) -> None:
        """Test pipeline gracefully handles invalid sample paths."""
        pipeline = E2EPipeline()
        summary, logs, telemetry = pipeline.run_scenario("/nonexistent/path.json")

        assert summary is None
        assert len(logs) == 0
        assert telemetry.total_events > 0
        assert len(telemetry.execution_errors) > 0
