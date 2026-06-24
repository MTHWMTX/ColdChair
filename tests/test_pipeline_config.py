from __future__ import annotations

from pathlib import Path

import pytest

from python.config.pipeline_config import (
    PipelineConfig,
    ExperimentConfig,
    create_default_config,
    create_aggressive_config,
    create_conservative_config,
)


def test_pipeline_config_basic() -> None:
    config = PipelineConfig(
        name="test_config",
        description="Test configuration",
        max_actions_per_second=5.0,
    )

    assert config.name == "test_config"
    assert config.max_actions_per_second == 5.0
    assert config.dry_run_enabled is True


def test_pipeline_config_dict_roundtrip() -> None:
    config = PipelineConfig(
        name="test",
        description="Test",
        max_actions_per_second=3.0,
        tags=["test", "tuning"],
    )

    config_dict = config.to_dict()
    config2 = PipelineConfig.from_dict(config_dict)

    assert config2.name == "test"
    assert config2.max_actions_per_second == 3.0
    assert config2.tags == ["test", "tuning"]


def test_experiment_config_add_and_list() -> None:
    exp = ExperimentConfig(
        experiment_id="exp1",
        description="Test experiment",
        created_at="2026-06-24",
    )

    config1 = PipelineConfig(name="config1", description="Config 1")
    config2 = PipelineConfig(name="config2", description="Config 2")

    exp.add_config(config1)
    exp.add_config(config2)

    configs = exp.list_configs()
    assert configs == ["config1", "config2"]
    assert exp.get_config("config1") is not None


def test_experiment_config_save_load(tmp_path: Path) -> None:
    exp = ExperimentConfig(
        experiment_id="exp1",
        description="Test experiment",
        created_at="2026-06-24",
        baseline_config_name="config1",
    )

    config = PipelineConfig(name="config1", description="Test config")
    exp.add_config(config)

    save_path = tmp_path / "experiment.json"
    exp.save(save_path)

    exp2 = ExperimentConfig.load(save_path)
    assert exp2.experiment_id == "exp1"
    assert exp2.baseline_config_name == "config1"
    assert exp2.get_config("config1") is not None


def test_create_default_config() -> None:
    config = create_default_config()
    assert config.name == "default_safety_first"
    assert config.dry_run_enabled is True
    assert config.online_mode_enabled is False


def test_create_aggressive_config() -> None:
    config = create_aggressive_config()
    assert config.name == "aggressive_tuned"
    assert config.max_actions_per_second == 10.0
    assert "performance" in config.tags


def test_create_conservative_config() -> None:
    config = create_conservative_config()
    assert config.name == "conservative_safety"
    assert config.max_actions_per_second == 1.0
    assert "safety" in config.tags
    assert config.min_executed_rate == 0.95
