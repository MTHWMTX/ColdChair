from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StateValidationError:
    field: str
    error: str
    value: Any = None


@dataclass
class StateValidationResult:
    valid: bool
    errors: list[StateValidationError] = field(default_factory=list)

    def add_error(self, field: str, error: str, value: Any = None) -> None:
        self.errors.append(StateValidationError(field=field, error=error, value=value))

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "error_count": len(self.errors),
            "errors": [
                {"field": e.field, "error": e.error} for e in self.errors
            ],
        }


class StateValidator:
    """Validates game state integrity and consistency."""

    @staticmethod
    def validate_resources(resources: dict[str, int]) -> StateValidationResult:
        """Validate resource state."""
        result = StateValidationResult(valid=True)

        if not isinstance(resources.get("gold"), int) or resources["gold"] < 0:
            result.valid = False
            result.add_error("resources.gold", "Gold must be a non-negative integer", resources.get("gold"))

        if not isinstance(resources.get("lumber"), int) or resources["lumber"] < 0:
            result.valid = False
            result.add_error("resources.lumber", "Lumber must be a non-negative integer", resources.get("lumber"))

        return result

    @staticmethod
    def validate_supply(supply: dict[str, int]) -> StateValidationResult:
        """Validate supply state."""
        result = StateValidationResult(valid=True)

        used = supply.get("used", 0)
        maximum = supply.get("maximum", 0)

        if not isinstance(used, int) or used < 0:
            result.valid = False
            result.add_error("supply.used", "Used supply must be a non-negative integer", used)

        if not isinstance(maximum, int) or maximum < 0:
            result.valid = False
            result.add_error("supply.maximum", "Max supply must be a non-negative integer", maximum)

        if used > maximum:
            result.valid = False
            result.add_error("supply", "Used supply exceeds maximum supply", {"used": used, "max": maximum})

        return result

    @staticmethod
    def validate_units(units: list[dict[str, Any]]) -> StateValidationResult:
        """Validate units list."""
        result = StateValidationResult(valid=True)

        if not isinstance(units, list):
            result.valid = False
            result.add_error("units", "Units must be a list", type(units).__name__)
            return result

        for idx, unit in enumerate(units):
            if not isinstance(unit.get("id"), int) or unit["id"] <= 0:
                result.valid = False
                result.add_error(f"units[{idx}].id", "Unit ID must be a positive integer", unit.get("id"))

            if not isinstance(unit.get("type"), str) or not unit["type"]:
                result.valid = False
                result.add_error(f"units[{idx}].type", "Unit type must be a non-empty string", unit.get("type"))

            if not isinstance(unit.get("health"), (int, float)) or unit["health"] <= 0:
                result.valid = False
                result.add_error(f"units[{idx}].health", "Unit health must be positive", unit.get("health"))

        return result

    @staticmethod
    def validate_game_state(state: dict[str, Any]) -> StateValidationResult:
        """Validate complete game state."""
        result = StateValidationResult(valid=True)

        # Check resources
        resources_result = StateValidator.validate_resources(state.get("resources", {}))
        if not resources_result.valid:
            result.valid = False
            result.errors.extend(resources_result.errors)

        # Check supply
        supply_result = StateValidator.validate_supply(state.get("supply", {}))
        if not supply_result.valid:
            result.valid = False
            result.errors.extend(supply_result.errors)

        # Check units
        units_result = StateValidator.validate_units(state.get("units", []))
        if not units_result.valid:
            result.valid = False
            result.errors.extend(units_result.errors)

        # Check tick
        tick = state.get("tick", 0)
        if not isinstance(tick, int) or tick < 0:
            result.valid = False
            result.add_error("tick", "Tick must be a non-negative integer", tick)

        return result
