#!/usr/bin/env python
"""One-command replay import + dataset registration + training orchestration."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# Support direct invocation: python scripts/import_and_train_replays.py
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from python.replay.import_replays_cli import import_replays_from_directory
from python.replay.build_balanced_dataset import build_balanced_dataset
from python.training.dataset_manager import DatasetManager
from python.training.policy_manager import PolicyManager
from python.training.run_training import run_training


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Import replay folder, register dataset, and run training"
    )
    parser.add_argument("--replays-dir", default="replays/incoming", help="Replay drop folder")
    parser.add_argument("--datasets-dir", default="datasets", help="Datasets directory")
    parser.add_argument("--policies-dir", default="policies", help="Policies directory")
    parser.add_argument("--reports-dir", default="reports", help="Reports directory")

    parser.add_argument("--dataset-id", default="replays_dataset", help="Dataset ID for imported replays")
    parser.add_argument(
        "--balance-dataset",
        action="store_true",
        help="Build balanced dataset before registration/training",
    )
    parser.add_argument(
        "--group-mode",
        choices=["subfolder", "map", "subfolder_map"],
        default="subfolder",
        help="Grouping strategy used when balancing dataset",
    )
    parser.add_argument(
        "--max-states-per-group",
        type=int,
        default=0,
        help="Cap states per group when balancing by subfolder (0 = no cap)",
    )

    parser.add_argument("--policy-version", default="v1.0", help="Policy version to train")
    parser.add_argument(
        "--policy-description",
        default="Auto-created baseline policy for replay import workflow",
        help="Description used if policy version must be created",
    )
    parser.add_argument("--policy-params", default="{}", help="JSON params for auto-created policy")
    parser.add_argument(
        "--no-auto-init-policy",
        action="store_true",
        help="Do not create policy if missing",
    )
    parser.add_argument(
        "--skip-training",
        action="store_true",
        help="Import/register only, do not run training",
    )
    parser.add_argument(
        "--train-dataset-id",
        default="",
        help="Dataset ID to train on (default: --dataset-id)",
    )
    return parser


def _load_json_array(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Expected JSON array in {path}")
    return [item for item in payload if isinstance(item, dict)]


def _register_dataset(
    manager: DatasetManager,
    dataset_id: str,
    name: str,
    description: str,
    sample_path: Path,
    tags: list[str],
) -> int:
    metadata = manager.register_dataset(
        dataset_id=dataset_id,
        name=name,
        description=description,
        sample_path=sample_path,
        tags=tags,
    )
    print(f"✓ Registered dataset {dataset_id} ({metadata.sample_count} samples)")
    return metadata.sample_count


def _ensure_policy(
    manager: PolicyManager,
    version_id: str,
    description: str,
    params_json: str,
    auto_init: bool,
) -> bool:
    policies_path = Path(manager.policies_dir)
    for policy_file in policies_path.glob("*.json"):
        manager.load_version(policy_file)

    existing = manager.get_version(version_id)
    if existing is not None:
        print(f"✓ Using existing policy version {version_id}")
        return True

    if not auto_init:
        print(f"Policy version not found and auto-init disabled: {version_id}")
        return False

    params = json.loads(params_json)
    manager.create_policy_version(version_id, description, params)
    manager.save_version(version_id, policies_path / f"{version_id}.json")
    print(f"✓ Created policy version {version_id}")
    return True


def main() -> int:
    args = build_parser().parse_args()

    replays_dir = args.replays_dir

    datasets_dir = Path(args.datasets_dir)
    datasets_dir.mkdir(parents=True, exist_ok=True)
    reports_dir = Path(args.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    dataset_manager = DatasetManager(datasets_dir)
    dataset_manager._load_metadata()

    replay_dir = Path(replays_dir)
    output_file = datasets_dir / "replays_extracted.json"

    print(f"\n[replays] Importing from {replay_dir}")
    if not replay_dir.exists():
        print(f"  - Skipped: folder not found ({replay_dir})")
        return 1

    if args.balance_dataset or args.max_states_per_group > 0:
        summary = build_balanced_dataset(
            replays_dir=replay_dir,
            out_file=output_file,
            max_states_per_group=args.max_states_per_group,
            group_mode=args.group_mode,
            verbose=True,
        )
        count = int(summary["total_states"])
        print(
            f"Balanced dataset groups: {summary['total_groups']} (mode={summary['group_mode']})"
        )
    else:
        count = import_replays_from_directory(
            replay_dir=replay_dir,
            output_file=output_file,
            tag="replays",
            verbose=True,
        )
    if count <= 0:
        print("\nNo replay datasets were imported. Add .w3g files to replays/incoming.")
        return 1

    _register_dataset(
        manager=dataset_manager,
        dataset_id=args.dataset_id,
        name="Imported Replays",
        description=f"Imported from {replay_dir}",
        sample_path=output_file,
        tags=["replays", "training"],
    )

    if args.skip_training:
        print("\nTraining skipped (--skip-training).")
        return 0

    policy_manager = PolicyManager(args.policies_dir)
    if not _ensure_policy(
        manager=policy_manager,
        version_id=args.policy_version,
        description=args.policy_description,
        params_json=args.policy_params,
        auto_init=not args.no_auto_init_policy,
    ):
        return 1

    train_dataset_id = args.train_dataset_id or args.dataset_id
    dataset_path = dataset_manager.get_dataset_path(train_dataset_id)
    if dataset_path is None:
        dataset_path = dataset_manager.get_dataset_path(args.dataset_id)
        train_dataset_id = args.dataset_id

    if dataset_path is None:
        print("No dataset file found for training.")
        return 1

    print(f"\n[training] policy={args.policy_version} dataset={train_dataset_id}")
    result = run_training(str(dataset_path), args.policy_version, args.policies_dir)

    out_path = reports_dir / "training_result_imported_replays.json"
    out_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))
    print(f"\n✓ Training report: {out_path}")

    return 0 if result.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
