from pathlib import Path

import pytest

from python.replay.sample_loader import load_state_samples


@pytest.fixture()
def temp_sample_file(tmp_path: Path) -> Path:
    sample_path = tmp_path / "samples.json"
    sample_path.write_text(
        """[
  {
    \"resources\": {\"gold\": 100, \"lumber\": 20},
    \"supply\": {\"used\": 8, \"cap\": 18},
    \"units\": []
  }
]""",
        encoding="utf-8",
    )
    return sample_path


def test_load_state_samples_json(temp_sample_file: Path) -> None:
    samples = load_state_samples(temp_sample_file)
    assert len(samples) == 1
    assert samples[0]["resources"]["gold"] == 100


def test_load_state_samples_missing_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_state_samples("does_not_exist.json")


def test_load_state_samples_rejects_missing_keys(tmp_path: Path) -> None:
    broken_path = tmp_path / "broken.json"
    broken_path.write_text("[{\"resources\": {}}]", encoding="utf-8")

    with pytest.raises(ValueError):
        load_state_samples(broken_path)
