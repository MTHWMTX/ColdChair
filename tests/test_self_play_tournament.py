from __future__ import annotations

import json
from pathlib import Path

from python.runtime.run_self_play_tournament import main
from python.runtime.self_play_tournament import SelfPlayTournament


def test_tournament_runs_two_games_per_round() -> None:
    tournament = SelfPlayTournament()
    summary, matches = tournament.run(rounds=3, ticks=10)

    assert summary.rounds == 3
    assert summary.total_games == 6
    assert len(matches) == 6
    assert summary.bot_a_wins + summary.bot_b_wins + summary.draws == 6


def test_tournament_cli_writes_report(tmp_path: Path, monkeypatch) -> None:
    sample_path = tmp_path / "samples.json"
    out_path = tmp_path / "tournament.json"

    sample_path.write_text(
        """[
  {
    \"tick\": 1,
    \"resources\": {\"gold\": 200, \"lumber\": 60},
    \"supply\": {\"used\": 10, \"cap\": 20},
    \"units\": [
      {\"id\": \"a1\", \"owner\": \"self\", \"type\": \"peasant\", \"hp\": 100, \"position\": {\"x\": 1, \"y\": 1}},
      {\"id\": \"b1\", \"owner\": \"enemy\", \"type\": \"peasant\", \"hp\": 100, \"position\": {\"x\": 2, \"y\": 2}}
    ]
  }
]""",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "run_self_play_tournament.py",
            "--samples",
            str(sample_path),
            "--rounds",
            "4",
            "--ticks",
            "12",
            "--bot-a-label",
            "candidate",
            "--bot-b-label",
            "baseline",
            "--out",
            str(out_path),
        ],
    )

    code = main()
    assert code == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["summary"]["total_games"] == 8
    assert len(payload["matches"]) == 8
    assert "candidate" in payload["summary"]["bot_a_label"]
    assert "baseline" in payload["summary"]["bot_b_label"]
