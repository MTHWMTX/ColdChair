#!/usr/bin/env python
"""Quick start script to initialize and run first training."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


def run_command(cmd: list[str]) -> bool:
    """Run command and return success status."""
    print(f"\n→ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode == 0


def main() -> int:
    print("=" * 60)
    print("ColdChair Training Quick Start")
    print("=" * 60)

    # Step 1: Initialize baseline policy
    print("\n[1/4] Initializing baseline policy...")
    if not run_command(
        [
            "python",
            "-m",
            "python.training.orchestrate",
            "init-policy",
            "--version",
            "v1.0",
            "--description",
            "Baseline decision policy from MVP",
        ]
    ):
        print("Failed to initialize policy")
        return 1

    # Step 2: Register training dataset
    print("\n[2/4] Registering training dataset...")
    sample_path = Path("examples/sample_states.json")
    if not sample_path.exists():
        print(f"Sample file not found: {sample_path}")
        return 1

    if not run_command(
        [
            "python",
            "-m",
            "python.training.orchestrate",
            "register-dataset",
            "--dataset-id",
            "ds_initial",
            "--name",
            "Initial Training Set",
            "--description",
            "Baseline scenarios for first training run",
            "--samples",
            str(sample_path),
            "--tags",
            "baseline,initial",
        ]
    ):
        print("Failed to register dataset")
        return 1

    # Step 3: Run training
    print("\n[3/4] Running training pipeline...")
    if not run_command(
        [
            "python",
            "-m",
            "python.training.orchestrate",
            "train",
            "--policy-version",
            "v1.0",
            "--dataset-id",
            "ds_initial",
            "--out",
            "reports/training_result_quickstart.json",
        ]
    ):
        print("Failed to run training")
        return 1

    # Step 4: Check status
    print("\n[4/4] Checking training status...")
    if not run_command(["python", "-m", "python.training.orchestrate", "status"]):
        print("Failed to check status")
        return 1

    print("\n" + "=" * 60)
    print("✓ Training ready! You can now:")
    print("  - Create new policy versions for experimentation")
    print("  - Add more training datasets")
    print("  - Run iterative training to improve performance")
    print("  - Track metrics and compare versions")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
