from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from python.config.pipeline_config import PipelineConfig, ExperimentConfig
from python.runtime.action_queue import ActionQueue, RuntimeSafetyConfig
from python.runtime.e2e_pipeline import E2EPipeline
from python.runtime.executor import IntentExecutor
from python.replay.sample_loader import load_state_samples


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run pipeline experiment with configuration")
    parser.add_argument("--config", required=True, help="Path to pipeline configuration JSON file")
    parser.add_argument("--samples", required=True, help="Path to JSON/JSONL game-state samples")
    parser.add_argument("--out", default="reports/experiment_result.json", help="Output path for experiment result")
    parser.add_argument("--compare-to", help="Path to baseline experiment result for comparison")
    return parser


def run_experiment(config: PipelineConfig, samples_path: str) -> dict:
    """Execute pipeline with given configuration."""
    try:
        samples = load_state_samples(samples_path)
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}

    queue = ActionQueue(
        RuntimeSafetyConfig(
            max_actions_per_second=config.max_actions_per_second,
            online_mode_enabled=config.online_mode_enabled,
        )
    )

    if not config.window_active_required:
        queue.set_active_window_ok(True)

    executor = IntentExecutor(dry_run=config.dry_run_enabled)
    pipeline = E2EPipeline(queue=queue, executor=executor)

    total_executed = 0
    total_blocked = 0
    total_states = 0

    for sample in samples:
        summary, logs, telemetry = pipeline.run_scenario(samples_path)
        if summary is not None:
            total_states += summary.total_states
            total_executed += summary.executed_actions
            total_blocked += summary.blocked_states

    executed_rate = total_executed / max(total_states, 1)

    gate_passed = (
        executed_rate >= config.min_executed_rate
        and total_executed >= 0
    )

    return {
        "status": "success",
        "config_name": config.name,
        "total_states": total_states,
        "total_executed": total_executed,
        "total_blocked": total_blocked,
        "executed_rate": executed_rate,
        "gate_passed": gate_passed,
        "gate_thresholds": {
            "min_executed_rate": config.min_executed_rate,
            "min_train_rate": config.min_train_rate,
            "min_gather_rate": config.min_gather_rate,
        },
    }


def compare_results(current: dict, baseline: dict) -> dict:
    """Compare experiment result against baseline."""
    if baseline.get("status") != "success" or current.get("status") != "success":
        return {"status": "incomplete", "reason": "missing baseline or current result"}

    current_rate = current.get("executed_rate", 0)
    baseline_rate = baseline.get("executed_rate", 0)
    drift = abs(current_rate - baseline_rate)

    return {
        "current_executed_rate": current_rate,
        "baseline_executed_rate": baseline_rate,
        "drift": drift,
        "improved": current_rate > baseline_rate,
        "regressed": current_rate < baseline_rate,
    }


def main() -> int:
    args = build_parser().parse_args()

    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Configuration not found: {config_path}")
        return 1

    config_data = json.loads(config_path.read_text(encoding="utf-8"))
    if isinstance(config_data, dict) and "configurations" in config_data:
        # It's an experiment file, use first config
        exp = ExperimentConfig.from_dict(config_data)
        config = exp.get_config(exp.list_configs()[0])
    else:
        config = PipelineConfig.from_dict(config_data)

    # Run experiment
    result = run_experiment(config, args.samples)

    # Compare if baseline provided
    if args.compare_to and result.get("status") == "success":
        baseline_path = Path(args.compare_to)
        if baseline_path.exists():
            baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
            result["comparison"] = compare_results(result, baseline)

    # Write output
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
