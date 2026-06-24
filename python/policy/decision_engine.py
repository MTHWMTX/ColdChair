from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ActionIntent:
    type: str
    priority: int = 0
    target_id: str | None = None
    position: dict[str, float] | None = None


class DecisionEngine:
    """Baseline rule engine for early offline experiments."""

    def decide(self, game_state: dict[str, Any]) -> list[ActionIntent]:
        resources = game_state.get("resources", {})
        supply = game_state.get("supply", {})
        units = game_state.get("units", [])

        if not units:
            return [ActionIntent(type="idle", priority=0)]

        gold = int(resources.get("gold", 0))
        lumber = int(resources.get("lumber", 0))
        used = int(supply.get("used", 0))
        cap = int(supply.get("cap", 0))

        intents: list[ActionIntent] = []

        # Basic economic heuristic for early scaffolding.
        if gold >= 180 and lumber >= 40 and used < cap:
            intents.append(ActionIntent(type="train_unit", priority=10))

        # If we have enough units, request an attack-move intent.
        own_units = [u for u in units if u.get("owner") == "self"]
        if len(own_units) >= 8:
            intents.append(
                ActionIntent(
                    type="attack_move",
                    priority=8,
                    position={"x": 64.0, "y": 64.0},
                )
            )

        if not intents:
            intents.append(ActionIntent(type="gather_resources", priority=5))

        return sorted(intents, key=lambda i: i.priority, reverse=True)
