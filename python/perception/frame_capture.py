from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FrameCaptureConfig:
    fps: int = 10
    region: tuple[int, int, int, int] | None = None


class FrameCapture:
    """Perception stub for Phase 4 foundation work."""

    def __init__(self, config: FrameCaptureConfig | None = None) -> None:
        self.config = config or FrameCaptureConfig()

    def capture(self) -> dict[str, Any]:
        """Return placeholder frame payload until real capture is implemented."""
        return {
            "status": "placeholder",
            "fps": self.config.fps,
            "region": self.config.region,
        }
