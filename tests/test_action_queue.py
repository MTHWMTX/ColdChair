from __future__ import annotations

from python.policy.decision_engine import ActionIntent
from python.runtime.action_queue import ActionQueue, RuntimeSafetyConfig


def test_queue_orders_by_priority() -> None:
    queue = ActionQueue(RuntimeSafetyConfig(max_actions_per_second=1000.0, online_mode_enabled=False))
    queue.enqueue(
        [
            ActionIntent(type="low", priority=1),
            ActionIntent(type="high", priority=9),
        ]
    )

    first = queue.dequeue_next()

    assert first is not None
    assert first.type == "high"


def test_queue_blocks_when_kill_switch_is_engaged() -> None:
    queue = ActionQueue(RuntimeSafetyConfig(max_actions_per_second=1000.0, online_mode_enabled=False))
    queue.enqueue([ActionIntent(type="gather_resources", priority=1)])
    queue.engage_kill_switch()

    assert queue.dequeue_next() is None


def test_queue_blocks_online_only_actions_when_offline_mode() -> None:
    queue = ActionQueue(RuntimeSafetyConfig(max_actions_per_second=1000.0, online_mode_enabled=False))
    queue.enqueue([ActionIntent(type="join_queue", priority=10)])

    assert queue.dequeue_next() is None


def test_queue_blocks_when_window_not_active() -> None:
    queue = ActionQueue(RuntimeSafetyConfig(max_actions_per_second=1000.0, online_mode_enabled=False))
    queue.enqueue([ActionIntent(type="gather_resources", priority=10)])
    queue.set_active_window_ok(False)

    assert queue.dequeue_next() is None
