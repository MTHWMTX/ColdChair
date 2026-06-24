from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ReplayParseResult:
    """Represents high-level parsed replay data.

    This is a minimal placeholder parser for Phase 2 scaffolding.
    """

    source_path: Path
    map_name: str
    duration_ms: int
    player_count: int
    events: list[dict[str, Any]]


class W3GParser:
    """Parser interface for Warcraft III replay sources.

    Current implementation accepts a JSON placeholder replay format that
    contains event snapshots. Binary .w3g parsing will be added later.
    """

    def parse(self, replay_path: str | Path) -> ReplayParseResult:
        path = Path(replay_path)
        if not path.exists():
            raise FileNotFoundError(f"Replay file not found: {path}")

        if path.suffix.lower() not in {".json"}:
            raise ValueError("Only JSON replay placeholder input is supported right now")

        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Replay payload must be a JSON object")

        events = payload.get("events", [])
        if not isinstance(events, list):
            raise ValueError("Replay payload field 'events' must be a list")

        return ReplayParseResult(
            source_path=path,
            map_name=str(payload.get("map_name", "unknown")),
            duration_ms=int(payload.get("duration_ms", 0)),
            player_count=int(payload.get("player_count", 0)),
            events=events,
        )

    def to_game_state_samples(self, parsed: ReplayParseResult) -> list[dict[str, Any]]:
        """Convert parsed replay events into normalized game-state samples."""
        samples: list[dict[str, Any]] = []
        for event in parsed.events:
            if not isinstance(event, dict):
                continue

            if event.get("type") != "state":
                continue

            state = event.get("state", {})
            if not isinstance(state, dict):
                continue

            sample = {
                "tick": int(state.get("tick", 0)),
                "resources": {
                    "gold": int(state.get("resources", {}).get("gold", 0)),
                    "lumber": int(state.get("resources", {}).get("lumber", 0)),
                },
                "supply": {
                    "used": int(state.get("supply", {}).get("used", 0)),
                    "cap": int(state.get("supply", {}).get("cap", 0)),
                },
                "units": state.get("units", []),
            }
            samples.append(sample)

        # Deterministic ordering by tick guarantees reproducible evaluation.
        return sorted(samples, key=lambda s: int(s.get("tick", 0)))
