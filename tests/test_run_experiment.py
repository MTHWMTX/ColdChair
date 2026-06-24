from __future__ import annotations

import json
from pathlib import Path

import pytest

from python.config.pipeline_config import create_default_config
from python.config.run_experiment import run_experiment


def test_run_experiment_with_default_config() -> None:
    config = create_default_config()
    samples_path = Path(__file__).parent.parent / "examples" / "sample_states.json"

    result = run_experiment(config, str(samples_path))

    assert result.get("status") == "success"
    assert result.get("config_name") == "default_safety_first"
    assert "total_states" in result
    assert "executed_rate" in result


def test_run_experiment_missing_samples() -> None:
    config = create_default_config()
    result = run_experiment(config, "/nonexistent/path.json")

    assert result.get("status") == "failed"
    assert "error" in result
