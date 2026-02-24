"""Global hotkey listener wrapper."""

from __future__ import annotations

from typing import Callable, Dict, Optional

try:
    from pynput import keyboard
except Exception:  # pragma: no cover - import depends on OS capabilities
    keyboard = None


def normalize_shortcut_to_pynput(shortcut: str) -> str:
    """Convert human shortcut string (Alt+F1) to pynput format."""
    token_map = {
        "alt": "<alt>",
        "ctrl": "<ctrl>",
        "control": "<ctrl>",
        "shift": "<shift>",
        "win": "<cmd>",
        "meta": "<cmd>",
        "cmd": "<cmd>",
    }
    normalized_tokens: list[str] = []
    for token in shortcut.split("+"):
        cleaned = token.strip().lower()
        if not cleaned:
            continue
        mapped = token_map.get(cleaned, cleaned)
        if mapped.startswith("f") and len(mapped) > 1 and mapped[1:].isdigit():
            mapped = f"<{mapped}>"
        normalized_tokens.append(mapped)
    return "+".join(normalized_tokens)


class GlobalHotkeyListener:
    """Manage application-wide hotkey registration with callbacks."""

    def __init__(self) -> None:
        self._callbacks: Dict[str, Callable[[], None]] = {}
        self._listener: Optional["keyboard.GlobalHotKeys"] = None

    def register(self, shortcut: str, callback: Callable[[], None]) -> None:
        normalized = normalize_shortcut_to_pynput(shortcut)
        self._callbacks[normalized] = callback

    def clear(self) -> None:
        self._callbacks.clear()
        self.stop()

    def start(self) -> None:
        if keyboard is None:
            raise RuntimeError("pynput is not available in this environment.")
        if self._listener is not None:
            self.stop()
        self._listener = keyboard.GlobalHotKeys(self._callbacks)
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
