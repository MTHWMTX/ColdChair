from __future__ import annotations

import argparse
import json
from pathlib import Path

from python.replay.w3g_parser import W3GParser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract normalized state samples from replay input"
    )
    parser.add_argument("--replay", required=True, help="Path to replay source file")
    parser.add_argument(
        "--out",
        default="reports/replay_states.jsonl",
        help="Output path for normalized samples as JSONL",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    replay_path = Path(args.replay)

    parser = W3GParser()
    parsed = parser.parse(replay_path)
    samples = parser.to_game_state_samples(parsed)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [json.dumps(sample) for sample in samples]
    out_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"wrote {len(samples)} samples to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
