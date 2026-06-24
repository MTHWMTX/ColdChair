from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from python.contracts.validator import validate_game_state


def load_state_samples(path: str | Path) -> list[dict[str, Any]]:
    """Load normalized game-state samples from JSON or JSONL files."""
    sample_path = Path(path)
    if not sample_path.exists():
        raise FileNotFoundError(f"Sample file not found: {sample_path}")

    suffix = sample_path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(sample_path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError("JSON sample file must contain a list of state objects")
        return _validate_samples(payload)

    if suffix == ".jsonl":
        items: list[dict[str, Any]] = []
        for line in sample_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            item = json.loads(line)
            if not isinstance(item, dict):
                raise ValueError("Each JSONL line must be an object")
            items.append(item)
        return _validate_samples(items)

    raise ValueError("Unsupported sample file extension, expected .json or .jsonl")


def _validate_samples(samples: list[Any]) -> list[dict[str, Any]]:
    validated: list[dict[str, Any]] = []
    for idx, sample in enumerate(samples):
        if not isinstance(sample, dict):
            raise ValueError(f"Sample at index {idx} is not an object")
        normalized = dict(sample)
        normalized.setdefault("tick", idx)
        if "resources" not in sample or "supply" not in sample or "units" not in sample:
            raise ValueError(
                f"Sample at index {idx} is missing one of required keys: resources, supply, units"
            )
        validated.append(validate_game_state(normalized))
    return validated
