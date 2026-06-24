from __future__ import annotations

from python.runtime.game_adapter import SupervisedGameAdapter


def test_adapter_blocks_without_live_input_opt_in() -> None:
    adapter = SupervisedGameAdapter(
        allow_live_input=False,
        required_window_substring="Warcraft III",
        require_active_window=False,
    )

    result = adapter.dispatch({"op": "key_press", "key": "T"})
    assert result.status == "blocked"
    assert result.reason == "live_input_not_allowed"


def test_adapter_blocks_on_window_title_mismatch() -> None:
    adapter = SupervisedGameAdapter(
        allow_live_input=True,
        required_window_substring="Warcraft III",
        require_active_window=True,
        foreground_title_provider=lambda: "Notepad",
    )

    result = adapter.dispatch({"op": "noop"})
    assert result.status == "blocked"
    assert result.reason.startswith("active_window_mismatch:")


def test_adapter_supports_noop_when_window_matches() -> None:
    adapter = SupervisedGameAdapter(
        allow_live_input=True,
        required_window_substring="Warcraft III",
        require_active_window=True,
        foreground_title_provider=lambda: "Warcraft III",
    )

    result = adapter.dispatch({"op": "noop"})
    assert result.status == "executed"
    assert result.reason == ""


def test_adapter_requires_coordinates_for_right_click_resource() -> None:
    adapter = SupervisedGameAdapter(
        allow_live_input=True,
        required_window_substring="Warcraft III",
        require_active_window=False,
    )

    result = adapter.dispatch({"op": "right_click_resource"})
    assert result.status == "blocked"
    assert result.reason == "missing_coordinates_for_right_click_resource"
