from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from python.replay.sample_loader import load_state_samples
from python.runtime.action_queue import ActionQueue, RuntimeSafetyConfig
from python.runtime.e2e_pipeline import E2EPipeline
from python.runtime.executor import IntentExecutor
from python.training.policy_manager import PolicyManager, TrainingLog, TrainingRun


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run training on replay data")
    parser.add_argument("--samples", required=True, help="Path to training samples")
    parser.add_argument("--version", required=True, help="Policy version to train")
    parser.add_argument("--description", help="Training run description")
    parser.add_argument("--output", default="reports/training_run.json", help="Output report path")
    parser.add_argument("--policies-dir", default="policies", help="Policies directory")
    parser.add_argument("--log-file", default="reports/training_log.json", help="Training log file")
    return parser


def run_training(
    samples_path: str,
    policy_version: str,
    policies_dir: str = "policies",
) -> dict[str, Any]:
    """Execute training on samples with given policy version."""
    try:
        samples = load_state_samples(samples_path)
    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
            "samples_loaded": 0,
        }

    # Load or create policy
    manager = PolicyManager(policies_dir)
    # Load all policies from disk
    from pathlib import Path

    policies_path = Path(policies_dir)
    if policies_path.exists():
        for policy_file in policies_path.glob("*.json"):
            manager.load_version(policy_file)

    policy = manager.get_version(policy_version)

    if policy is None:
        return {
            "status": "failed",
            "error": f"Policy version not found: {policy_version}",
        }

    # Run pipeline
    queue = ActionQueue(
        RuntimeSafetyConfig(
            max_actions_per_second=policy.params.get("max_actions_per_second", 1000000.0),
            online_mode_enabled=policy.params.get("online_mode_enabled", False),
        )
    )
    executor = IntentExecutor(dry_run=policy.params.get("dry_run_enabled", True))
    pipeline = E2EPipeline(queue=queue, executor=executor)

    total_executed = 0
    total_blocked = 0
    total_states = len(samples)

    for _ in samples:
        summary, logs, telemetry = pipeline.run_scenario(samples_path)
        if summary is not None:
            total_executed += summary.executed_actions
            total_blocked += summary.blocked_states

    execution_rate = total_executed / max(total_states, 1)

    return {
        "status": "success",
        "policy_version": policy_version,
        "samples_loaded": total_states,
        "executed_actions": total_executed,
        "blocked_actions": total_blocked,
        "execution_rate": execution_rate,
        "metrics": {
            "execution_rate": execution_rate,
            "blocked_rate": total_blocked / max(total_states, 1),
        },
    }


def main() -> int:
    args = build_parser().parse_args()

    # Run training
    result = run_training(args.samples, args.version, args.policies_dir)

    if result.get("status") != "success":
        print(json.dumps(result, indent=2))
        return 1

    # Record training run
    log = TrainingLog(args.log_file)
    log.load()

    run = TrainingRun(
        run_id=f"run_{datetime.now().isoformat()}",
        timestamp=datetime.now().isoformat(),
        policy_version=args.version,
        dataset_size=result["samples_loaded"],
        executed_actions=result["executed_actions"],
        blocked_actions=result["blocked_actions"],
        execution_rate=result["execution_rate"],
        metrics=result["metrics"],
        errors=[],
    )

    log.record_run(run)
    log.save()

    # Save training report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
