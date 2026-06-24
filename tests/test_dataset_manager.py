from __future__ import annotations

from pathlib import Path

import pytest

from python.training.dataset_manager import DatasetManager


def test_register_dataset(tmp_path: Path) -> None:
    manager = DatasetManager(tmp_path / "datasets")

    sample_file = Path(__file__).parent.parent / "examples" / "sample_states.json"

    metadata = manager.register_dataset(
        "ds1",
        "Test Dataset",
        "Test dataset description",
        sample_file,
        tags=["test", "validation"],
    )

    assert metadata.dataset_id == "ds1"
    assert metadata.sample_count == 2
    assert "test" in metadata.tags


def test_get_dataset() -> None:
    manager = DatasetManager()
    sample_file = Path(__file__).parent.parent / "examples" / "sample_states.json"

    manager.register_dataset("ds1", "Dataset 1", "Desc", sample_file)
    dataset = manager.get_dataset("ds1")

    assert dataset is not None
    assert dataset.name == "Dataset 1"


def test_find_datasets_by_tag() -> None:
    manager = DatasetManager()
    sample_file = Path(__file__).parent.parent / "examples" / "sample_states.json"

    manager.register_dataset("ds1", "Dataset 1", "Desc", sample_file, tags=["training"])
    manager.register_dataset("ds2", "Dataset 2", "Desc", sample_file, tags=["testing"])
    manager.register_dataset("ds3", "Dataset 3", "Desc", sample_file, tags=["training"])

    training_datasets = manager.find_datasets_by_tag("training")
    assert len(training_datasets) == 2
