from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ResourceState:
    gold: int
    lumber: int


@dataclass
class SupplyState:
    used: int
    cap: int


@dataclass
class UnitState:
    id: str
    owner: str
    type: str
    hp: float
    x: float
    y: float


@dataclass
class GameState:
    tick: int
    resources: ResourceState
    supply: SupplyState
    units: list[UnitState]


def game_state_from_dict(payload: dict[str, Any]) -> GameState:
    resources_payload = payload.get("resources", {})
    supply_payload = payload.get("supply", {})
    units_payload = payload.get("units", [])

    units = [
        UnitState(
            id=str(unit["id"]),
            owner=str(unit["owner"]),
            type=str(unit["type"]),
            hp=float(unit["hp"]),
            x=float(unit["position"]["x"]),
            y=float(unit["position"]["y"]),
        )
        for unit in units_payload
    ]

    return GameState(
        tick=int(payload.get("tick", 0)),
        resources=ResourceState(
            gold=int(resources_payload.get("gold", 0)),
            lumber=int(resources_payload.get("lumber", 0)),
        ),
        supply=SupplyState(
            used=int(supply_payload.get("used", 0)),
            cap=int(supply_payload.get("cap", 0)),
        ),
        units=units,
    )
