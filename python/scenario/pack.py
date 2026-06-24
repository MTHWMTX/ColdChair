from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass
class ScenarioMetadata:
    name: str
    description: str
    expected_executed_rate: float
    expected_train_unit_actions: int
    expected_attack_actions: int
    expected_gather_actions: int


class ScenarioPack:
    """Manages scenario files, metadata, and regression expectations."""

    def __init__(self, scenario_dir: str | Path) -> None:
        self.scenario_dir = Path(scenario_dir)
        self.metadata: dict[str, ScenarioMetadata] = {}

    def add_scenario(
        self,
        filename: str,
        description: str,
        expected_executed_rate: float,
        expected_train_unit_actions: int = 0,
        expected_attack_actions: int = 0,
        expected_gather_actions: int = 0,
    ) -> None:
        """Register scenario metadata for regression tracking."""
        self.metadata[filename] = ScenarioMetadata(
            name=filename,
            description=description,
            expected_executed_rate=expected_executed_rate,
            expected_train_unit_actions=expected_train_unit_actions,
            expected_attack_actions=expected_attack_actions,
            expected_gather_actions=expected_gather_actions,
        )

    def get_metadata(self, filename: str) -> ScenarioMetadata | None:
        return self.metadata.get(filename)

    def list_scenarios(self) -> list[str]:
        return sorted(self.metadata.keys())

    def export_metadata(self, out_path: str | Path) -> None:
        """Export scenario metadata for external tools."""
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        metadata_dict = {name: asdict(meta) for name, meta in self.metadata.items()}
        out_path.write_text(json.dumps(metadata_dict, indent=2), encoding="utf-8")

    def import_metadata(self, in_path: str | Path) -> None:
        """Import scenario metadata from JSON file."""
        in_path = Path(in_path)
        if not in_path.exists():
            return

        data = json.loads(in_path.read_text(encoding="utf-8"))
        for name, meta in data.items():
            self.metadata[name] = ScenarioMetadata(**meta)


def create_local_ai_pack() -> ScenarioPack:
    """Create the local AI scenario pack with regression expectations."""
    pack = ScenarioPack("scenarios/local_ai")

    pack.add_scenario(
        "early_pressure.json",
        "Early game pressure scenario - test rapid decision making",
        expected_executed_rate=1.0,
        expected_train_unit_actions=1,
        expected_gather_actions=0,
    )

    pack.add_scenario(
        "opening_balanced.json",
        "Balanced opening - test resource management",
        expected_executed_rate=1.0,
        expected_train_unit_actions=1,
        expected_gather_actions=1,
    )

    pack.add_scenario(
        "counter_pressure.json",
        "Counter pressure scenario - test defensive reactions",
        expected_executed_rate=0.9,
        expected_train_unit_actions=0,
        expected_attack_actions=2,
    )

    return pack
