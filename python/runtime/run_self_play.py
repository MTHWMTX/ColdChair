from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from python.replay.sample_loader import load_state_samples
from python.runtime.self_play import SelfPlayArena


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run offline bot-vs-bot self-play simulation")
    parser.add_argument("--ticks", type=int, default=60, help="Maximum ticks to simulate")
    parser.add_argument(
        "--samples",
        help="Optional JSON/JSONL sample states path (first sample is used as seed)",
    )
    parser.add_argument(
        "--initial-state",
        help="Optional JSON file with shared self-play state; if it is an array, first element is used",
    )
    parser.add_argument(
        "--out",
        default="reports/self_play_report.json",
        help="Output report path",
    )
    return parser


def _load_initial_state(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(payload, list):
        if not payload:
            raise ValueError("Initial-state array is empty")
        first = payload[0]
        if not isinstance(first, dict):
            raise ValueError("Initial-state array first item must be an object")
        return first

    if not isinstance(payload, dict):
        raise ValueError("Initial-state payload must be an object or array")

    return payload


def main() -> int:
    args = build_parser().parse_args()

    initial_state: dict[str, Any] | None = None
    if args.samples:
        samples = load_state_samples(args.samples)
        if not samples:
            raise ValueError("No sample states found in --samples file")
        initial_state = samples[0]
    elif args.initial_state:
        initial_state = _load_initial_state(args.initial_state)

    arena = SelfPlayArena()
    summary, logs = arena.run(ticks=args.ticks, initial_state=initial_state)

    payload = {
        "summary": asdict(summary),
        "logs": logs,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
