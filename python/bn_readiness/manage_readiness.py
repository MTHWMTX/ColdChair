from __future__ import annotations

import argparse
import json
from pathlib import Path

from python.bn_readiness.readiness import BattleNetReadiness


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Battle.net readiness checklist")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # status command
    subparsers.add_parser("status", help="Show readiness status")

    # mark-ready command
    mark_cmd = subparsers.add_parser("mark-ready", help="Mark a check as ready")
    mark_cmd.add_argument("--phase", required=True, help="Phase key")
    mark_cmd.add_argument("--check", required=True, help="Check name")
    mark_cmd.add_argument("--completed-by", default="", help="Completed by")
    mark_cmd.add_argument("--notes", default="", help="Notes")

    # export command
    export_cmd = subparsers.add_parser("export", help="Export readiness status")
    export_cmd.add_argument("--out", default="reports/bn_readiness.json", help="Output path")

    return parser


def main() -> int:
    args = build_parser().parse_args()

    readiness = BattleNetReadiness()

    if args.command == "status":
        progress = readiness.overall_progress()
        print(json.dumps(progress, indent=2))
        return 0

    elif args.command == "mark-ready":
        phase = readiness.get_phase(args.phase)
        if phase is None:
            print(f"Phase not found: {args.phase}")
            return 1

        phase.mark_complete(args.check, args.completed_by, args.notes)
        print(json.dumps(readiness.to_dict(), indent=2))
        return 0

    elif args.command == "export":
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(readiness.to_dict(), indent=2), encoding="utf-8")
        print(f"Readiness exported to {out_path}")
        return 0

    else:
        print("No command specified")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
