"""UI package exports."""

from DesktopAssistant.ui.edit_entry_dialog import EditEntryDialog
from DesktopAssistant.ui.main_window import MainWindow
from DesktopAssistant.ui.mini_window import MiniWindow
from DesktopAssistant.ui.screenshot_window import ScreenshotWindow
from DesktopAssistant.ui.settings_dialog import SettingsDialog
from DesktopAssistant.ui.system_tray import SystemTrayManager

__all__ = [
    "EditEntryDialog",
    "MainWindow",
    "MiniWindow",
    "ScreenshotWindow",
    "SettingsDialog",
    "SystemTrayManager",
]
