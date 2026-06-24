"""Tests for replay parser and import tools."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from python.replay.w3g_parser import W3GParser, ReplayParseResult


class TestW3GParser:
    """Test W3GParser with various replay formats."""

    def test_parse_json_array(self) -> None:
        """Test parsing JSON array of game states."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            json_file = tmppath / "test.json"

            states = [
                {
                    "tick": 1,
                    "resources": {"gold": 200, "lumber": 60},
                    "supply": {"used": 2, "cap": 15},
                    "units": [{"id": "u1", "owner": "self", "type": "peasant", "hp": 220, "position": {"x": 1, "y": 2}}],
                },
                {
                    "tick": 2,
                    "resources": {"gold": 150, "lumber": 50},
                    "supply": {"used": 3, "cap": 15},
                    "units": [{"id": "u2", "owner": "self", "type": "footman", "hp": 420, "position": {"x": 5, "y": 6}}],
                },
            ]

            json_file.write_text(json.dumps(states))

            parser = W3GParser()
            result = parser.parse(json_file)

            assert isinstance(result, ReplayParseResult)
            assert len(result.events) == 2
            assert result.source_path == json_file

    def test_parse_json_object(self) -> None:
        """Test parsing JSON object with events."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            json_file = tmppath / "test.json"

            replay_obj = {
                "map_name": "Lost Temple",
                "player_count": 2,
                "duration_ms": 60000,
                "events": [
                    {"type": "state", "state": {"tick": 1, "resources": {"gold": 500, "lumber": 100}, "supply": {"used": 0, "cap": 15}, "units": []}},
                    {"type": "state", "state": {"tick": 2, "resources": {"gold": 450, "lumber": 100}, "supply": {"used": 1, "cap": 15}, "units": []}},
                ],
            }

            json_file.write_text(json.dumps(replay_obj))

            parser = W3GParser()
            result = parser.parse(json_file)

            assert result.map_name == "Lost Temple"
            assert result.player_count == 2
            assert len(result.events) == 2

    def test_to_game_state_samples(self) -> None:
        """Test conversion to game state samples."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            json_file = tmppath / "test.json"

            states = [
                {
                    "tick": 1,
                    "resources": {"gold": 200, "lumber": 60},
                    "supply": {"used": 2, "cap": 15},
                    "units": [],
                },
                {
                    "tick": 2,
                    "resources": {"gold": 150, "lumber": 50},
                    "supply": {"used": 3, "cap": 15},
                    "units": [],
                },
            ]

            json_file.write_text(json.dumps(states))

            parser = W3GParser()
            result = parser.parse(json_file)
            samples = parser.to_game_state_samples(result)

            assert len(samples) == 2
            assert samples[0]["tick"] == 1
            assert samples[0]["resources"]["gold"] == 200
            assert samples[1]["tick"] == 2
            assert samples[1]["resources"]["gold"] == 150

    def test_samples_sorted_by_tick(self) -> None:
        """Test that samples are sorted by tick."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            json_file = tmppath / "test.json"

            # Write states in reverse tick order
            states = [
                {"tick": 3, "resources": {"gold": 100, "lumber": 30}, "supply": {"used": 0, "cap": 15}, "units": []},
                {"tick": 1, "resources": {"gold": 300, "lumber": 90}, "supply": {"used": 0, "cap": 15}, "units": []},
                {"tick": 2, "resources": {"gold": 200, "lumber": 60}, "supply": {"used": 0, "cap": 15}, "units": []},
            ]

            json_file.write_text(json.dumps(states))

            parser = W3GParser()
            result = parser.parse(json_file)
            samples = parser.to_game_state_samples(result)

            assert samples[0]["tick"] == 1
            assert samples[1]["tick"] == 2
            assert samples[2]["tick"] == 3

    def test_missing_file(self) -> None:
        """Test error handling for missing files."""
        parser = W3GParser()
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("nonexistent.json"))

    def test_unsupported_format(self) -> None:
        """Test error handling for unsupported file types."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            bad_file = tmppath / "test.txt"
            bad_file.write_text("not a replay")

            parser = W3GParser()
            with pytest.raises(ValueError, match="Unsupported replay format"):
                parser.parse(bad_file)
