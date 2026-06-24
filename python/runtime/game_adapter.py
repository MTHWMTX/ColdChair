from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from python.runtime import windows_input
from python.runtime.windows_input import WindowsInputError


@dataclass
class AdapterDispatchResult:
    status: str
    reason: str = ""


class SupervisedGameAdapter:
    """Safety-gated adapter that can dispatch intents to local game input."""

    def __init__(
        self,
        *,
        allow_live_input: bool,
        required_window_substring: str = "Warcraft III",
        require_active_window: bool = True,
        confirm_before_action: bool = False,
        foreground_title_provider: Callable[[], str] | None = None,
    ) -> None:
        self.allow_live_input = allow_live_input
        self.required_window_substring = required_window_substring
        self.require_active_window = require_active_window
        self.confirm_before_action = confirm_before_action
        self._foreground_title_provider = foreground_title_provider or windows_input.get_foreground_window_title

    def dispatch(self, command: dict) -> AdapterDispatchResult:
        if not self.allow_live_input:
            return AdapterDispatchResult(status="blocked", reason="live_input_not_allowed")

        if self.require_active_window:
            title = self._foreground_title_provider()
            expected = self.required_window_substring.lower()
            if expected not in title.lower():
                return AdapterDispatchResult(
                    status="blocked",
                    reason=f"active_window_mismatch:{title or 'none'}",
                )

        if self.confirm_before_action:
            # Explicit per-action supervision gate.
            print(f"[supervised] Ready to dispatch command: {command}")
            response = input("Dispatch to live game? [y/N]: ").strip().lower()
            if response not in {"y", "yes"}:
                return AdapterDispatchResult(status="blocked", reason="user_rejected_action")

        op = str(command.get("op", ""))

        try:
            if op == "noop":
                return AdapterDispatchResult(status="executed")

            if op == "key_press":
                key = str(command.get("key", ""))
                windows_input.key_tap(key)
                return AdapterDispatchResult(status="executed")

            if op == "right_click_resource":
                # This currently requires explicit screen coordinates in command payload.
                if "x" not in command or "y" not in command:
                    return AdapterDispatchResult(
                        status="blocked",
                        reason="missing_coordinates_for_right_click_resource",
                    )
                windows_input.right_click(float(command["x"]), float(command["y"]))
                return AdapterDispatchResult(status="executed")

            if op == "attack_move":
                if "x" not in command or "y" not in command:
                    return AdapterDispatchResult(status="blocked", reason="missing_coordinates_for_attack_move")
                windows_input.key_tap("A")
                windows_input.left_click(float(command["x"]), float(command["y"]))
                return AdapterDispatchResult(status="executed")

            return AdapterDispatchResult(status="unsupported", reason=f"unsupported_op:{op}")
        except WindowsInputError as exc:
            return AdapterDispatchResult(status="blocked", reason=str(exc))
