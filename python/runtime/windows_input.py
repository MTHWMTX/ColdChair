from __future__ import annotations

import ctypes
import platform
from ctypes import wintypes


VK_BY_KEY: dict[str, int] = {
    "A": 0x41,
    "T": 0x54,
}


class WindowsInputError(RuntimeError):
    """Raised when guarded live input cannot be performed."""


def is_windows() -> bool:
    return platform.system().lower() == "windows"


def get_foreground_window_title() -> str:
    if not is_windows():
        return ""

    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ""

    length = user32.GetWindowTextLengthW(hwnd)
    if length <= 0:
        return ""

    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, len(buf))
    return str(buf.value)


def key_tap(key: str) -> None:
    """Tap a virtual key using keybd_event (legacy but stable for this MVP)."""
    if not is_windows():
        raise WindowsInputError("Live input is only supported on Windows")

    upper = key.upper()
    if upper not in VK_BY_KEY:
        raise WindowsInputError(f"Unsupported key: {key}")

    user32 = ctypes.windll.user32
    vk = VK_BY_KEY[upper]

    KEYEVENTF_KEYUP = 0x0002
    user32.keybd_event(vk, 0, 0, 0)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)


def _set_cursor_pos(x: float, y: float) -> None:
    if not is_windows():
        raise WindowsInputError("Live input is only supported on Windows")
    ctypes.windll.user32.SetCursorPos(int(x), int(y))


def left_click(x: float, y: float) -> None:
    if not is_windows():
        raise WindowsInputError("Live input is only supported on Windows")

    _set_cursor_pos(x, y)
    user32 = ctypes.windll.user32
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


def right_click(x: float, y: float) -> None:
    if not is_windows():
        raise WindowsInputError("Live input is only supported on Windows")

    _set_cursor_pos(x, y)
    user32 = ctypes.windll.user32
    MOUSEEVENTF_RIGHTDOWN = 0x0008
    MOUSEEVENTF_RIGHTUP = 0x0010
    user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
    user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
