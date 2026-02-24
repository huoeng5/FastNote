"""Dialog for editing an existing entry."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional

from PIL import Image
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from DesktopAssistant.ui.screenshot_window import ScreenshotWindow


class EditEntryDialog(QDialog):
    """Edit tags, text, note, and image settings for one entry."""

    def __init__(
        self,
        *,
        record: dict[str, Any],
        screenshot_factory: Optional[Callable[[], ScreenshotWindow]] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.record = record
        self.saved = False
        self.replacement_image_file = ""
        self.replacement_image: Optional[Image.Image] = None
        self._screenshot_window: Optional[ScreenshotWindow] = None
        self._screenshot_factory: Callable[[], ScreenshotWindow] = (
            screenshot_factory or (lambda: ScreenshotWindow(show_copy_clipboard_button=False))
        )

        self.setWindowTitle(f"编辑记录 #{record.get('id', '')}")
        self.setModal(True)
        self.setMinimumWidth(500)

        self.tags_input = QLineEdit(self)
        self.text_edit = QTextEdit(self)
        self.note_input = QLineEdit(self)
        self.image_info_label = QLabel(self)
        self.remove_image_checkbox = QCheckBox("移除当前图片", self)
        self.remove_image_checkbox.toggled.connect(self._on_remove_image_toggled)

        self.btn_select_image = QPushButton("选择新图片", self)
        self.btn_select_image.clicked.connect(self._choose_replacement_image)
        self.btn_recapture_image = QPushButton("重新截图", self)
        self.btn_recapture_image.clicked.connect(self._start_recapture)
        self.btn_clear_selected_image = QPushButton("清除选择", self)
        self.btn_clear_selected_image.clicked.connect(self._clear_replacement_image)
        self.selected_image_label = QLabel("未选择新图片", self)

        self.btn_save = QPushButton("保存", self)
        self.btn_cancel = QPushButton("取消", self)
        self.btn_save.clicked.connect(self.handle_save)
        self.btn_cancel.clicked.connect(self.reject)

        self._build_layout()
        self._load_record()

    def _build_layout(self) -> None:
        root = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow("标签", self.tags_input)
        form.addRow("内容", self.text_edit)
        form.addRow("备注", self.note_input)
        form.addRow("当前图片", self.image_info_label)
        form.addRow("", self.remove_image_checkbox)

        image_action_container = QWidget(self)
        image_action_layout = QHBoxLayout(image_action_container)
        image_action_layout.setContentsMargins(0, 0, 0, 0)
        image_action_layout.addWidget(self.btn_select_image)
        image_action_layout.addWidget(self.btn_recapture_image)
        image_action_layout.addWidget(self.btn_clear_selected_image)
        form.addRow("替换图片", image_action_container)
        form.addRow("新图片", self.selected_image_label)
        root.addLayout(form)

        actions = QHBoxLayout()
        actions.addStretch(1)
        actions.addWidget(self.btn_cancel)
        actions.addWidget(self.btn_save)
        root.addLayout(actions)
        self.setLayout(root)

    def _load_record(self) -> None:
        self.tags_input.setText(str(self.record.get("tags", "")))
        self.text_edit.setPlainText(str(self.record.get("text_content", "")))
        self.note_input.setText(str(self.record.get("note", "")))
        image_path = str(self.record.get("image_path", ""))
        self.image_info_label.setText(image_path if image_path else "无")
        self.remove_image_checkbox.setEnabled(bool(image_path))
        self.remove_image_checkbox.setChecked(False)
        self._clear_replacement_image()

    def _choose_replacement_image(self) -> None:
        selected, _ = QFileDialog.getOpenFileName(
            self,
            "选择替换图片",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.webp)",
        )
        if not selected:
            return
        self.replacement_image_file = selected
        self.replacement_image = None
        self.selected_image_label.setText(str(Path(selected)))
        if self.remove_image_checkbox.isChecked():
            self.remove_image_checkbox.setChecked(False)
        self.btn_clear_selected_image.setEnabled(True)

    def _start_recapture(self) -> None:
        if self._screenshot_window is not None:
            return
        screenshot_window = self._screenshot_factory()
        self._screenshot_window = screenshot_window
        screenshot_window.screenshot_taken.connect(self._on_screenshot_taken)
        screenshot_window.capture_canceled.connect(self._on_screenshot_canceled)
        self.setWindowModality(Qt.WindowModality.NonModal)
        self.showMinimized()
        screenshot_window.begin_capture()

    def _finish_capture_session(self) -> None:
        screenshot_window = self._screenshot_window
        self._screenshot_window = None
        if screenshot_window is not None:
            screenshot_window.close()
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _on_screenshot_taken(self, image: Image.Image) -> None:
        self.replacement_image = image.copy()
        self.replacement_image_file = ""
        width, height = self.replacement_image.size
        self.selected_image_label.setText(f"已重新截图 ({width}x{height})")
        if self.remove_image_checkbox.isChecked():
            self.remove_image_checkbox.setChecked(False)
        self.btn_clear_selected_image.setEnabled(True)
        self._finish_capture_session()

    def _on_screenshot_canceled(self) -> None:
        self._finish_capture_session()

    def _clear_replacement_image(self) -> None:
        self.replacement_image_file = ""
        self.replacement_image = None
        self.selected_image_label.setText("未选择新图片")
        self.btn_clear_selected_image.setEnabled(False)

    def _on_remove_image_toggled(self, checked: bool) -> None:
        if checked and (self.replacement_image_file or self.replacement_image is not None):
            self._clear_replacement_image()

    def get_payload(self) -> dict[str, Any]:
        image_path = str(self.record.get("image_path", ""))
        if self.remove_image_checkbox.isChecked():
            image_path = ""
        return {
            "tags": self.tags_input.text().strip(),
            "text_content": self.text_edit.toPlainText(),
            "note": self.note_input.text().strip(),
            "image_path": image_path,
            "replacement_image_file": self.replacement_image_file,
            "replacement_image": self.replacement_image,
        }

    def handle_save(self) -> None:
        payload = self.get_payload()
        if not payload["tags"]:
            QMessageBox.warning(self, "输入无效", "标签不能为空。")
            return
        has_image = bool(
            payload["image_path"]
            or payload["replacement_image_file"]
            or payload["replacement_image"] is not None
        )
        if not payload["text_content"].strip() and not has_image:
            QMessageBox.warning(self, "输入无效", "内容与图片不能同时为空。")
            return
        self.saved = True
        self.accept()

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and (
            event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ):
            self.handle_save()
            return
        super().keyPressEvent(event)
