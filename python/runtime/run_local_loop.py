from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from python.replay.sample_loader import load_state_samples
from python.runtime.action_queue import ActionQueue, RuntimeSafetyConfig
from python.runtime.executor import IntentExecutor
from python.runtime.local_loop import LocalLoopRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run supervised local decision-to-action loop over state samples"
    )
    parser.add_argument("--samples", required=True, help="Path to JSON/JSONL game-state samples")
    parser.add_argument(
        "--out",
        default="reports/local_loop_report.json",
        help="Output path for local loop report",
    )
    parser.add_argument(
        "--max-actions-per-second",
        type=float,
        default=1000000.0,
        help="Action throttle limit used by runtime queue",
    )
    parser.add_argument(
        "--online-mode",
        action="store_true",
        help="Enable online-only actions in queue safeguards",
    )
    parser.add_argument(
        "--window-inactive",
        action="store_true",
        help="Simulate inactive game window, causing queue blocks",
    )
    parser.add_argument(
        "--live-execution",
        action="store_true",
        help="Disable dry-run mode in executor telemetry",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    samples = load_state_samples(args.samples)
    queue = ActionQueue(
        RuntimeSafetyConfig(
            max_actions_per_second=args.max_actions_per_second,
            online_mode_enabled=args.online_mode,
        )
    )
    queue.set_active_window_ok(not args.window_inactive)
    executor = IntentExecutor(dry_run=not args.live_execution)

    runner = LocalLoopRunner(queue=queue, executor=executor)
    summary, logs = runner.run_states(samples)

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
