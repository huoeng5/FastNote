"""Desktop assistant application bootstrap."""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Optional

from PIL import Image
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QApplication

from DesktopAssistant.app_core import AssistantCore
from DesktopAssistant.ui.main_window import MainWindow
from DesktopAssistant.ui.mini_window import MiniWindow
from DesktopAssistant.ui.screenshot_window import ScreenshotWindow
from DesktopAssistant.ui.settings_dialog import SettingsDialog
from DesktopAssistant.ui.system_tray import SystemTrayManager
from DesktopAssistant.utils.hotkey_listener import GlobalHotkeyListener


class _ThreadBridge(QObject):
    toggle_mini_requested = pyqtSignal()
    screenshot_requested = pyqtSignal()


def _pil_to_qimage(image: Image.Image) -> QImage:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    qimage = QImage.fromData(buffer.getvalue(), "PNG")
    return qimage


class DesktopAssistantApplication:
    """Compose core services and UI components."""

    def __init__(self, *, base_dir: Optional[Path] = None, test_mode: bool = False) -> None:
        self.qt_app = QApplication.instance() or QApplication(sys.argv)
        self.qt_app.setQuitOnLastWindowClosed(False)

        self.core = AssistantCore(base_dir=base_dir)
        self.bridge = _ThreadBridge()
        self.bridge.toggle_mini_requested.connect(self.toggle_mini_window)
        self.bridge.screenshot_requested.connect(self.start_screenshot)

        self.main_window = MainWindow(
            core=self.core,
            on_open_mini=self.show_mini_window,
            on_open_settings=self.open_settings_dialog,
        )
        self.mini_window = MiniWindow(
            core=self.core,
            on_open_manager=self.show_main_window,
            on_start_screenshot=self.start_screenshot,
        )
        self.screenshot_window = ScreenshotWindow()
        self.screenshot_window.screenshot_taken.connect(self._on_screenshot_taken)
        self.screenshot_window.capture_canceled.connect(self._on_screenshot_canceled)

        self.tray: Optional[SystemTrayManager] = None
        self.hotkeys: Optional[GlobalHotkeyListener] = None

        if not test_mode:
            self._setup_tray()
            self._setup_hotkeys()

    def _setup_tray(self) -> None:
        self.tray = SystemTrayManager(
            on_toggle_mini=self.toggle_mini_window,
            on_open_manager=self.show_main_window,
            on_quit=self.quit,
        )
        self.tray.show()

    def _setup_hotkeys(self) -> None:
        if self.hotkeys is not None:
            self.hotkeys.stop()
        self.hotkeys = GlobalHotkeyListener()
        self.hotkeys.register(
            str(self.core.config.get("shortcut_main", "Alt+F1")),
            lambda: self.bridge.toggle_mini_requested.emit(),
        )
        self.hotkeys.register(
            str(self.core.config.get("shortcut_screenshot", "Alt+F2")),
            lambda: self.bridge.screenshot_requested.emit(),
        )
        try:
            self.hotkeys.start()
        except Exception as exc:  # pragma: no cover - depends on desktop environment
            print(f"[warn] hotkey listener failed: {exc}")

    def open_settings_dialog(self) -> None:
        dialog = SettingsDialog(config=self.core.config, parent=self.main_window)
        dialog.exec()
        if not dialog.saved:
            return
        self.mini_window.refresh_hints()
        if self.hotkeys is not None:
            self._setup_hotkeys()

    def show_mini_window(self) -> None:
        self.mini_window.show()
        self.mini_window.raise_()
        self.mini_window.activateWindow()

    def hide_mini_window(self) -> None:
        self.mini_window.hide()

    def toggle_mini_window(self) -> None:
        if self.mini_window.isVisible():
            self.hide_mini_window()
        else:
            self.show_mini_window()

    def show_main_window(self) -> None:
        self.main_window.refresh_tag_filter()
        self.main_window.refresh_records()
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()

    def start_screenshot(self) -> None:
        self.hide_mini_window()
        self.screenshot_window.begin_capture()

    def _copy_image_to_clipboard(self, image: Image.Image) -> None:
        clipboard = self.qt_app.clipboard()
        qimage = _pil_to_qimage(image)
        clipboard.setImage(qimage)

    def _on_screenshot_taken(self, image: Image.Image) -> None:
        behavior = str(self.core.config.get("after_screenshot", "open_mini_window"))
        default_tags = str(self.core.config.get("default_screenshot_tags", "截图 待整理"))

        if behavior == "copy_only":
            self._copy_image_to_clipboard(image)
            self.show_mini_window()
            return

        if behavior == "silent_save":
            self.core.save_entry(text="", tags=default_tags, image=image)
            self.main_window.refresh_tag_filter()
            self.main_window.refresh_records()
            return

        if not self.mini_window.tags_input.text().strip():
            self.mini_window.tags_input.setText(default_tags)
        self.mini_window.set_pending_image(image)
        self.show_mini_window()

    def _on_screenshot_canceled(self) -> None:
        self.show_mini_window()

    def run(self) -> int:
        self.show_mini_window()
        return self.qt_app.exec()

    def quit(self) -> None:
        if self.hotkeys is not None:
            self.hotkeys.stop()
        if self.tray is not None:
            self.tray.hide()
        self.qt_app.quit()


def main() -> int:
    app = DesktopAssistantApplication()
    return app.run()


if __name__ == "__main__":
    raise SystemExit(main())
