"""Application configuration management."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional


class ConfigManager:
    """Manage persistent configuration values."""

    DEFAULTS = {
        "shortcut_main": "Alt+F1",
        "shortcut_screenshot": "Alt+F2",
        "after_screenshot": "open_mini_window",
        "default_screenshot_tags": "截图 待整理",
        "tag_alias_map": {"1": "工作"},
        "image_quality": 95,
        "mini_window_position": None,
        "mini_window_size": [300, 200],
        "main_window_position": None,
        "main_window_size": [800, 600],
        "minimize_to_tray": True,
        "auto_start": False,
        "show_hints": True,
    }

    def __init__(self, config_path: Optional[str] = None) -> None:
        if config_path:
            self.config_path = Path(config_path)
        else:
            base_dir = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "DesktopAssistant"
            self.config_path = base_dir / "config.json"

        self._config: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        if self.config_path.exists():
            try:
                loaded = json.loads(self.config_path.read_text(encoding="utf-8"))
                self._config = {**self.DEFAULTS, **loaded}
                return
            except (OSError, json.JSONDecodeError):
                pass

        self._config = self.DEFAULTS.copy()
        self.save()

    def save(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_path.write_text(
            json.dumps(self._config, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._config[key] = value
        self.save()

    def reset(self, key: Optional[str] = None) -> None:
        if key is None:
            self._config = self.DEFAULTS.copy()
        elif key in self.DEFAULTS:
            self._config[key] = self.DEFAULTS[key]
        self.save()


_CONFIG_INSTANCE: Optional[ConfigManager] = None


def get_config(config_path: Optional[str] = None) -> ConfigManager:
    global _CONFIG_INSTANCE
    if _CONFIG_INSTANCE is None or config_path is not None:
        _CONFIG_INSTANCE = ConfigManager(config_path=config_path)
    return _CONFIG_INSTANCE
