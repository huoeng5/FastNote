"""Compact quick-entry window."""

from __future__ import annotations

from typing import Callable, Optional

from PIL import Image
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from DesktopAssistant.app_core import AssistantCore


class MiniWindow(QWidget):
    """A compact floating window for quick text and screenshot notes."""

    def __init__(
        self,
        *,
        core: AssistantCore,
        on_open_manager: Callable[[], None],
        on_start_screenshot: Callable[[], None],
    ) -> None:
        super().__init__(None)
        self.core = core
        self.on_open_manager = on_open_manager
        self.on_start_screenshot = on_start_screenshot
        self.pending_image: Optional[Image.Image] = None

        self.setWindowTitle("桌面助手 - 快速记录")
        self.setFixedSize(320, 270)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

        self.text_edit = QTextEdit(self)
        self.text_edit.setPlaceholderText("输入内容...")

        self.tags_input = QLineEdit(self)
        self.tags_input.setPlaceholderText("标签: 空格分隔，支持别名如 1=工作")

        self.note_input = QLineEdit(self)
        self.note_input.setPlaceholderText("备注: 可选")

        self.image_hint_label = QLabel("未附加截图", self)

        self.btn_screenshot = QPushButton("截图", self)
        self.btn_save = QPushButton("保存", self)
        self.btn_open_manager = QPushButton("管理", self)

        self.btn_screenshot.clicked.connect(self._handle_start_screenshot)
        self.btn_save.clicked.connect(self.handle_save)
        self.btn_open_manager.clicked.connect(self._handle_open_manager)

        self.hint_label = QLabel("", self)

        self._build_layout()
        self.refresh_hints()

    def _build_layout(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(self.text_edit)
        main_layout.addWidget(self.tags_input)
        main_layout.addWidget(self.note_input)
        main_layout.addWidget(self.image_hint_label)

        buttons = QHBoxLayout()
        buttons.addWidget(self.btn_screenshot)
        buttons.addWidget(self.btn_save)
        buttons.addWidget(self.btn_open_manager)
        main_layout.addLayout(buttons)
        main_layout.addWidget(self.hint_label)
        self.setLayout(main_layout)

    def _config_get(self, key: str, default):
        config = getattr(self.core, "config", None)
        if config is None or not hasattr(config, "get"):
            return default
        return config.get(key, default)

    def refresh_hints(self) -> None:
        shortcut_main = str(self._config_get("shortcut_main", "Alt+F1")).strip() or "Alt+F1"
        show_hints = bool(self._config_get("show_hints", True))
        self.hint_label.setText(f"快捷键: {shortcut_main} 显示/隐藏, Ctrl+Enter 保存, Esc 隐藏")
        self.hint_label.setVisible(show_hints)

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() == Qt.Key.Key_Escape:
            self.hide()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and (
            event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self.handle_save()
            return
        super().keyPressEvent(event)

    def _handle_start_screenshot(self) -> None:
        self.hide()
        self.on_start_screenshot()

    def _handle_open_manager(self) -> None:
        self.hide()
        self.on_open_manager()

    def set_pending_image(self, image: Image.Image) -> None:
        self.pending_image = image
        self.image_hint_label.setText("已附加截图，保存后写入记录")

    def clear_pending_image(self) -> None:
        self.pending_image = None
        self.image_hint_label.setText("未附加截图")

    def handle_save(self, checked: bool = False, show_message: bool = True) -> None:
        _ = checked
        text = self.text_edit.toPlainText()
        tags = self.tags_input.text()
        note = self.note_input.text()
        if not text.strip() and self.pending_image is None:
            QMessageBox.information(self, "提示", "请输入文本或附加截图后再保存。")
            return

        self.core.save_entry(text=text, tags=tags, note=note, image=self.pending_image)
        self.text_edit.clear()
        self.note_input.clear()
        self.clear_pending_image()
        if show_message:
            QMessageBox.information(self, "保存成功", "记录已保存。")
