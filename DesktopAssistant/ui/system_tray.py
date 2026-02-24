"""System tray integration."""

from __future__ import annotations

from typing import Callable

from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QStyle, QSystemTrayIcon


class SystemTrayManager:
    """Create tray icon and menu actions."""

    def __init__(
        self,
        *,
        on_toggle_mini: Callable[[], None],
        on_open_manager: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        app = QApplication.instance()
        if app is None:
            raise RuntimeError("QApplication is required before creating system tray.")

        icon = app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray = QSystemTrayIcon(icon, app)
        self.tray.setToolTip("桌面助手")

        menu = QMenu()
        action_toggle = QAction("显示/隐藏快速窗口", menu)
        action_manage = QAction("打开管理窗口", menu)
        action_quit = QAction("退出", menu)

        action_toggle.triggered.connect(on_toggle_mini)
        action_manage.triggered.connect(on_open_manager)
        action_quit.triggered.connect(on_quit)

        menu.addAction(action_toggle)
        menu.addAction(action_manage)
        menu.addSeparator()
        menu.addAction(action_quit)
        self.tray.setContextMenu(menu)

        self.tray.activated.connect(self._on_activated)
        self._on_toggle_mini = on_toggle_mini

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._on_toggle_mini()

    def show(self) -> None:
        self.tray.show()

    def hide(self) -> None:
        self.tray.hide()
