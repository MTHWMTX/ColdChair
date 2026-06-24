from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from python.replay.import_replays_cli import parse_replay


def _group_name_for_file(replays_dir: Path, replay_file: Path) -> str:
    rel_parent = replay_file.parent.relative_to(replays_dir)
    if not rel_parent.parts:
        return "ungrouped"
    return str(rel_parent.parts[0])


def build_balanced_dataset(
    replays_dir: str | Path,
    out_file: str | Path,
    *,
    max_states_per_group: int = 0,
    verbose: bool = True,
) -> dict[str, Any]:
    root = Path(replays_dir)
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")

    replay_files = sorted(list(root.glob("**/*.w3g")) + list(root.glob("**/*.json")))
    replay_files = [p for p in replay_files if p.is_file()]

    grouped_states: dict[str, list[dict[str, Any]]] = {}
    file_counts: dict[str, int] = {}

    for replay_file in replay_files:
        group = _group_name_for_file(root, replay_file)
        samples = parse_replay(replay_file, verbose=verbose)
        if not samples:
            continue

        if group not in grouped_states:
            grouped_states[group] = []
            file_counts[group] = 0

        grouped_states[group].extend(samples)
        file_counts[group] += 1

    if not grouped_states:
        return {
            "total_states": 0,
            "total_groups": 0,
            "groups": {},
            "out_file": str(out_file),
        }

    balanced: list[dict[str, Any]] = []
    group_summary: dict[str, Any] = {}

    for group, states in sorted(grouped_states.items()):
        selected = states
        if max_states_per_group > 0:
            selected = states[:max_states_per_group]

        balanced.extend(selected)
        group_summary[group] = {
            "files": file_counts[group],
            "states_before_cap": len(states),
            "states_after_cap": len(selected),
        }

    out_path = Path(out_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(balanced, indent=2), encoding="utf-8")

    summary = {
        "total_states": len(balanced),
        "total_groups": len(group_summary),
        "groups": group_summary,
        "max_states_per_group": max_states_per_group,
        "out_file": str(out_path),
    }

    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build race/matchup-balanced replay dataset")
    parser.add_argument("--replays-dir", default="replays/incoming", help="Replay root directory")
    parser.add_argument("--out", default="datasets/replays_balanced.json", help="Output JSON dataset")
    parser.add_argument(
        "--max-states-per-group",
        type=int,
        default=0,
        help="Cap states per top-level group folder (0 = no cap)",
    )
    parser.add_argument("--manifest", default="", help="Optional path for summary manifest JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = build_balanced_dataset(
        replays_dir=args.replays_dir,
        out_file=args.out,
        max_states_per_group=args.max_states_per_group,
        verbose=True,
    )

    if args.manifest:
        manifest_path = Path(args.manifest)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return 0 if summary["total_states"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
