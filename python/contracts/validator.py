from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


@lru_cache(maxsize=4)
def _load_schema(name: str) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    schema_path = root / "contracts" / name
    payload = json.loads(schema_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid schema payload in {schema_path}")
    return payload


def _as_payload(value: Any) -> dict[str, Any]:
    if is_dataclass(value):
        payload = asdict(value)
    elif isinstance(value, dict):
        payload = value
    else:
        raise ValueError("Expected dataclass or dictionary payload")

    if not isinstance(payload, dict):
        raise ValueError("Contract payload must be an object")
    return payload


def validate_game_state(value: Any) -> dict[str, Any]:
    payload = _as_payload(value)
    schema = _load_schema("game_state.schema.json")
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: e.path)
    if errors:
        messages = "; ".join(error.message for error in errors)
        raise ValueError(f"Game state contract validation failed: {messages}")
    return payload


def validate_action_intent(value: Any) -> dict[str, Any]:
    payload = _as_payload(value)
    schema = _load_schema("action_intent.schema.json")
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: e.path)
    if errors:
        messages = "; ".join(error.message for error in errors)
        raise ValueError(f"Action intent contract validation failed: {messages}")
    return payload
