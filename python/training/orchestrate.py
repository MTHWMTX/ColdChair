from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime

from python.training.policy_manager import PolicyManager, TrainingLog
from python.training.dataset_manager import DatasetManager
from python.training.run_training import run_training


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Orchestrate training pipeline")
    subparsers = parser.add_subparsers(dest="command", help="Command")

    # init-policy command
    init_cmd = subparsers.add_parser("init-policy", help="Initialize a new policy version")
    init_cmd.add_argument("--version", required=True, help="Policy version ID")
    init_cmd.add_argument("--description", required=True, help="Policy description")
    init_cmd.add_argument("--params", default="{}", help="Policy params JSON")

    # register-dataset command
    dataset_cmd = subparsers.add_parser("register-dataset", help="Register training dataset")
    dataset_cmd.add_argument("--dataset-id", required=True, help="Dataset ID")
    dataset_cmd.add_argument("--name", required=True, help="Dataset name")
    dataset_cmd.add_argument("--description", help="Dataset description")
    dataset_cmd.add_argument("--samples", required=True, help="Samples file path")
    dataset_cmd.add_argument("--tags", default="", help="Comma-separated tags")

    # train command
    train_cmd = subparsers.add_parser("train", help="Run training")
    train_cmd.add_argument("--policy-version", required=True, help="Policy version to train")
    train_cmd.add_argument("--dataset-id", required=True, help="Dataset to train on")
    train_cmd.add_argument("--out", default="reports/training_result.json", help="Output path")

    # status command
    status_cmd = subparsers.add_parser("status", help="Show training status")
    status_cmd.add_argument("--policies-dir", default="policies", help="Policies directory")

    return parser


def main() -> int:
    args = build_parser().parse_args()

    # Use consistent directories across commands
    policies_dir = "policies"
    datasets_dir = "datasets"

    if args.command == "init-policy":
        manager = PolicyManager(policies_dir)
        params = json.loads(args.params)
        version = manager.create_policy_version(args.version, args.description, params)
        manager.save_version(args.version, Path(policies_dir) / f"{args.version}.json")
        print(json.dumps(version.to_dict(), indent=2))
        return 0

    elif args.command == "register-dataset":
        manager = DatasetManager(datasets_dir)
        tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
        metadata = manager.register_dataset(
            args.dataset_id,
            args.name,
            args.description or "",
            args.samples,
            tags=tags,
        )
        print(json.dumps(metadata.to_dict(), indent=2))
        return 0

    elif args.command == "train":
        # Load datasets
        manager_datasets = DatasetManager(datasets_dir)
        manager_datasets._load_metadata()
        dataset = manager_datasets.get_dataset(args.dataset_id)
        if not dataset:
            print(f"Dataset not found: {args.dataset_id}")
            return 1

        dataset_path = manager_datasets.get_dataset_path(args.dataset_id)
        result = run_training(str(dataset_path), args.policy_version, policies_dir)

        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

        print(json.dumps(result, indent=2))
        return 0 if result.get("status") == "success" else 1

    elif args.command == "status":
        manager = PolicyManager(args.policies_dir or policies_dir)
        # Load all versions from disk
        policies_path = Path(manager.policies_dir)
        if policies_path.exists():
            for policy_file in policies_path.glob("v*.json"):
                manager.load_version(policy_file)

        versions = manager.list_versions()
        best = manager.get_best_version()

        status = {
            "total_versions": len(versions),
            "best_version": best.version_id if best else None,
            "best_accuracy": best.test_accuracy if best else 0.0,
            "versions": [v.to_dict() for v in versions[:5]],
        }

        print(json.dumps(status, indent=2))
        return 0

    else:
        print("No command specified")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
