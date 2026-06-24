from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional


@dataclass
class PipelineConfig:
    """Configuration for a complete e2e pipeline execution."""

    name: str
    description: str
    max_actions_per_second: float = 1000000.0
    online_mode_enabled: bool = False
    dry_run_enabled: bool = True
    window_active_required: bool = True
    min_train_rate: float = 0.0
    min_gather_rate: float = 0.0
    min_executed_rate: float = 0.0
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineConfig:
        return cls(**data)


@dataclass
class ExperimentConfig:
    """Experiment specification with multiple pipeline configurations."""

    experiment_id: str
    description: str
    created_at: str
    configurations: dict[str, PipelineConfig] = field(default_factory=dict)
    baseline_config_name: Optional[str] = None

    def add_config(self, config: PipelineConfig) -> None:
        self.configurations[config.name] = config

    def get_config(self, name: str) -> PipelineConfig | None:
        return self.configurations.get(name)

    def list_configs(self) -> list[str]:
        return sorted(self.configurations.keys())

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "description": self.description,
            "created_at": self.created_at,
            "baseline_config_name": self.baseline_config_name,
            "configurations": {name: config.to_dict() for name, config in self.configurations.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExperimentConfig:
        exp = cls(
            experiment_id=data["experiment_id"],
            description=data["description"],
            created_at=data["created_at"],
            baseline_config_name=data.get("baseline_config_name"),
        )
        for name, config_data in data.get("configurations", {}).items():
            exp.add_config(PipelineConfig.from_dict(config_data))
        return exp

    def save(self, out_path: str | Path) -> None:
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def load(cls, in_path: str | Path) -> ExperimentConfig:
        in_path = Path(in_path)
        data = json.loads(in_path.read_text(encoding="utf-8"))
        return cls.from_dict(data)


def create_default_config() -> PipelineConfig:
    """Create default safety-first pipeline configuration."""
    return PipelineConfig(
        name="default_safety_first",
        description="Safety-first default with dry-run enabled",
        max_actions_per_second=1000000.0,
        online_mode_enabled=False,
        dry_run_enabled=True,
        window_active_required=True,
        min_executed_rate=0.8,
    )


def create_aggressive_config() -> PipelineConfig:
    """Create aggressive tuned configuration for performance testing."""
    return PipelineConfig(
        name="aggressive_tuned",
        description="Aggressive tuning with higher rate limits",
        max_actions_per_second=10.0,
        online_mode_enabled=False,
        dry_run_enabled=True,
        window_active_required=False,
        min_executed_rate=0.9,
        tags=["performance", "tuning"],
    )


def create_conservative_config() -> PipelineConfig:
    """Create conservative configuration with stricter constraints."""
    return PipelineConfig(
        name="conservative_safety",
        description="Conservative with strict safety constraints",
        max_actions_per_second=1.0,
        online_mode_enabled=False,
        dry_run_enabled=True,
        window_active_required=True,
        min_executed_rate=0.95,
        min_train_rate=0.3,
        tags=["safety", "conservative"],
    )
