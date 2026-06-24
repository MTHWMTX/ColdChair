from __future__ import annotations

from dataclasses import dataclass
from time import monotonic

from python.contracts.validator import validate_action_intent
from python.policy.decision_engine import ActionIntent


@dataclass
class RuntimeSafetyConfig:
    max_actions_per_second: float = 6.0
    online_mode_enabled: bool = False


class ActionQueue:
    """Safety-aware action queue for supervised runtime execution."""

    def __init__(self, config: RuntimeSafetyConfig | None = None) -> None:
        self.config = config or RuntimeSafetyConfig()
        self._queue: list[ActionIntent] = []
        self._last_action_timestamp = 0.0
        self._kill_switch_engaged = False
        self._active_window_ok = True

    def set_active_window_ok(self, value: bool) -> None:
        self._active_window_ok = value

    def engage_kill_switch(self) -> None:
        self._kill_switch_engaged = True

    def clear_kill_switch(self) -> None:
        self._kill_switch_engaged = False

    def enqueue(self, intents: list[ActionIntent]) -> None:
        sorted_intents = sorted(intents, key=lambda i: i.priority, reverse=True)
        for intent in sorted_intents:
            validate_action_intent(intent)
        self._queue.extend(sorted_intents)

    def dequeue_next(self) -> ActionIntent | None:
        if self._kill_switch_engaged:
            return None

        if not self._active_window_ok:
            return None

        if not self.config.online_mode_enabled and self._contains_online_only_action():
            return None

        now = monotonic()
        min_interval = 1.0 / self.config.max_actions_per_second
        if now - self._last_action_timestamp < min_interval:
            return None

        if not self._queue:
            return None

        self._last_action_timestamp = now
        return self._queue.pop(0)

    def _contains_online_only_action(self) -> bool:
        online_only = {"join_queue", "accept_match", "start_matchmaking"}
        return any(intent.type in online_only for intent in self._queue)
