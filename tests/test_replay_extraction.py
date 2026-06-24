from __future__ import annotations

import json
from pathlib import Path

from python.replay.w3g_parser import W3GParser


def test_parser_extracts_sorted_state_samples(tmp_path: Path) -> None:
    replay_path = tmp_path / "replay.json"
    replay_path.write_text(
        json.dumps(
            {
                "map_name": "Echo Isles",
                "duration_ms": 1000,
                "player_count": 2,
                "events": [
                    {
                        "type": "state",
                        "state": {
                            "tick": 5,
                            "resources": {"gold": 10, "lumber": 0},
                            "supply": {"used": 10, "cap": 20},
                            "units": [],
                        },
                    },
                    {
                        "type": "state",
                        "state": {
                            "tick": 1,
                            "resources": {"gold": 200, "lumber": 60},
                            "supply": {"used": 9, "cap": 20},
                            "units": [],
                        },
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    parser = W3GParser()
    parsed = parser.parse(replay_path)
    samples = parser.to_game_state_samples(parsed)

    assert parsed.map_name == "Echo Isles"
    assert len(samples) == 2
    assert samples[0]["tick"] == 1
    assert samples[1]["tick"] == 5


def test_parser_rejects_non_json_replay(tmp_path: Path) -> None:
    replay_path = tmp_path / "replay.w3g"
    replay_path.write_text("placeholder", encoding="utf-8")

    parser = W3GParser()

    try:
        parser.parse(replay_path)
        assert False, "Expected ValueError"
    except ValueError as exc:
        # Now parser validates .w3g signature
        assert "Failed to parse" in str(exc) or "Invalid .w3g" in str(exc)
