from __future__ import annotations

import pytest

from python.contracts.validator import validate_action_intent, validate_game_state


def test_validate_game_state_accepts_valid_payload() -> None:
    payload = {
        "tick": 1,
        "resources": {"gold": 100, "lumber": 20},
        "supply": {"used": 6, "cap": 18},
        "units": [],
    }

    validated = validate_game_state(payload)
    assert validated["tick"] == 1


def test_validate_game_state_rejects_invalid_payload() -> None:
    payload = {
        "tick": 1,
        "resources": {"gold": -1, "lumber": 20},
        "supply": {"used": 6, "cap": 18},
        "units": [],
    }

    with pytest.raises(ValueError):
        validate_game_state(payload)


def test_validate_action_intent_accepts_valid_payload() -> None:
    payload = {"type": "train_unit", "priority": 10, "target_id": None, "position": None}

    validated = validate_action_intent(payload)
    assert validated["type"] == "train_unit"


def test_validate_action_intent_rejects_invalid_payload() -> None:
    payload = {"type": "train_unit", "priority": -1}

    with pytest.raises(ValueError):
        validate_action_intent(payload)
