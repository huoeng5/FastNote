"""Application settings dialog."""

from __future__ import annotations

import re

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from DesktopAssistant.config import ConfigManager


class SettingsDialog(QDialog):
    """Edit core app settings."""

    def __init__(self, *, config: ConfigManager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.config = config
        self.saved = False

        self.setWindowTitle("设置")
        self.setModal(True)
        self.setFixedWidth(420)

        self.shortcut_main_input = QLineEdit(self)
        self.shortcut_screenshot_input = QLineEdit(self)
        self.default_tags_input = QLineEdit(self)
        self.tag_alias_map_input = QLineEdit(self)
        self.tag_alias_map_input.setPlaceholderText("示例: 1=工作,2=账号")

        self.after_screenshot_combo = QComboBox(self)
        self.after_screenshot_combo.addItem("打开迷你窗", "open_mini_window")
        self.after_screenshot_combo.addItem("静默保存", "silent_save")
        self.after_screenshot_combo.addItem("仅复制到剪贴板", "copy_only")

        self.btn_save = QPushButton("保存", self)
        self.btn_cancel = QPushButton("取消", self)
        self.btn_save.clicked.connect(self.handle_save)
        self.btn_cancel.clicked.connect(self.reject)

        self._build_layout()
        self._load_values()

    def _build_layout(self) -> None:
        root = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow("主快捷键", self.shortcut_main_input)
        form.addRow("截图快捷键", self.shortcut_screenshot_input)
        form.addRow("截图后行为", self.after_screenshot_combo)
        form.addRow("默认截图标签", self.default_tags_input)
        form.addRow("标签别名映射", self.tag_alias_map_input)
        root.addLayout(form)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(self.btn_cancel)
        actions.addWidget(self.btn_save)
        root.addLayout(actions)
        self.setLayout(root)

    def _load_values(self) -> None:
        self.shortcut_main_input.setText(str(self.config.get("shortcut_main", "Alt+F1")))
        self.shortcut_screenshot_input.setText(str(self.config.get("shortcut_screenshot", "Alt+F2")))
        self.default_tags_input.setText(str(self.config.get("default_screenshot_tags", "截图 待整理")))
        behavior = str(self.config.get("after_screenshot", "open_mini_window"))
        index = self.after_screenshot_combo.findData(behavior)
        if index < 0:
            index = 0
        self.after_screenshot_combo.setCurrentIndex(index)
        alias_map = self.config.get("tag_alias_map", {"1": "工作"})
        if isinstance(alias_map, dict):
            alias_text = ",".join(f"{str(k).strip()}={str(v).strip()}" for k, v in alias_map.items())
            self.tag_alias_map_input.setText(alias_text)
        else:
            self.tag_alias_map_input.setText("1=工作")

    @staticmethod
    def _parse_alias_map(text: str) -> dict[str, str]:
        if not text.strip():
            return {}
        pairs = re.split(r"[,，;\n]+", text.strip())
        mapping: dict[str, str] = {}
        for pair in pairs:
            item = pair.strip()
            if not item:
                continue
            if "=" not in item:
                raise ValueError(f"invalid alias pair: {item}")
            left, right = item.split("=", 1)
            key = left.strip()
            value = right.strip()
            if not key or not value:
                raise ValueError(f"invalid alias pair: {item}")
            mapping[key] = value
        return mapping

    def handle_save(self) -> None:
        shortcut_main = self.shortcut_main_input.text().strip()
        shortcut_screenshot = self.shortcut_screenshot_input.text().strip()
        default_tags = self.default_tags_input.text().strip()
        behavior = str(self.after_screenshot_combo.currentData())
        alias_map_text = self.tag_alias_map_input.text().strip()

        if not shortcut_main or not shortcut_screenshot:
            QMessageBox.warning(self, "输入无效", "快捷键不能为空。")
            return

        if not default_tags:
            QMessageBox.warning(self, "输入无效", "默认截图标签不能为空。")
            return

        try:
            alias_map = self._parse_alias_map(alias_map_text)
        except ValueError:
            QMessageBox.warning(self, "输入无效", "标签别名映射格式错误，请使用 1=工作,2=账号。")
            return

        self.config.set("shortcut_main", shortcut_main)
        self.config.set("shortcut_screenshot", shortcut_screenshot)
        self.config.set("after_screenshot", behavior)
        self.config.set("default_screenshot_tags", default_tags)
        self.config.set("tag_alias_map", alias_map)

        self.saved = True
        self.accept()

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and (
            event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self.handle_save()
            return
        super().keyPressEvent(event)
