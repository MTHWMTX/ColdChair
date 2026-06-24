from __future__ import annotations

from python.policy.decision_engine import ActionIntent
from python.runtime.executor import IntentExecutor


def test_executor_maps_train_unit_intent() -> None:
    executor = IntentExecutor(dry_run=True)

    result = executor.execute(ActionIntent(type="train_unit", priority=10))

    assert result.status == "executed"
    assert result.command["op"] == "key_press"
    assert result.command["key"] == "T"
    assert result.dry_run is True


def test_executor_maps_attack_move_with_position() -> None:
    executor = IntentExecutor(dry_run=True)

    result = executor.execute(
        ActionIntent(type="attack_move", priority=8, position={"x": 64.0, "y": 65.0})
    )

    assert result.status == "executed"
    assert result.command["op"] == "attack_move"


def test_executor_rejects_unknown_intent() -> None:
    executor = IntentExecutor(dry_run=True)

    result = executor.execute(ActionIntent(type="unknown_action", priority=1))

    assert result.status == "unsupported"
