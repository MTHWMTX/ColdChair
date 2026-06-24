from __future__ import annotations

from pathlib import Path

from python.policy.decision_engine import ActionIntent
from python.runtime.targeting import Bounds, CommandEnricher, TargetProfile


def test_attack_move_world_to_screen_mapping() -> None:
    profile = TargetProfile(
        world_bounds=Bounds(min_x=0.0, max_x=128.0, min_y=0.0, max_y=128.0),
        screen_bounds=Bounds(min_x=400.0, max_x=1500.0, min_y=200.0, max_y=900.0),
    )
    enricher = CommandEnricher(profile)

    command = {"op": "attack_move", "x": 64.0, "y": 64.0}
    result = enricher.enrich_command(command, ActionIntent(type="attack_move"), state={})

    assert result["x"] == 950.0
    assert result["y"] == 550.0


def test_resource_point_from_profile_when_missing_in_command() -> None:
    profile = TargetProfile(resource_points=[{"x": 900.0, "y": 600.0}])
    enricher = CommandEnricher(profile)

    command = {"op": "right_click_resource"}
    result = enricher.enrich_command(command, ActionIntent(type="gather_resources"), state={})

    assert result["x"] == 900.0
    assert result["y"] == 600.0


def test_resource_node_from_state_with_mapping() -> None:
    profile = TargetProfile(
        world_bounds=Bounds(min_x=0.0, max_x=128.0, min_y=0.0, max_y=128.0),
        screen_bounds=Bounds(min_x=400.0, max_x=1500.0, min_y=200.0, max_y=900.0),
    )
    enricher = CommandEnricher(profile)

    state = {
        "resource_nodes": [
            {"type": "gold_mine", "position": {"x": 32.0, "y": 96.0}},
        ]
    }

    command = {"op": "right_click_resource"}
    result = enricher.enrich_command(command, ActionIntent(type="gather_resources"), state=state)

    assert result["x"] == 675.0
    assert result["y"] == 725.0


def test_target_profile_from_file() -> None:
    profile_path = Path("examples/live_target_profile.json")
    profile = TargetProfile.from_file(profile_path)

    assert profile.world_bounds is not None
    assert profile.screen_bounds is not None
    assert profile.resource_points is not None
    assert profile.attack_move_points is not None
