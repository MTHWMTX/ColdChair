from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from python.policy.decision_engine import ActionIntent


@dataclass
class Bounds:
    min_x: float
    max_x: float
    min_y: float
    max_y: float


@dataclass
class TargetProfile:
    world_bounds: Bounds | None = None
    screen_bounds: Bounds | None = None
    resource_points: list[dict[str, float]] | None = None
    attack_move_points: list[dict[str, float]] | None = None

    @staticmethod
    def from_file(path: str | Path) -> "TargetProfile":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))

        world = payload.get("world_bounds")
        screen = payload.get("screen_bounds")

        world_bounds = (
            Bounds(
                min_x=float(world.get("min_x", 0.0)),
                max_x=float(world.get("max_x", 0.0)),
                min_y=float(world.get("min_y", 0.0)),
                max_y=float(world.get("max_y", 0.0)),
            )
            if isinstance(world, dict)
            else None
        )
        screen_bounds = (
            Bounds(
                min_x=float(screen.get("min_x", 0.0)),
                max_x=float(screen.get("max_x", 0.0)),
                min_y=float(screen.get("min_y", 0.0)),
                max_y=float(screen.get("max_y", 0.0)),
            )
            if isinstance(screen, dict)
            else None
        )

        return TargetProfile(
            world_bounds=world_bounds,
            screen_bounds=screen_bounds,
            resource_points=payload.get("resource_points", []),
            attack_move_points=payload.get("attack_move_points", []),
        )


class CommandEnricher:
    """Enriches abstract commands with concrete screen coordinates."""

    def __init__(self, profile: TargetProfile | None = None) -> None:
        self.profile = profile or TargetProfile()

    def enrich_command(
        self,
        command: dict[str, Any],
        intent: ActionIntent,
        state: dict[str, Any] | None,
    ) -> dict[str, Any]:
        enriched = dict(command)
        op = str(enriched.get("op", ""))

        if op == "right_click_resource":
            if "x" not in enriched or "y" not in enriched:
                point = self._resource_point_from_state(state) or self._first_point(
                    self.profile.resource_points
                )
                if point is not None:
                    enriched["x"] = float(point["x"])
                    enriched["y"] = float(point["y"])

        if op == "attack_move":
            if "x" in enriched and "y" in enriched:
                mapped = self._map_world_to_screen(float(enriched["x"]), float(enriched["y"]))
                if mapped is not None:
                    enriched["x"], enriched["y"] = mapped
            else:
                point = self._first_point(self.profile.attack_move_points)
                if point is not None:
                    enriched["x"] = float(point["x"])
                    enriched["y"] = float(point["y"])

        return enriched

    def _resource_point_from_state(self, state: dict[str, Any] | None) -> dict[str, float] | None:
        if not isinstance(state, dict):
            return None

        nodes = state.get("resource_nodes", [])
        if not isinstance(nodes, list):
            return None

        for node in nodes:
            if not isinstance(node, dict):
                continue
            pos = node.get("position")
            if not isinstance(pos, dict):
                continue

            world_x = pos.get("x")
            world_y = pos.get("y")
            if world_x is None or world_y is None:
                continue

            mapped = self._map_world_to_screen(float(world_x), float(world_y))
            if mapped is None:
                return {"x": float(world_x), "y": float(world_y)}

            return {"x": mapped[0], "y": mapped[1]}

        return None

    def _map_world_to_screen(self, world_x: float, world_y: float) -> tuple[float, float] | None:
        wb = self.profile.world_bounds
        sb = self.profile.screen_bounds
        if wb is None or sb is None:
            return None

        world_dx = wb.max_x - wb.min_x
        world_dy = wb.max_y - wb.min_y
        if world_dx <= 0 or world_dy <= 0:
            return None

        nx = (world_x - wb.min_x) / world_dx
        ny = (world_y - wb.min_y) / world_dy
        nx = max(0.0, min(1.0, nx))
        ny = max(0.0, min(1.0, ny))

        screen_x = sb.min_x + nx * (sb.max_x - sb.min_x)
        screen_y = sb.min_y + ny * (sb.max_y - sb.min_y)
        return screen_x, screen_y

    @staticmethod
    def _first_point(points: list[dict[str, float]] | None) -> dict[str, float] | None:
        if not points:
            return None

        first = points[0]
        if not isinstance(first, dict):
            return None

        if "x" not in first or "y" not in first:
            return None

        return {"x": float(first["x"]), "y": float(first["y"])}
