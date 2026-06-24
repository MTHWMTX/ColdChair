from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from python.policy.decision_engine import ActionIntent, DecisionEngine
from python.runtime.executor import IntentExecutor


@dataclass
class SelfPlaySummary:
    ticks: int
    bot_a_units: int
    bot_b_units: int
    bot_a_score: float
    bot_b_score: float
    winner: str


class SelfPlayArena:
    """Deterministic offline self-play arena for bot-vs-bot simulation."""

    def __init__(
        self,
        *,
        engine_a: DecisionEngine | None = None,
        engine_b: DecisionEngine | None = None,
        executor_a: IntentExecutor | None = None,
        executor_b: IntentExecutor | None = None,
    ) -> None:
        self.engine_a = engine_a or DecisionEngine()
        self.engine_b = engine_b or DecisionEngine()
        self.executor_a = executor_a or IntentExecutor(dry_run=True)
        self.executor_b = executor_b or IntentExecutor(dry_run=True)
        self._next_unit_id = 1000

    def run(
        self,
        *,
        ticks: int,
        initial_state: dict[str, Any] | None = None,
    ) -> tuple[SelfPlaySummary, list[dict[str, Any]]]:
        shared = self._normalize_shared_state(initial_state)
        logs: list[dict[str, Any]] = []

        for tick in range(1, ticks + 1):
            shared["tick"] = tick

            state_a = self._to_engine_state(shared, "bot_a", "bot_b")
            state_b = self._to_engine_state(shared, "bot_b", "bot_a")

            intents_a = self.engine_a.decide(state_a)
            intents_b = self.engine_b.decide(state_b)
            intent_a = self._pick_intent(intents_a)
            intent_b = self._pick_intent(intents_b)

            execution_a = self.executor_a.execute(intent_a, state=state_a)
            execution_b = self.executor_b.execute(intent_b, state=state_b)

            self._apply_intent(shared, actor="bot_a", enemy="bot_b", intent=intent_a)
            self._apply_intent(shared, actor="bot_b", enemy="bot_a", intent=intent_b)

            logs.append(
                {
                    "tick": tick,
                    "bot_a": {
                        "intent": intent_a.type,
                        "status": execution_a.status,
                        "command": execution_a.command,
                    },
                    "bot_b": {
                        "intent": intent_b.type,
                        "status": execution_b.status,
                        "command": execution_b.command,
                    },
                    "state": {
                        "bot_a_units": len(shared["players"]["bot_a"]["units"]),
                        "bot_b_units": len(shared["players"]["bot_b"]["units"]),
                        "bot_a_gold": int(shared["players"]["bot_a"]["resources"]["gold"]),
                        "bot_b_gold": int(shared["players"]["bot_b"]["resources"]["gold"]),
                    },
                }
            )

            winner = self._winner_if_terminal(shared)
            if winner != "ongoing":
                summary = self._build_summary(shared, tick, winner)
                return summary, logs

        summary = self._build_summary(shared, ticks, self._winner_if_terminal(shared))
        return summary, logs

    def _normalize_shared_state(self, initial_state: dict[str, Any] | None) -> dict[str, Any]:
        if initial_state is None:
            return self._default_shared_state()

        if isinstance(initial_state.get("players"), dict):
            return initial_state

        # Accept standard game-state sample format and split units by owner.
        state = {
            "tick": int(initial_state.get("tick", 0)),
            "players": {
                "bot_a": {
                    "resources": dict(initial_state.get("resources", {"gold": 325, "lumber": 80})),
                    "supply": dict(initial_state.get("supply", {"used": 4, "cap": 12})),
                    "units": [],
                },
                "bot_b": {
                    "resources": dict(initial_state.get("resources", {"gold": 325, "lumber": 80})),
                    "supply": dict(initial_state.get("supply", {"used": 4, "cap": 12})),
                    "units": [],
                },
            },
        }

        for idx, unit in enumerate(initial_state.get("units", [])):
            if not isinstance(unit, dict):
                continue
            owner = str(unit.get("owner", "neutral"))
            target = "bot_a" if owner == "self" else "bot_b" if owner == "enemy" else ("bot_a" if idx % 2 == 0 else "bot_b")
            state["players"][target]["units"].append(
                {
                    "id": str(unit.get("id", f"u{idx}")),
                    "type": str(unit.get("type", "footman")),
                    "hp": float(unit.get("hp", 100.0)),
                    "position": dict(unit.get("position", {"x": 10.0, "y": 10.0})),
                }
            )

        if not state["players"]["bot_a"]["units"]:
            state["players"]["bot_a"]["units"].append(
                {"id": "a_seed", "type": "footman", "hp": 420.0, "position": {"x": 20.0, "y": 20.0}}
            )
        if not state["players"]["bot_b"]["units"]:
            state["players"]["bot_b"]["units"].append(
                {"id": "b_seed", "type": "footman", "hp": 420.0, "position": {"x": 100.0, "y": 100.0}}
            )

        return state

    @staticmethod
    def _pick_intent(intents: list[ActionIntent]) -> ActionIntent:
        if not intents:
            return ActionIntent(type="idle", priority=0)
        return sorted(intents, key=lambda i: i.priority, reverse=True)[0]

    def _apply_intent(self, shared: dict[str, Any], *, actor: str, enemy: str, intent: ActionIntent) -> None:
        actor_state = shared["players"][actor]
        enemy_state = shared["players"][enemy]

        if intent.type == "train_unit":
            resources = actor_state["resources"]
            supply = actor_state["supply"]
            if (
                int(resources.get("gold", 0)) >= 180
                and int(resources.get("lumber", 0)) >= 40
                and int(supply.get("used", 0)) < int(supply.get("cap", 0))
            ):
                resources["gold"] = int(resources.get("gold", 0)) - 180
                resources["lumber"] = int(resources.get("lumber", 0)) - 40
                supply["used"] = int(supply.get("used", 0)) + 1
                actor_state["units"].append(
                    {
                        "id": f"u{self._next_unit_id}",
                        "type": "footman",
                        "hp": 420.0,
                        "position": {"x": 12.0, "y": 12.0},
                    }
                )
                self._next_unit_id += 1
            return

        if intent.type == "gather_resources":
            actor_state["resources"]["gold"] = int(actor_state["resources"].get("gold", 0)) + 35
            actor_state["resources"]["lumber"] = int(actor_state["resources"].get("lumber", 0)) + 15
            return

        if intent.type == "attack_move":
            enemy_units = enemy_state["units"]
            if enemy_units:
                enemy_units[0]["hp"] = float(enemy_units[0].get("hp", 0.0)) - 65.0
                self._prune_dead_units(enemy_state)
            return

    @staticmethod
    def _prune_dead_units(player_state: dict[str, Any]) -> None:
        alive = [u for u in player_state["units"] if float(u.get("hp", 0.0)) > 0.0]
        before = len(player_state["units"])
        player_state["units"] = alive
        removed = before - len(alive)
        if removed > 0:
            player_state["supply"]["used"] = max(0, int(player_state["supply"].get("used", 0)) - removed)

    @staticmethod
    def _to_engine_state(shared: dict[str, Any], actor: str, enemy: str) -> dict[str, Any]:
        actor_state = shared["players"][actor]
        enemy_state = shared["players"][enemy]

        units: list[dict[str, Any]] = []
        for unit in actor_state["units"]:
            units.append(
                {
                    "id": unit["id"],
                    "owner": "self",
                    "type": unit["type"],
                    "hp": unit["hp"],
                    "position": unit.get("position", {"x": 0.0, "y": 0.0}),
                }
            )

        for unit in enemy_state["units"]:
            units.append(
                {
                    "id": unit["id"],
                    "owner": "enemy",
                    "type": unit["type"],
                    "hp": unit["hp"],
                    "position": unit.get("position", {"x": 0.0, "y": 0.0}),
                }
            )

        return {
            "tick": int(shared.get("tick", 0)),
            "resources": {
                "gold": int(actor_state["resources"].get("gold", 0)),
                "lumber": int(actor_state["resources"].get("lumber", 0)),
            },
            "supply": {
                "used": int(actor_state["supply"].get("used", 0)),
                "cap": int(actor_state["supply"].get("cap", 0)),
            },
            "units": units,
        }

    @staticmethod
    def _winner_if_terminal(shared: dict[str, Any]) -> str:
        a_units = len(shared["players"]["bot_a"]["units"])
        b_units = len(shared["players"]["bot_b"]["units"])

        if a_units == 0 and b_units == 0:
            return "draw"
        if a_units == 0:
            return "bot_b"
        if b_units == 0:
            return "bot_a"
        return "ongoing"

    def _build_summary(self, shared: dict[str, Any], ticks: int, terminal_winner: str) -> SelfPlaySummary:
        score_a = self._score_player(shared["players"]["bot_a"])
        score_b = self._score_player(shared["players"]["bot_b"])

        winner = terminal_winner
        if winner == "ongoing":
            if score_a > score_b:
                winner = "bot_a"
            elif score_b > score_a:
                winner = "bot_b"
            else:
                winner = "draw"

        return SelfPlaySummary(
            ticks=ticks,
            bot_a_units=len(shared["players"]["bot_a"]["units"]),
            bot_b_units=len(shared["players"]["bot_b"]["units"]),
            bot_a_score=score_a,
            bot_b_score=score_b,
            winner=winner,
        )

    @staticmethod
    def _score_player(player_state: dict[str, Any]) -> float:
        units = player_state["units"]
        unit_hp_sum = sum(float(u.get("hp", 0.0)) for u in units)
        gold = float(player_state["resources"].get("gold", 0))
        lumber = float(player_state["resources"].get("lumber", 0))
        return len(units) * 100.0 + unit_hp_sum * 0.25 + gold * 0.5 + lumber * 0.3

    @staticmethod
    def _default_shared_state() -> dict[str, Any]:
        def base_units(prefix: str) -> list[dict[str, Any]]:
            return [
                {
                    "id": f"{prefix}_p{i}",
                    "type": "peasant",
                    "hp": 230.0,
                    "position": {"x": 10.0 + i, "y": 10.0 + i},
                }
                for i in range(4)
            ]

        return {
            "tick": 0,
            "players": {
                "bot_a": {
                    "resources": {"gold": 325, "lumber": 80},
                    "supply": {"used": 4, "cap": 12},
                    "units": base_units("a"),
                },
                "bot_b": {
                    "resources": {"gold": 325, "lumber": 80},
                    "supply": {"used": 4, "cap": 12},
                    "units": base_units("b"),
                },
            },
        }
