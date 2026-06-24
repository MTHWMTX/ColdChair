from __future__ import annotations

from pathlib import Path

import pytest

from python.analysis.replay import DecisionRecord, ExecutionRecord, DecisionReplay


def test_decision_record() -> None:
    decision = DecisionRecord(
        state_index=0,
        tick=5,
        decision_type="train_unit",
        priority=10,
        reasoning="Gold available for training",
    )

    assert decision.state_index == 0
    assert decision.decision_type == "train_unit"
    assert decision.priority == 10


def test_execution_record() -> None:
    decision = DecisionRecord(state_index=0, tick=5, decision_type="gather", priority=5, reasoning="Test")
    execution = ExecutionRecord(state_index=0, decision=decision, executed=True)

    assert execution.executed
    assert execution.decision.decision_type == "gather"


def test_decision_replay_add_records() -> None:
    replay = DecisionReplay(replay_id="test1", description="Test replay", total_states=5)

    decision = DecisionRecord(state_index=0, tick=0, decision_type="train_unit", priority=10, reasoning="Test")
    execution = ExecutionRecord(state_index=0, decision=decision, executed=True)

    replay.add_decision(decision)
    replay.add_execution(execution)

    assert len(replay.decisions) == 1
    assert len(replay.executions) == 1


def test_get_decisions_by_type() -> None:
    replay = DecisionReplay(replay_id="test1", description="Test", total_states=3)

    replay.add_decision(DecisionRecord(0, 0, "train_unit", 10, ""))
    replay.add_decision(DecisionRecord(1, 1, "gather", 5, ""))
    replay.add_decision(DecisionRecord(2, 2, "train_unit", 10, ""))

    train_decisions = replay.get_decisions_by_type("train_unit")
    assert len(train_decisions) == 2


def test_get_blocked_executions() -> None:
    replay = DecisionReplay(replay_id="test1", description="Test", total_states=3)

    d1 = DecisionRecord(0, 0, "train_unit", 10, "")
    d2 = DecisionRecord(1, 1, "gather", 5, "")

    replay.add_execution(ExecutionRecord(0, d1, executed=True))
    replay.add_execution(ExecutionRecord(1, d2, executed=False, reason_if_blocked="Window inactive"))

    blocked = replay.get_blocked_executions()
    assert len(blocked) == 1
    assert blocked[0].reason_if_blocked == "Window inactive"


def test_get_block_rate() -> None:
    replay = DecisionReplay(replay_id="test1", description="Test", total_states=4)

    d = DecisionRecord(0, 0, "train_unit", 10, "")
    replay.add_execution(ExecutionRecord(0, d, executed=True))
    replay.add_execution(ExecutionRecord(1, d, executed=True))
    replay.add_execution(ExecutionRecord(2, d, executed=False, reason_if_blocked="Rate limited"))
    replay.add_execution(ExecutionRecord(3, d, executed=False, reason_if_blocked="Rate limited"))

    assert replay.get_block_rate() == 0.5


def test_get_top_block_reasons() -> None:
    replay = DecisionReplay(replay_id="test1", description="Test", total_states=5)

    d = DecisionRecord(0, 0, "train_unit", 10, "")
    replay.add_execution(ExecutionRecord(0, d, executed=False, reason_if_blocked="Rate limited"))
    replay.add_execution(ExecutionRecord(1, d, executed=False, reason_if_blocked="Rate limited"))
    replay.add_execution(ExecutionRecord(2, d, executed=False, reason_if_blocked="Window inactive"))

    reasons = replay.get_top_block_reasons()
    assert reasons[0] == ("Rate limited", 2)
    assert reasons[1] == ("Window inactive", 1)


def test_replay_to_dict() -> None:
    replay = DecisionReplay(replay_id="test1", description="Test replay", total_states=2)

    d1 = DecisionRecord(0, 0, "train_unit", 10, "")
    d2 = DecisionRecord(1, 1, "gather", 5, "")

    replay.add_decision(d1)
    replay.add_decision(d2)
    replay.add_execution(ExecutionRecord(0, d1, executed=True))
    replay.add_execution(ExecutionRecord(1, d2, executed=True))

    replay_dict = replay.to_dict()
    assert replay_dict["replay_id"] == "test1"
    assert replay_dict["total_decisions"] == 2
    assert replay_dict["total_executions"] == 2
    assert "decision_success_rates" in replay_dict
