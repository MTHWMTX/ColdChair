from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from python.policy.decision_engine import ActionIntent, DecisionEngine


@dataclass
class EvaluationSummary:
    total_states: int
    train_unit_rate: float
    attack_move_rate: float
    gather_rate: float


class OfflinePolicyEvaluator:
    """Scores how often core intents are emitted over state samples."""

    def __init__(self, engine: DecisionEngine | None = None) -> None:
        self.engine = engine or DecisionEngine()

    def evaluate(self, states: list[dict]) -> EvaluationSummary:
        if not states:
            return EvaluationSummary(
                total_states=0,
                train_unit_rate=0.0,
                attack_move_rate=0.0,
                gather_rate=0.0,
            )

        intents_per_state: list[list[ActionIntent]] = [self.engine.decide(state) for state in states]

        def has_intent(intent_type: str, actions: list[ActionIntent]) -> float:
            return 1.0 if any(action.type == intent_type for action in actions) else 0.0

        train_rates = [has_intent("train_unit", actions) for actions in intents_per_state]
        attack_rates = [has_intent("attack_move", actions) for actions in intents_per_state]
        gather_rates = [has_intent("gather_resources", actions) for actions in intents_per_state]

        return EvaluationSummary(
            total_states=len(states),
            train_unit_rate=mean(train_rates),
            attack_move_rate=mean(attack_rates),
            gather_rate=mean(gather_rates),
        )
