from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from python.policy.decision_engine import DecisionEngine
from python.runtime.action_queue import ActionQueue, RuntimeSafetyConfig


@dataclass
class LocalLoopSummary:
    total_states: int
    executed_actions: int
    blocked_states: int


class LocalLoopRunner:
    """Runs a supervised local loop for offline and local-AI testing."""

    def __init__(
        self,
        engine: DecisionEngine | None = None,
        queue: ActionQueue | None = None,
    ) -> None:
        self.engine = engine or DecisionEngine()
        self.queue = queue or ActionQueue(
            RuntimeSafetyConfig(max_actions_per_second=1000000.0, online_mode_enabled=False)
        )

    def run_states(self, states: list[dict[str, Any]]) -> tuple[LocalLoopSummary, list[dict[str, Any]]]:
        logs: list[dict[str, Any]] = []
        blocked_states = 0

        for idx, state in enumerate(states):
            intents = self.engine.decide(state)
            self.queue.enqueue(intents)
            action = self.queue.dequeue_next()

            if action is None:
                blocked_states += 1
                logs.append({"index": idx, "status": "blocked"})
                continue

            logs.append(
                {
                    "index": idx,
                    "status": "executed",
                    "action": {
                        "type": action.type,
                        "priority": action.priority,
                        "target_id": action.target_id,
                        "position": action.position,
                    },
                }
            )

        summary = LocalLoopSummary(
            total_states=len(states),
            executed_actions=len([item for item in logs if item["status"] == "executed"]),
            blocked_states=blocked_states,
        )
        return summary, logs
