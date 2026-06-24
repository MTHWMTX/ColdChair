from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class PolicyVersion:
    """Track a specific policy iteration."""

    version_id: str
    created_at: str
    description: str
    metrics: dict[str, float]
    params: dict[str, Any]
    parent_version: Optional[str] = None
    training_samples_count: int = 0
    test_accuracy: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TrainingRun:
    """Track a single training execution."""

    run_id: str
    timestamp: str
    policy_version: str
    dataset_size: int
    executed_actions: int
    blocked_actions: int
    execution_rate: float
    metrics: dict[str, float]
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PolicyManager:
    """Manage policy versions and track improvements."""

    def __init__(self, policies_dir: str | Path = "policies") -> None:
        self.policies_dir = Path(policies_dir)
        self.policies_dir.mkdir(parents=True, exist_ok=True)
        self.current_version: Optional[PolicyVersion] = None
        self.versions: dict[str, PolicyVersion] = {}

    def create_policy_version(
        self,
        version_id: str,
        description: str,
        params: dict[str, Any],
        parent_version: Optional[str] = None,
    ) -> PolicyVersion:
        """Create a new policy version."""
        version = PolicyVersion(
            version_id=version_id,
            created_at=datetime.now().isoformat(),
            description=description,
            metrics={},
            params=params,
            parent_version=parent_version,
        )
        self.versions[version_id] = version
        self.current_version = version
        return version

    def update_metrics(self, version_id: str, metrics: dict[str, float]) -> None:
        """Update metrics for a policy version."""
        if version_id in self.versions:
            self.versions[version_id].metrics.update(metrics)

    def set_test_accuracy(self, version_id: str, accuracy: float) -> None:
        """Set test accuracy for a version."""
        if version_id in self.versions:
            self.versions[version_id].test_accuracy = accuracy

    def get_version(self, version_id: str) -> PolicyVersion | None:
        return self.versions.get(version_id)

    def list_versions(self) -> list[PolicyVersion]:
        return sorted(self.versions.values(), key=lambda v: v.created_at, reverse=True)

    def get_best_version(self) -> Optional[PolicyVersion]:
        """Get best performing version."""
        if not self.versions:
            return None
        return max(self.versions.values(), key=lambda v: v.test_accuracy)

    def save_version(self, version_id: str, file_path: str | Path) -> None:
        """Save version metadata."""
        if version_id not in self.versions:
            return
        version = self.versions[version_id]
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        import json

        file_path.write_text(json.dumps(version.to_dict(), indent=2), encoding="utf-8")

    def load_version(self, file_path: str | Path) -> Optional[PolicyVersion]:
        """Load version metadata."""
        import json

        file_path = Path(file_path)
        if not file_path.exists():
            return None
        data = json.loads(file_path.read_text(encoding="utf-8"))
        version = PolicyVersion(**data)
        self.versions[version.version_id] = version
        return version


class TrainingLog:
    """Track training runs and iterations."""

    def __init__(self, log_file: str | Path = "reports/training_log.json") -> None:
        self.log_file = Path(log_file)
        self.runs: list[TrainingRun] = []

    def record_run(self, run: TrainingRun) -> None:
        """Record a training run."""
        self.runs.append(run)

    def save(self) -> None:
        """Save training log to file."""
        import json

        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        log_data = [run.to_dict() for run in self.runs]
        self.log_file.write_text(json.dumps(log_data, indent=2), encoding="utf-8")

    def load(self) -> None:
        """Load training log from file."""
        import json

        if not self.log_file.exists():
            return
        data = json.loads(self.log_file.read_text(encoding="utf-8"))
        self.runs = [TrainingRun(**run_data) for run_data in data]

    def get_latest_run(self) -> Optional[TrainingRun]:
        return self.runs[-1] if self.runs else None

    def get_runs_for_version(self, version_id: str) -> list[TrainingRun]:
        return [run for run in self.runs if run.policy_version == version_id]

    def average_metrics_for_version(self, version_id: str) -> dict[str, float]:
        """Get average metrics across all runs for a version."""
        runs = self.get_runs_for_version(version_id)
        if not runs:
            return {}

        avg_metrics: dict[str, float] = {}
        for run in runs:
            for key, value in run.metrics.items():
                if key not in avg_metrics:
                    avg_metrics[key] = 0.0
                avg_metrics[key] += value

        for key in avg_metrics:
            avg_metrics[key] /= len(runs)

        return avg_metrics
