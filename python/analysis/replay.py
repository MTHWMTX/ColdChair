from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DecisionRecord:
    """Record of a decision made at a particular state."""

    state_index: int
    tick: int
    decision_type: str
    priority: int
    reasoning: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionRecord:
    """Record of an action execution."""

    state_index: int
    decision: DecisionRecord
    executed: bool
    reason_if_blocked: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class DecisionReplay:
    """Complete replay of decisions and executions for analysis."""

    replay_id: str
    description: str
    total_states: int
    decisions: list[DecisionRecord] = field(default_factory=list)
    executions: list[ExecutionRecord] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def add_decision(self, decision: DecisionRecord) -> None:
        self.decisions.append(decision)

    def add_execution(self, execution: ExecutionRecord) -> None:
        self.executions.append(execution)

    def add_error(self, error: str) -> None:
        self.errors.append(error)

    def get_decisions_by_type(self, decision_type: str) -> list[DecisionRecord]:
        return [d for d in self.decisions if d.decision_type == decision_type]

    def get_blocked_executions(self) -> list[ExecutionRecord]:
        return [e for e in self.executions if not e.executed]

    def get_block_rate(self) -> float:
        if not self.executions:
            return 0.0
        blocked = len(self.get_blocked_executions())
        return blocked / len(self.executions)

    def get_decision_success_rate(self, decision_type: str) -> float:
        """Success rate for a specific decision type."""
        execs = [e for e in self.executions if e.decision.decision_type == decision_type]
        if not execs:
            return 0.0
        executed = sum(1 for e in execs if e.executed)
        return executed / len(execs)

    def get_top_block_reasons(self, limit: int = 5) -> list[tuple[str, int]]:
        """Get most common reasons for blocking."""
        reason_counts: dict[str, int] = {}
        for execution in self.get_blocked_executions():
            reason = execution.reason_if_blocked or "unknown"
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

        return sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

    def to_dict(self) -> dict[str, Any]:
        return {
            "replay_id": self.replay_id,
            "description": self.description,
            "total_states": self.total_states,
            "total_decisions": len(self.decisions),
            "total_executions": len(self.executions),
            "block_rate": self.get_block_rate(),
            "top_block_reasons": self.get_top_block_reasons(),
            "error_count": len(self.errors),
            "decision_success_rates": {
                dt: self.get_decision_success_rate(dt)
                for dt in set(d.decision_type for d in self.decisions)
            },
        }
