from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import json


@dataclass
class DatasetMetadata:
    """Metadata for a training dataset."""

    dataset_id: str
    name: str
    description: str
    sample_count: int
    source: str
    created_at: str
    tags: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DatasetManager:
    """Manage training datasets."""

    def __init__(self, datasets_dir: str | Path = "datasets") -> None:
        self.datasets_dir = Path(datasets_dir)
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self.metadata: dict[str, DatasetMetadata] = {}

    def register_dataset(
        self,
        dataset_id: str,
        name: str,
        description: str,
        sample_path: str | Path,
        source: str = "replay",
        tags: list[str] | None = None,
    ) -> DatasetMetadata:
        """Register a new training dataset."""
        sample_path = Path(sample_path)
        if not sample_path.exists():
            raise FileNotFoundError(f"Sample file not found: {sample_path}")

        from python.replay.sample_loader import load_state_samples

        samples = load_state_samples(str(sample_path))

        from datetime import datetime

        metadata = DatasetMetadata(
            dataset_id=dataset_id,
            name=name,
            description=description,
            sample_count=len(samples),
            source=source,
            created_at=datetime.now().isoformat(),
            tags=tags or [],
        )

        self.metadata[dataset_id] = metadata

        # Copy to datasets directory
        dest_path = self.datasets_dir / f"{dataset_id}.json"
        dest_path.write_text(sample_path.read_text(encoding="utf-8"), encoding="utf-8")

        # Save metadata
        self._save_metadata()

        return metadata

    def get_dataset(self, dataset_id: str) -> DatasetMetadata | None:
        return self.metadata.get(dataset_id)

    def list_datasets(self) -> list[DatasetMetadata]:
        return sorted(self.metadata.values(), key=lambda d: d.created_at, reverse=True)

    def find_datasets_by_tag(self, tag: str) -> list[DatasetMetadata]:
        return [d for d in self.metadata.values() if tag in d.tags]

    def get_dataset_path(self, dataset_id: str) -> Path | None:
        path = self.datasets_dir / f"{dataset_id}.json"
        return path if path.exists() else None

    def _save_metadata(self) -> None:
        """Save all metadata to index file."""
        index_path = self.datasets_dir / "index.json"
        data = {did: meta.to_dict() for did, meta in self.metadata.items()}
        index_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _load_metadata(self) -> None:
        """Load all metadata from index file."""
        index_path = self.datasets_dir / "index.json"
        if not index_path.exists():
            return
        data = json.loads(index_path.read_text(encoding="utf-8"))
        for did, meta_data in data.items():
            self.metadata[did] = DatasetMetadata(**meta_data)
