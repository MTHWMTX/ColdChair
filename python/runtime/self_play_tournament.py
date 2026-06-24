from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from python.runtime.self_play import SelfPlayArena, SelfPlaySummary


@dataclass
class TournamentSummary:
    rounds: int
    total_games: int
    bot_a_label: str
    bot_b_label: str
    bot_a_wins: int
    bot_b_wins: int
    draws: int
    bot_a_elo: float
    bot_b_elo: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SelfPlayTournament:
    """Runs repeated self-play matches with side-swapping and Elo tracking."""

    def __init__(self, *, bot_a_label: str = "bot_a", bot_b_label: str = "bot_b") -> None:
        self.bot_a_label = bot_a_label
        self.bot_b_label = bot_b_label

    def run(
        self,
        *,
        rounds: int,
        ticks: int,
        initial_states: list[dict[str, Any]] | None = None,
    ) -> tuple[TournamentSummary, list[dict[str, Any]]]:
        states = initial_states or [None]
        matches: list[dict[str, Any]] = []

        rating_a = 1000.0
        rating_b = 1000.0
        wins_a = 0
        wins_b = 0
        draws = 0

        for round_index in range(rounds):
            seed_state = states[round_index % len(states)]

            # Game 1: A on bot_a side, B on bot_b side.
            summary_1 = self._run_match(seed_state=seed_state, ticks=ticks)
            mapped_1 = self._map_winner(summary_1.winner, a_on_bot_a_side=True)
            rating_a, rating_b = self._update_elo(rating_a, rating_b, mapped_1)
            wins_a, wins_b, draws = self._update_counts(
                mapped_1,
                self.bot_a_label,
                self.bot_b_label,
                wins_a,
                wins_b,
                draws,
            )
            matches.append(
                {
                    "round": round_index + 1,
                    "game": 1,
                    "sides": {"bot_a": self.bot_a_label, "bot_b": self.bot_b_label},
                    "winner": mapped_1,
                    "raw_winner": summary_1.winner,
                    "summary": asdict(summary_1),
                    "ratings": {self.bot_a_label: rating_a, self.bot_b_label: rating_b},
                }
            )

            # Game 2: side swap for fairness.
            swapped = self._swap_state(seed_state)
            summary_2 = self._run_match(seed_state=swapped, ticks=ticks)
            mapped_2 = self._map_winner(summary_2.winner, a_on_bot_a_side=False)
            rating_a, rating_b = self._update_elo(rating_a, rating_b, mapped_2)
            wins_a, wins_b, draws = self._update_counts(
                mapped_2,
                self.bot_a_label,
                self.bot_b_label,
                wins_a,
                wins_b,
                draws,
            )
            matches.append(
                {
                    "round": round_index + 1,
                    "game": 2,
                    "sides": {"bot_a": self.bot_b_label, "bot_b": self.bot_a_label},
                    "winner": mapped_2,
                    "raw_winner": summary_2.winner,
                    "summary": asdict(summary_2),
                    "ratings": {self.bot_a_label: rating_a, self.bot_b_label: rating_b},
                }
            )

        summary = TournamentSummary(
            rounds=rounds,
            total_games=rounds * 2,
            bot_a_label=self.bot_a_label,
            bot_b_label=self.bot_b_label,
            bot_a_wins=wins_a,
            bot_b_wins=wins_b,
            draws=draws,
            bot_a_elo=rating_a,
            bot_b_elo=rating_b,
        )
        return summary, matches

    @staticmethod
    def _run_match(seed_state: dict[str, Any] | None, ticks: int) -> SelfPlaySummary:
        arena = SelfPlayArena()
        summary, _ = arena.run(ticks=ticks, initial_state=seed_state)
        return summary

    def _map_winner(self, winner: str, *, a_on_bot_a_side: bool) -> str:
        if winner == "draw":
            return "draw"

        if a_on_bot_a_side:
            return self.bot_a_label if winner == "bot_a" else self.bot_b_label

        # Sides are swapped in game 2.
        return self.bot_a_label if winner == "bot_b" else self.bot_b_label

    @staticmethod
    def _update_counts(
        mapped_winner: str,
        bot_a_label: str,
        bot_b_label: str,
        wins_a: int,
        wins_b: int,
        draws: int,
    ) -> tuple[int, int, int]:
        if mapped_winner == "draw":
            return wins_a, wins_b, draws + 1
        if mapped_winner == bot_a_label:
            return wins_a + 1, wins_b, draws
        if mapped_winner == bot_b_label:
            return wins_a, wins_b + 1, draws
        return wins_a, wins_b, draws

    def _update_elo(self, rating_a: float, rating_b: float, mapped_winner: str) -> tuple[float, float]:
        score_a, score_b = self._scores_from_winner(mapped_winner)
        expected_a = 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))
        expected_b = 1.0 - expected_a
        k = 16.0
        new_a = rating_a + k * (score_a - expected_a)
        new_b = rating_b + k * (score_b - expected_b)
        return new_a, new_b

    def _scores_from_winner(self, mapped_winner: str) -> tuple[float, float]:
        if mapped_winner == "draw":
            return 0.5, 0.5
        if mapped_winner == self.bot_a_label:
            return 1.0, 0.0
        if mapped_winner == self.bot_b_label:
            return 0.0, 1.0
        return 0.5, 0.5

    @staticmethod
    def _swap_state(state: dict[str, Any] | None) -> dict[str, Any] | None:
        if state is None:
            return None

        if isinstance(state.get("players"), dict):
            players = state["players"]
            bot_a = players.get("bot_a", {})
            bot_b = players.get("bot_b", {})
            return {
                **state,
                "players": {
                    "bot_a": bot_b,
                    "bot_b": bot_a,
                },
            }

        # Standard sample-state format: swap self/enemy ownership tags.
        swapped = {
            **state,
            "units": [],
        }
        for unit in state.get("units", []):
            if not isinstance(unit, dict):
                continue
            owner = unit.get("owner")
            new_owner = "enemy" if owner == "self" else "self" if owner == "enemy" else owner
            swapped["units"].append({**unit, "owner": new_owner})
        return swapped
