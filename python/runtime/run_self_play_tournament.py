from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from python.replay.sample_loader import load_state_samples
from python.runtime.self_play_tournament import SelfPlayTournament


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run ranked self-play tournament")
    parser.add_argument("--samples", help="Optional JSON/JSONL sample states")
    parser.add_argument("--rounds", type=int, default=20, help="Number of rounds (2 games each)")
    parser.add_argument("--ticks", type=int, default=80, help="Ticks per game")
    parser.add_argument("--bot-a-label", default="bot_a", help="Label for bot A")
    parser.add_argument("--bot-b-label", default="bot_b", help="Label for bot B")
    parser.add_argument(
        "--out",
        default="reports/self_play_tournament_report.json",
        help="Output report path",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    states = load_state_samples(args.samples) if args.samples else None
    tournament = SelfPlayTournament(bot_a_label=args.bot_a_label, bot_b_label=args.bot_b_label)
    summary, matches = tournament.run(rounds=args.rounds, ticks=args.ticks, initial_states=states)

    payload = {
        "summary": asdict(summary),
        "matches": matches,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
