"""Main management window for browsing and editing records."""

from __future__ import annotations

import html
import re
from typing import Callable, Optional

from PIL import Image, UnidentifiedImageError
from PyQt6.QtCore import QEventLoop, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QBrush, QColor, QPixmap
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from DesktopAssistant.app_core import AssistantCore
from DesktopAssistant.ui.edit_entry_dialog import EditEntryDialog


class ClickableLabel(QLabel):
    clicked = pyqtSignal()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    """Record management interface."""

    def __init__(
        self,
        *,
        core: AssistantCore,
        on_open_mini: Callable[[], None],
        on_open_settings: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(None)
        self.core = core
        self.on_open_mini = on_open_mini
        self.on_open_settings = on_open_settings

        self.setWindowTitle("桌面助手 - 管理")
        self.resize(900, 620)
        self.page_size = 20
        self.current_page = 1
        self._total_count = 0
        self._total_pages = 1
        self._has_next_page = False
        self._current_image_absolute_path: Optional[str] = None

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("搜索标题/内容/标签...")
        self.search_input.textChanged.connect(self._on_filters_changed)

        self.tag_filter = QComboBox(self)
        self.tag_filter.addItem("全部标签", "")
        self.tag_filter.currentIndexChanged.connect(self._on_filters_changed)

        self.type_filter = QComboBox(self)
        self.type_filter.addItem("全部类型", "")
        self.type_filter.addItem("纯文本", "text")
        self.type_filter.addItem("截图", "screenshot")
        self.type_filter.addItem("混合", "mixed")
        self.type_filter.currentIndexChanged.connect(self._on_filters_changed)

        self.btn_new = QPushButton("新建", self)
        self.btn_settings = QPushButton("设置", self)
        self.btn_new.clicked.connect(self.on_open_mini)
        self.btn_settings.clicked.connect(self._open_settings)

        self.record_list = QListWidget(self)
        self.record_list.setWordWrap(True)
        self.record_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.record_list.currentItemChanged.connect(self._show_selected_detail)

        self.detail_text = QTextEdit(self)
        self.detail_text.setReadOnly(True)

        self.image_label = ClickableLabel("无图片", self)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setMinimumHeight(160)
        self.image_label.clicked.connect(self._open_image_preview)

        self.btn_delete = QPushButton("删除", self)
        self.btn_delete.clicked.connect(self.handle_delete_selected)
        self.btn_edit = QPushButton("编辑", self)
        self.btn_edit.clicked.connect(self.handle_edit_selected)
        self.btn_export = QPushButton("导出Excel", self)
        self.btn_export.clicked.connect(self.handle_export_excel)
        self.btn_first_page = QPushButton("<<", self)
        self.btn_first_page.clicked.connect(self._on_first_page)
        self.btn_prev_page = QPushButton("<", self)
        self.btn_prev_page.clicked.connect(self._on_prev_page)
        self.page_label = QLabel("Page 1", self)
        self.page_jump_input = QLineEdit(self)
        self.page_jump_input.setFixedWidth(70)
        self.page_jump_input.setPlaceholderText("页码")
        self.page_jump_input.returnPressed.connect(self._on_jump_page)
        self.btn_jump_page = QPushButton("跳转", self)
        self.btn_jump_page.clicked.connect(self._on_jump_page)
        self.btn_next_page = QPushButton(">", self)
        self.btn_next_page.clicked.connect(self._on_next_page)
        self.btn_last_page = QPushButton(">>", self)
        self.btn_last_page.clicked.connect(self._on_last_page)
        self.page_size_combo = QComboBox(self)
        self.page_size_combo.addItem("20/页", 20)
        self.page_size_combo.addItem("50/页", 50)
        self.page_size_combo.addItem("100/页", 100)
        page_size_index = self.page_size_combo.findData(self.page_size)
        if page_size_index >= 0:
            self.page_size_combo.setCurrentIndex(page_size_index)
        self.page_size_combo.currentIndexChanged.connect(self._on_page_size_changed)

        self.status_label = QLabel("共 0 条记录", self)

        self._build_layout()
        self._build_menu()
        self.refresh_tag_filter()
        self.refresh_records()

    def _build_layout(self) -> None:
        central = QWidget(self)
        root = QVBoxLayout(central)

        toolbar = QHBoxLayout()
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(self.tag_filter)
        toolbar.addWidget(self.type_filter)
        toolbar.addWidget(self.btn_new)
        toolbar.addWidget(self.btn_settings)
        root.addLayout(toolbar)

        content = QHBoxLayout()
        content.addWidget(self.record_list, 2)

        right = QVBoxLayout()
        right.addWidget(self.detail_text, 3)
        right.addWidget(self.image_label, 2)
        right.addWidget(self.btn_edit)
        right.addWidget(self.btn_delete)
        right.addWidget(self.btn_export)
        content.addLayout(right, 3)
        root.addLayout(content)

        pagination = QHBoxLayout()
        pagination.addStretch(1)
        pagination.addWidget(self.btn_first_page)
        pagination.addWidget(self.btn_prev_page)
        pagination.addWidget(self.page_label)
        pagination.addWidget(self.page_jump_input)
        pagination.addWidget(self.btn_jump_page)
        pagination.addWidget(self.btn_next_page)
        pagination.addWidget(self.btn_last_page)
        pagination.addWidget(self.page_size_combo)
        pagination.addStretch(1)
        root.addLayout(pagination)

        root.addWidget(self.status_label)
        self.setCentralWidget(central)

    def _build_menu(self) -> None:
        menu = self.menuBar().addMenu("文件")
        action_new = QAction("新建记录", self)
        action_new.triggered.connect(self.on_open_mini)
        menu.addAction(action_new)

        action_refresh = QAction("刷新", self)
        action_refresh.triggered.connect(self.refresh_records)
        menu.addAction(action_refresh)

        action_edit = QAction("编辑记录", self)
        action_edit.triggered.connect(self.handle_edit_selected)
        menu.addAction(action_edit)

        action_export = QAction("导出Excel", self)
        action_export.triggered.connect(self.handle_export_excel)
        menu.addAction(action_export)

    def _open_settings(self) -> None:
        if self.on_open_settings is not None:
            self.on_open_settings()
            return
        self._open_settings_placeholder()

    def _open_settings_placeholder(self) -> None:
        QMessageBox.information(self, "设置", "设置面板将在后续版本补充。")

    def refresh_tag_filter(self) -> None:
        current_data = self.tag_filter.currentData()
        self.tag_filter.blockSignals(True)
        self.tag_filter.clear()
        self.tag_filter.addItem("全部标签", "")
        for tag in self.core.available_tags():
            self.tag_filter.addItem(tag, tag)
        index = self.tag_filter.findData(current_data)
        if index >= 0:
            self.tag_filter.setCurrentIndex(index)
        self.tag_filter.blockSignals(False)

    def _on_filters_changed(self, *_args) -> None:
        self.current_page = 1
        self.refresh_records()

    def _on_prev_page(self) -> None:
        if self.current_page <= 1:
            return
        self.current_page -= 1
        self.refresh_records()

    def _on_first_page(self) -> None:
        if self.current_page <= 1:
            return
        self.current_page = 1
        self.refresh_records()

    def _on_next_page(self) -> None:
        if self.current_page >= self._total_pages:
            return
        self.current_page += 1
        self.refresh_records()

    def _on_last_page(self) -> None:
        if self.current_page >= self._total_pages:
            return
        self.current_page = self._total_pages
        self.refresh_records()

    def _on_jump_page(self) -> None:
        raw_text = self.page_jump_input.text().strip()
        if not raw_text:
            self.page_jump_input.setText(str(self.current_page))
            return

        try:
            target_page = int(raw_text)
        except ValueError:
            self.page_jump_input.setText(str(self.current_page))
            return

        target_page = max(1, min(target_page, self._total_pages))
        self.page_jump_input.setText(str(target_page))
        if target_page == self.current_page:
            return
        self.current_page = target_page
        self.refresh_records()

    def _on_page_size_changed(self, _index: int) -> None:
        selected_size = self.page_size_combo.currentData()
        try:
            new_page_size = int(selected_size)
        except (TypeError, ValueError):
            return
        if new_page_size == self.page_size:
            return
        self.page_size = new_page_size
        self.current_page = 1
        self.refresh_records()

    def _update_pagination_controls(self, current_count: int) -> None:
        self.btn_first_page.setEnabled(self.current_page > 1)
        self.btn_prev_page.setEnabled(self.current_page > 1)
        self.btn_next_page.setEnabled(self.current_page < self._total_pages)
        self.btn_last_page.setEnabled(self.current_page < self._total_pages)
        self.page_label.setText(f"第 {self.current_page}/{self._total_pages} 页")
        self.page_jump_input.setText(str(self.current_page))
        self.page_jump_input.setPlaceholderText(f"1-{self._total_pages}")
        self.btn_jump_page.setEnabled(self._total_count > 0)
        if current_count == 0 and self.current_page == 1:
            self.btn_next_page.setEnabled(False)
            self.btn_last_page.setEnabled(False)

    def _update_status_label(self, current_count: int) -> None:
        if self._total_count <= 0 or current_count <= 0:
            start = 0
            end = 0
        else:
            start = (self.current_page - 1) * self.page_size + 1
            end = start + current_count - 1
        self.status_label.setText(f"共 {self._total_count} 条记录 | 当前显示 {start}-{end}/{self._total_count}")

    def _count_filtered_records(
        self,
        *,
        search_query: str,
        tag: Optional[str],
        content_type: Optional[str],
    ) -> int:
        if hasattr(self.core, "count_entries"):
            try:
                return int(
                    self.core.count_entries(
                        search_query=search_query,
                        tag=tag or None,
                        content_type=content_type or None,
                    )
                )
            except Exception:
                pass

        records = self.core.list_entries(
            search_query=search_query,
            tag=tag or None,
            content_type=content_type or None,
            limit=None,
            offset=0,
        )
        return len(records)

    @staticmethod
    def _build_list_summary(record: dict) -> str:
        summary_text = " ".join(str(record.get("note", "")).split())
        if not summary_text:
            summary_text = " ".join(str(record.get("text_content", "")).split())

        if summary_text:
            if len(summary_text) > 60:
                summary_text = summary_text[:57] + "..."
        elif str(record.get("image_path", "")).strip():
            summary_text = "[Image]"
        else:
            summary_text = "(empty)"

        tags = str(record.get("tags", ""))
        created_at = str(record.get("created_at", ""))
        return f"{summary_text}\n{tags}  {created_at}"

    @staticmethod
    def _highlight_html(text: str, keyword: str) -> str:
        source = str(text or "")
        query = str(keyword or "").strip()
        if not query:
            return html.escape(source)

        pattern = re.compile(re.escape(query), re.IGNORECASE)
        parts: list[str] = []
        start = 0
        for match in pattern.finditer(source):
            parts.append(html.escape(source[start : match.start()]))
            parts.append(
                "<span style='background-color:#FFE58A;color:#000;font-weight:600;'>"
                f"{html.escape(match.group(0))}</span>"
            )
            start = match.end()
        parts.append(html.escape(source[start:]))
        return "".join(parts)

    def _build_record_item_widget(self, summary: str, search_query: str) -> QWidget:
        lines = summary.splitlines()
        primary_line = lines[0] if lines else ""
        meta_line = lines[1] if len(lines) > 1 else ""

        container = QWidget(self.record_list)
        container.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)

        primary_label = QLabel(container)
        primary_label.setObjectName("summaryLinePrimary")
        primary_label.setWordWrap(True)
        primary_label.setTextFormat(Qt.TextFormat.RichText)
        primary_label.setText(self._highlight_html(primary_line, search_query))
        primary_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        meta_label = QLabel(container)
        meta_label.setObjectName("summaryLineMeta")
        meta_label.setWordWrap(True)
        meta_label.setTextFormat(Qt.TextFormat.RichText)
        meta_label.setStyleSheet("color: #666666;")
        meta_label.setText(self._highlight_html(meta_line, search_query))
        meta_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)

        layout.addWidget(primary_label)
        layout.addWidget(meta_label)
        return container

    def refresh_records(self) -> None:
        search_query = self.search_input.text().strip()
        tag = self.tag_filter.currentData()
        content_type = self.type_filter.currentData()

        self._total_count = self._count_filtered_records(
            search_query=search_query,
            tag=tag,
            content_type=content_type,
        )
        self._total_pages = max(1, (self._total_count + self.page_size - 1) // self.page_size)
        if self.current_page > self._total_pages:
            self.current_page = self._total_pages

        offset = (self.current_page - 1) * self.page_size

        records = self.core.list_entries(
            search_query=search_query,
            tag=tag or None,
            content_type=content_type or None,
            limit=self.page_size,
            offset=offset,
        )

        # If current page became empty after filtering/deletion, fall back to previous page.
        if not records and self.current_page > 1:
            self.current_page -= 1
            offset = (self.current_page - 1) * self.page_size
            records = self.core.list_entries(
                search_query=search_query,
                tag=tag or None,
                content_type=content_type or None,
                limit=self.page_size,
                offset=offset,
            )

        self._has_next_page = self.current_page < self._total_pages
        self.record_list.clear()
        for record in records:
            summary = self._build_list_summary(record)
            item = QListWidgetItem(summary)
            item.setForeground(QBrush(QColor(0, 0, 0, 0)))
            item.setSizeHint(QSize(0, 44))
            item.setData(Qt.ItemDataRole.UserRole, record)
            self.record_list.addItem(item)
            self.record_list.setItemWidget(
                item,
                self._build_record_item_widget(summary, search_query),
            )

        self._update_pagination_controls(len(records))
        self._update_status_label(len(records))
        if records:
            self.record_list.setCurrentRow(0)
        else:
            self.detail_text.clear()
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText("无图片")
            self.image_label.setCursor(Qt.CursorShape.ArrowCursor)
            self._current_image_absolute_path = None

    def _show_selected_detail(self, current: Optional[QListWidgetItem], _previous) -> None:
        if current is None:
            return
        record = current.data(Qt.ItemDataRole.UserRole)
        if not record:
            return

        detail = [
            f"创建时间: {record['created_at']}",
            "",
            record.get("text_content", ""),
            "",
            f"备注: {record.get('note', '')}",
        ]
        self.detail_text.setPlainText("\n".join(detail))

        image_path = record.get("image_path", "")
        self._current_image_absolute_path = None
        if image_path and hasattr(self.core, "image_manager"):
            try:
                absolute_path = self.core.image_manager.get_absolute_path(image_path)
                pixmap = QPixmap(str(absolute_path))
            except Exception:
                pixmap = QPixmap()
            if not pixmap.isNull():
                scaled = pixmap.scaled(
                    260,
                    160,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self.image_label.setPixmap(scaled)
                self.image_label.setText("")
                self._current_image_absolute_path = str(absolute_path)
                self.image_label.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                self.image_label.setPixmap(QPixmap())
                self.image_label.setText("图片加载失败")
                self.image_label.setCursor(Qt.CursorShape.ArrowCursor)
        else:
            self.image_label.setPixmap(QPixmap())
            self.image_label.setText("无图片")
            self.image_label.setCursor(Qt.CursorShape.ArrowCursor)

    def _open_image_preview(self) -> None:
        if not self._current_image_absolute_path:
            return

        pixmap = QPixmap(self._current_image_absolute_path)
        if pixmap.isNull():
            QMessageBox.warning(self, "预览失败", "无法加载图片。")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("图片预览")
        dialog.resize(900, 700)

        layout = QVBoxLayout(dialog)
        preview_label = QLabel(dialog)
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setPixmap(pixmap)
        layout.addWidget(preview_label)

        dialog.exec()

    def handle_delete_selected(self, checked: bool = False, confirm: bool = True) -> None:
        _ = checked
        selected_items = self.record_list.selectedItems()
        if not selected_items:
            current_item = self.record_list.currentItem()
            if current_item is not None:
                selected_items = [current_item]

        records_to_delete: list[dict] = []
        for item in selected_items:
            record = item.data(Qt.ItemDataRole.UserRole)
            if record:
                records_to_delete.append(record)

        if not records_to_delete:
            return

        if confirm:
            if len(records_to_delete) == 1:
                prompt = f"删除记录 #{records_to_delete[0]['id']} ?"
            else:
                prompt = f"删除已选中的 {len(records_to_delete)} 条记录?"
            answer = QMessageBox.question(self, "确认删除", prompt)
            if answer != QMessageBox.StandardButton.Yes:
                return

        for record in records_to_delete:
            self.core.delete_entry(record["id"], remove_image=True)
        self.refresh_tag_filter()
        self.refresh_records()

    def _select_record_by_id(self, record_id: int) -> None:
        for index in range(self.record_list.count()):
            item = self.record_list.item(index)
            record = item.data(Qt.ItemDataRole.UserRole)
            if record and record.get("id") == record_id:
                self.record_list.setCurrentRow(index)
                break

    def _execute_dialog(self, dialog) -> int:
        # Keep tests compatible with lightweight fake dialogs that only implement exec().
        if not isinstance(dialog, QDialog):
            return int(dialog.exec())

        loop = QEventLoop(self)
        dialog.finished.connect(loop.quit)
        dialog.setWindowModality(Qt.WindowModality.WindowModal)
        dialog.setModal(False)
        dialog.show()
        dialog.raise_()
        dialog.activateWindow()
        loop.exec()
        return int(dialog.result())

    def handle_edit_selected(self, checked: bool = False, show_message: bool = True) -> None:
        _ = checked
        item = self.record_list.currentItem()
        if item is None:
            return
        record = item.data(Qt.ItemDataRole.UserRole)
        if not record:
            return

        dialog = EditEntryDialog(record=record, parent=self)
        if self._execute_dialog(dialog) != int(QDialog.DialogCode.Accepted):
            return

        payload = dialog.get_payload()
        replacement_image = payload.pop("replacement_image", None)
        replacement_image_file = str(payload.pop("replacement_image_file", "")).strip()
        if replacement_image is not None:
            payload["image"] = replacement_image
        elif replacement_image_file:
            try:
                with Image.open(replacement_image_file) as replacement_image:
                    payload["image"] = replacement_image.copy()
            except (OSError, UnidentifiedImageError):
                QMessageBox.warning(self, "替换失败", "无法读取所选图片，请重新选择。")
                return

        updated = self.core.update_entry(record["id"], **payload)
        if not updated:
            QMessageBox.warning(self, "更新失败", "未能更新记录，请重试。")
            return

        self.refresh_tag_filter()
        self.refresh_records()
        self._select_record_by_id(record["id"])
        if show_message:
            QMessageBox.information(self, "保存成功", "记录已更新。")

    def handle_export_excel(self, checked: bool = False, export_path=None, show_message: bool = True):
        _ = checked
        target = export_path
        if target is None:
            selected, _ = QFileDialog.getSaveFileName(
                self,
                "导出 Excel",
                "desktop_assistant_export.xlsx",
                "Excel Files (*.xlsx)",
            )
            if not selected:
                return None
            target = selected

        exported = self.core.export_excel(
            target,
            search_query=self.search_input.text().strip(),
            tag=self.tag_filter.currentData() or None,
            content_type=self.type_filter.currentData() or None,
        )
        if show_message:
            QMessageBox.information(self, "导出成功", f"已导出到: {exported}")
        return exported
