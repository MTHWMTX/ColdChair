from __future__ import annotations

import argparse
import json
from pathlib import Path

from python.runtime.run_scenarios import main as _run_scenarios_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a scenario baseline report from current scenario pack"
    )
    parser.add_argument(
        "--scenario-dir",
        default="scenarios/local_ai",
        help="Directory containing scenario files",
    )
    parser.add_argument(
        "--out",
        default="scenarios/local_ai/baseline_report.json",
        help="Output path for the baseline report",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    # Reuse run_scenarios pipeline without baseline comparison.
    import sys

    old_argv = sys.argv
    try:
        sys.argv = [
            "run_scenarios.py",
            "--scenario-dir",
            args.scenario_dir,
            "--out",
            args.out,
        ]
        code = _run_scenarios_main()
    finally:
        sys.argv = old_argv

    if code != 0:
        return code

    out_path = Path(args.out)
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    payload["baseline_compared"] = False
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"baseline written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
