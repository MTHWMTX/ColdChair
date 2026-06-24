from __future__ import annotations

from pathlib import Path
from datetime import datetime

import pytest

from python.training.policy_manager import PolicyManager, TrainingLog, TrainingRun, PolicyVersion


def test_create_policy_version() -> None:
    manager = PolicyManager()
    version = manager.create_policy_version(
        "v1.0",
        "Initial baseline policy",
        {"max_actions_per_second": 1000.0},
    )

    assert version.version_id == "v1.0"
    assert version.description == "Initial baseline policy"
    assert manager.current_version == version


def test_update_metrics() -> None:
    manager = PolicyManager()
    manager.create_policy_version("v1.0", "Test", {})
    manager.update_metrics("v1.0", {"accuracy": 0.85, "loss": 0.15})

    version = manager.get_version("v1.0")
    assert version.metrics["accuracy"] == 0.85


def test_get_best_version() -> None:
    manager = PolicyManager()
    manager.create_policy_version("v1.0", "Policy 1", {})
    manager.create_policy_version("v2.0", "Policy 2", {})

    manager.set_test_accuracy("v1.0", 0.80)
    manager.set_test_accuracy("v2.0", 0.95)

    best = manager.get_best_version()
    assert best.version_id == "v2.0"


def test_training_log_record_and_retrieve() -> None:
    log = TrainingLog()

    run1 = TrainingRun(
        run_id="run1",
        timestamp="2026-06-24T00:00:00",
        policy_version="v1.0",
        dataset_size=100,
        executed_actions=80,
        blocked_actions=20,
        execution_rate=0.8,
        metrics={"accuracy": 0.80},
        errors=[],
    )

    log.record_run(run1)
    assert len(log.runs) == 1
    assert log.get_latest_run() == run1


def test_training_log_get_runs_for_version() -> None:
    log = TrainingLog()

    run1 = TrainingRun(
        "run1", "2026-06-24T00:00:00", "v1.0", 100, 80, 20, 0.8, {"accuracy": 0.80}, []
    )
    run2 = TrainingRun(
        "run2", "2026-06-24T01:00:00", "v1.0", 100, 85, 15, 0.85, {"accuracy": 0.85}, []
    )
    run3 = TrainingRun(
        "run3", "2026-06-24T02:00:00", "v2.0", 100, 90, 10, 0.90, {"accuracy": 0.90}, []
    )

    log.record_run(run1)
    log.record_run(run2)
    log.record_run(run3)

    v1_runs = log.get_runs_for_version("v1.0")
    assert len(v1_runs) == 2


def test_average_metrics_for_version() -> None:
    log = TrainingLog()

    run1 = TrainingRun(
        "run1", "2026-06-24T00:00:00", "v1.0", 100, 80, 20, 0.8, {"accuracy": 0.80}, []
    )
    run2 = TrainingRun(
        "run2", "2026-06-24T01:00:00", "v1.0", 100, 90, 10, 0.90, {"accuracy": 0.90}, []
    )

    log.record_run(run1)
    log.record_run(run2)

    avg = log.average_metrics_for_version("v1.0")
    assert abs(avg["accuracy"] - 0.85) < 0.01


def test_policy_version_save_load(tmp_path: Path) -> None:
    manager = PolicyManager()
    version = manager.create_policy_version("v1.0", "Test", {"param": "value"})

    save_path = tmp_path / "version.json"
    manager.save_version("v1.0", save_path)

    assert save_path.exists()

    manager2 = PolicyManager()
    loaded = manager2.load_version(save_path)
    assert loaded is not None
    assert loaded.version_id == "v1.0"
