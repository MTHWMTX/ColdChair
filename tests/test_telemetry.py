from __future__ import annotations

from pathlib import Path

import pytest

from python.telemetry.profiler import PipelineProfile, Profiler, profile_function
from python.telemetry.state_validator import StateValidator, StateValidationResult


def test_timing_metric_basic() -> None:
    profile = PipelineProfile()
    profile.record_metric("test_metric", 10.5)
    profile.record_metric("test_metric", 20.3)

    metric = profile.metrics["test_metric"]
    assert metric.count == 2
    assert abs(metric.mean_ms() - 15.4) < 0.1


def test_profiler_context_manager() -> None:
    profile = PipelineProfile()

    with Profiler(profile, "sample_op"):
        pass

    assert "sample_op" in profile.metrics
    assert profile.metrics["sample_op"].count >= 1


def test_profiler_decorator() -> None:
    profile = PipelineProfile()

    @profile_function(profile, "decorated_func")
    def test_func() -> int:
        return 42

    result = test_func()
    assert result == 42
    assert "decorated_func" in profile.metrics


def test_state_validator_valid_resources() -> None:
    resources = {"gold": 100, "lumber": 50}
    result = StateValidator.validate_resources(resources)
    assert result.valid


def test_state_validator_invalid_resources() -> None:
    resources = {"gold": -10, "lumber": 50}
    result = StateValidator.validate_resources(resources)
    assert not result.valid
    assert len(result.errors) > 0


def test_state_validator_valid_supply() -> None:
    supply = {"used": 10, "maximum": 20}
    result = StateValidator.validate_supply(supply)
    assert result.valid


def test_state_validator_supply_overflow() -> None:
    supply = {"used": 25, "maximum": 20}
    result = StateValidator.validate_supply(supply)
    assert not result.valid


def test_state_validator_valid_units() -> None:
    units = [
        {"id": 1, "type": "footman", "health": 60},
        {"id": 2, "type": "archer", "health": 45},
    ]
    result = StateValidator.validate_units(units)
    assert result.valid


def test_state_validator_invalid_units() -> None:
    units = [{"id": -1, "type": "footman", "health": 60}]
    result = StateValidator.validate_units(units)
    assert not result.valid


def test_state_validator_complete_state() -> None:
    state = {
        "tick": 5,
        "resources": {"gold": 100, "lumber": 50},
        "supply": {"used": 10, "maximum": 20},
        "units": [{"id": 1, "type": "footman", "health": 60}],
    }
    result = StateValidator.validate_game_state(state)
    assert result.valid


def test_state_validator_invalid_state() -> None:
    state = {
        "tick": -1,
        "resources": {"gold": -100, "lumber": 50},
        "supply": {"used": 25, "maximum": 20},
        "units": [{"id": 0, "type": "", "health": -10}],
    }
    result = StateValidator.validate_game_state(state)
    assert not result.valid
    assert len(result.errors) > 0


def test_profile_to_dict() -> None:
    profile = PipelineProfile(total_elapsed_ms=100.5)
    profile.record_metric("op1", 25.0)
    profile.record_phase("load", 50.0)
    profile.add_error()

    profile_dict = profile.to_dict()
    assert profile_dict["total_elapsed_ms"] == 100.5
    assert profile_dict["errors_encountered"] == 1
    assert "op1" in profile_dict["metrics"]
    assert profile_dict["phase_timings"]["load"] == 50.0
