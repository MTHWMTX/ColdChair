from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Callable

from python.policy.decision_engine import DecisionEngine
from python.replay.sample_loader import load_state_samples
from python.runtime.action_queue import ActionQueue, RuntimeSafetyConfig
from python.runtime.executor import IntentExecutor
from python.runtime.local_loop import LocalLoopRunner


@dataclass
class TelemetryEvent:
    phase: str
    timestamp_ms: float
    event_type: str
    details: dict[str, Any]


@dataclass
class PipelineTelemetry:
    total_events: int
    events_by_phase: dict[str, int]
    execution_errors: list[str]


class E2EPipeline:
    """End-to-end orchestrator: state loading → decision → queue → execution → telemetry collection."""

    def __init__(
        self,
        engine: DecisionEngine | None = None,
        queue: ActionQueue | None = None,
        executor: IntentExecutor | None = None,
    ) -> None:
        self.engine = engine or DecisionEngine()
        self.queue = queue or ActionQueue(
            RuntimeSafetyConfig(max_actions_per_second=1000000.0, online_mode_enabled=False)
        )
        self.executor = executor or IntentExecutor(dry_run=True)
        self.telemetry: list[TelemetryEvent] = []
        self._phase_counter = 0

    def run_scenario(self, sample_path: str) -> tuple[Any, list[dict[str, Any]], PipelineTelemetry]:
        """Load and execute a complete scenario pipeline."""
        try:
            states = load_state_samples(sample_path)
            self._emit_event("load", "scenario_loaded", {"sample_count": len(states)})
        except Exception as exc:
            self._emit_event("load", "scenario_load_failed", {"error": str(exc)})
            return None, [], self._get_telemetry_summary()

        runner = LocalLoopRunner(engine=self.engine, queue=self.queue, executor=self.executor)
        summary, logs = runner.run_states(states)

        for log_entry in logs:
            self._emit_event(
                "execution",
                log_entry.get("status", "unknown"),
                {
                    "state_index": log_entry["index"],
                    "action_type": log_entry.get("action", {}).get("type"),
                },
            )

        return summary, logs, self._get_telemetry_summary()

    def _emit_event(self, phase: str, event_type: str, details: dict[str, Any]) -> None:
        self._phase_counter += 1
        event = TelemetryEvent(
            phase=phase,
            timestamp_ms=self._phase_counter * 0.1,
            event_type=event_type,
            details=details,
        )
        self.telemetry.append(event)

    def _get_telemetry_summary(self) -> PipelineTelemetry:
        phase_counts: dict[str, int] = {}
        errors: list[str] = []

        for event in self.telemetry:
            phase_counts[event.phase] = phase_counts.get(event.phase, 0) + 1
            if "error" in event.event_type.lower() or "failed" in event.event_type.lower():
                errors.append(f"{event.event_type}: {event.details}")

        return PipelineTelemetry(
            total_events=len(self.telemetry),
            events_by_phase=phase_counts,
            execution_errors=errors,
        )

    def get_telemetry(self) -> list[dict[str, Any]]:
        return [asdict(e) for e in self.telemetry]
