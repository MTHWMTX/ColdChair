from __future__ import annotations

import json
from pathlib import Path

from python.runtime.run_self_play import main
from python.runtime.self_play import SelfPlayArena


def test_self_play_runs_for_configured_ticks() -> None:
    arena = SelfPlayArena()

    summary, logs = arena.run(ticks=12)

    assert summary.ticks <= 12
    assert len(logs) == summary.ticks
    assert summary.winner in {"bot_a", "bot_b", "draw"}


def test_self_play_cli_writes_report(tmp_path: Path, monkeypatch) -> None:
    out_path = tmp_path / "self_play_report.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "run_self_play.py",
            "--ticks",
            "10",
            "--out",
            str(out_path),
        ],
    )

    code = main()
    assert code == 0
    assert out_path.exists()

    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert "summary" in payload
    assert "logs" in payload
    assert payload["summary"]["winner"] in {"bot_a", "bot_b", "draw"}


def test_self_play_respects_custom_initial_state() -> None:
    arena = SelfPlayArena()
    initial = {
        "tick": 0,
        "players": {
            "bot_a": {
                "resources": {"gold": 500, "lumber": 100},
                "supply": {"used": 8, "cap": 12},
                "units": [
                    {"id": "a1", "type": "footman", "hp": 420.0, "position": {"x": 10.0, "y": 10.0}},
                    {"id": "a2", "type": "footman", "hp": 420.0, "position": {"x": 11.0, "y": 11.0}},
                    {"id": "a3", "type": "footman", "hp": 420.0, "position": {"x": 12.0, "y": 12.0}},
                    {"id": "a4", "type": "footman", "hp": 420.0, "position": {"x": 13.0, "y": 13.0}},
                    {"id": "a5", "type": "footman", "hp": 420.0, "position": {"x": 14.0, "y": 14.0}},
                    {"id": "a6", "type": "footman", "hp": 420.0, "position": {"x": 15.0, "y": 15.0}},
                    {"id": "a7", "type": "footman", "hp": 420.0, "position": {"x": 16.0, "y": 16.0}},
                    {"id": "a8", "type": "footman", "hp": 420.0, "position": {"x": 17.0, "y": 17.0}},
                ],
            },
            "bot_b": {
                "resources": {"gold": 500, "lumber": 100},
                "supply": {"used": 8, "cap": 12},
                "units": [
                    {"id": "b1", "type": "footman", "hp": 420.0, "position": {"x": 20.0, "y": 20.0}},
                    {"id": "b2", "type": "footman", "hp": 420.0, "position": {"x": 21.0, "y": 21.0}},
                    {"id": "b3", "type": "footman", "hp": 420.0, "position": {"x": 22.0, "y": 22.0}},
                    {"id": "b4", "type": "footman", "hp": 420.0, "position": {"x": 23.0, "y": 23.0}},
                    {"id": "b5", "type": "footman", "hp": 420.0, "position": {"x": 24.0, "y": 24.0}},
                    {"id": "b6", "type": "footman", "hp": 420.0, "position": {"x": 25.0, "y": 25.0}},
                    {"id": "b7", "type": "footman", "hp": 420.0, "position": {"x": 26.0, "y": 26.0}},
                    {"id": "b8", "type": "footman", "hp": 420.0, "position": {"x": 27.0, "y": 27.0}},
                ],
            },
        },
    }

    summary, logs = arena.run(ticks=15, initial_state=initial)

    assert summary.ticks <= 15
    assert len(logs) == summary.ticks
    assert all("bot_a" in log and "bot_b" in log for log in logs)


def test_self_play_accepts_standard_sample_state_format() -> None:
    arena = SelfPlayArena()
    sample_like = {
        "tick": 1,
        "resources": {"gold": 200, "lumber": 60},
        "supply": {"used": 10, "cap": 20},
        "units": [
            {"id": "s1", "owner": "self", "type": "peasant", "hp": 100, "position": {"x": 1, "y": 1}},
            {"id": "e1", "owner": "enemy", "type": "peasant", "hp": 100, "position": {"x": 2, "y": 2}},
        ],
    }

    summary, logs = arena.run(ticks=6, initial_state=sample_like)

    assert summary.ticks <= 6
    assert len(logs) == summary.ticks
    assert summary.winner in {"bot_a", "bot_b", "draw"}
