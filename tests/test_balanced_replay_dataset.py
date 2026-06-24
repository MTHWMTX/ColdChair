from __future__ import annotations

import json
from pathlib import Path

from python.replay.build_balanced_dataset import build_balanced_dataset


def _write_sample(path: Path, tick: int) -> None:
    payload = [
        {
            "tick": tick,
            "resources": {"gold": 200, "lumber": 60},
            "supply": {"used": 10, "cap": 20},
            "units": [
                {
                    "id": f"u{tick}",
                    "owner": "self",
                    "type": "peasant",
                    "hp": 100,
                    "position": {"x": 1, "y": 1},
                }
            ],
        }
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_build_balanced_dataset_caps_per_group(tmp_path: Path) -> None:
    replays = tmp_path / "incoming"
    _write_sample(replays / "h_vs_o" / "a.json", 1)
    _write_sample(replays / "h_vs_o" / "b.json", 2)
    _write_sample(replays / "n_vs_u" / "c.json", 3)
    _write_sample(replays / "n_vs_u" / "d.json", 4)

    out = tmp_path / "balanced.json"
    summary = build_balanced_dataset(replays, out, max_states_per_group=1, verbose=False)

    assert summary["total_groups"] == 2
    assert summary["total_states"] == 2
    assert summary["groups"]["h_vs_o"]["states_after_cap"] == 1
    assert summary["groups"]["n_vs_u"]["states_after_cap"] == 1

    samples = json.loads(out.read_text(encoding="utf-8"))
    assert len(samples) == 2


def test_build_balanced_dataset_empty_returns_zero(tmp_path: Path) -> None:
    replays = tmp_path / "incoming"
    replays.mkdir(parents=True)
    out = tmp_path / "balanced.json"

    summary = build_balanced_dataset(replays, out, max_states_per_group=0, verbose=False)

    assert summary["total_states"] == 0
    assert summary["total_groups"] == 0
    assert not out.exists()
