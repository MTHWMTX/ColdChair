from __future__ import annotations

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


class W3GParser:
    """Placeholder parser interface for Warcraft III replay files."""

    def parse(self, replay_path: str | Path) -> ReplayParseResult:
        path = Path(replay_path)
        if not path.exists():
            raise FileNotFoundError(f"Replay file not found: {path}")

        # TODO: Implement full .w3g binary parsing.
        # For now we return conservative placeholder metadata.
        return ReplayParseResult(
            source_path=path,
            map_name="unknown",
            duration_ms=0,
            player_count=0,
        )

    def to_game_state_samples(self, parsed: ReplayParseResult) -> list[dict[str, Any]]:
        """Convert parsed replay metadata into normalized game-state samples."""
        # TODO: Replace with event timeline extraction once parser is implemented.
        return []
