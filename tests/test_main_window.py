import tempfile
from pathlib import Path

from PIL import Image
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QDialog, QLabel

from DesktopAssistant.ui.main_window import MainWindow


class DummyCore:
    def __init__(self):
        self.records = [
            {
                "id": 1,
                "created_at": "2026-02-24T10:00:00",
                "tags": "工作 邮箱",
                "content_type": "text",
                "text_content": "mail.company.com",
                "image_path": "",
                "note": "",
            },
            {
                "id": 2,
                "created_at": "2026-02-24T11:00:00",
                "tags": "项目 截图",
                "content_type": "screenshot",
                "text_content": "ui image",
                "image_path": "images/a.png",
                "note": "",
            },
        ]
        self.last_export_path = None
        self.last_export_filters = {}
        self.last_update = None
        self.last_list_kwargs = {}

    def _filtered_items(self, **kwargs):
        items = self.records
        q = kwargs.get("search_query", "")
        if q:
            ql = q.lower()
            items = [r for r in items if ql in r["text_content"].lower() or ql in r["tags"].lower()]
        tag = kwargs.get("tag")
        if tag:
            items = [r for r in items if tag in r["tags"].split()]
        ctype = kwargs.get("content_type")
        if ctype:
            items = [r for r in items if r["content_type"] == ctype]
        return items

    def list_entries(self, **kwargs):
        self.last_list_kwargs = dict(kwargs)
        items = self._filtered_items(**kwargs)
        offset = int(kwargs.get("offset", 0) or 0)
        limit = kwargs.get("limit")
        if limit is None:
            return items[offset:]
        return items[offset : offset + int(limit)]

    def count_entries(self, **kwargs):
        return len(self._filtered_items(**kwargs))

    def available_tags(self):
        return ["工作", "邮箱", "项目", "截图"]

    def delete_entry(self, record_id, remove_image=False):
        self.records = [r for r in self.records if r["id"] != record_id]
        return True

    def export_excel(self, output_path, **filters):
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("dummy", encoding="utf-8")
        self.last_export_path = path
        self.last_export_filters = filters
        return path

    def update_entry(self, record_id, **kwargs):
        self.last_update = {"record_id": record_id, **kwargs}
        for record in self.records:
            if record["id"] == record_id:
                record.update(kwargs)
                return True
        return False


def test_main_window_refresh_and_filter(qapp):
    core = DummyCore()
    window = MainWindow(core=core, on_open_mini=lambda: None)

    window.refresh_records()
    assert window.record_list.count() == 2
    first_item_text = window.record_list.item(0).text()
    assert "#1" not in first_item_text
    assert "[text]" not in first_item_text
    first_item_lines = first_item_text.splitlines()
    assert len(first_item_lines) == 2
    assert first_item_lines[0] == core.records[0]["text_content"]
    assert core.records[0]["tags"] in first_item_lines[1]
    assert core.records[0]["created_at"] in first_item_lines[1]

    window.search_input.setText("mail")
    window.refresh_records()
    assert window.record_list.count() == 1
    window.close()


def test_main_window_list_summary_prefers_note_then_text(qapp):
    core = DummyCore()
    core.records[0]["note"] = "优先显示这条备注"
    core.records[0]["text_content"] = "this text should not be shown first"
    window = MainWindow(core=core, on_open_mini=lambda: None)

    window.refresh_records()
    first_item_text = window.record_list.item(0).text()
    first_item_lines = first_item_text.splitlines()
    assert first_item_lines[0] == "优先显示这条备注"

    core.records[0]["note"] = "   "
    core.records[0]["text_content"] = "备注为空时显示内容"
    window.refresh_records()
    first_item_text = window.record_list.item(0).text()
    first_item_lines = first_item_text.splitlines()
    assert first_item_lines[0] == "备注为空时显示内容"

    window.close()


def test_main_window_search_keyword_highlights_list_text(qapp):
    core = DummyCore()
    window = MainWindow(core=core, on_open_mini=lambda: None)

    window.search_input.setText("mail")
    item = window.record_list.item(0)
    widget = window.record_list.itemWidget(item)
    assert widget is not None
    primary_label = widget.findChild(QLabel, "summaryLinePrimary")
    assert primary_label is not None
    assert "background-color" in primary_label.text()
    assert "mail" in primary_label.text().lower()

    window.close()


def test_main_window_list_item_native_text_is_transparent_with_custom_widget(qapp):
    core = DummyCore()
    window = MainWindow(core=core, on_open_mini=lambda: None)

    item = window.record_list.item(0)
    assert item is not None
    assert item.foreground().color().alpha() == 0

    window.close()


def test_main_window_delete_selected(qapp):
    core = DummyCore()
    window = MainWindow(core=core, on_open_mini=lambda: None)

    window.refresh_records()
    window.record_list.setCurrentRow(0)
    window.handle_delete_selected(confirm=False)

    assert window.record_list.count() == 1
    window.close()


def test_main_window_delete_selected_supports_multi_selection(qapp):
    core = DummyCore()
    core.records.append(
        {
            "id": 3,
            "created_at": "2026-02-24T12:00:00",
            "tags": "工作",
            "content_type": "text",
            "text_content": "third row",
            "image_path": "",
            "note": "",
        }
    )
    window = MainWindow(core=core, on_open_mini=lambda: None)

    window.refresh_records()
    window.record_list.item(0).setSelected(True)
    window.record_list.item(1).setSelected(True)
    window.handle_delete_selected(confirm=False)

    assert len(core.records) == 1
    remaining_ids = {record["id"] for record in core.records}
    assert remaining_ids == {3}
    assert window.record_list.count() == 1
    window.close()


def test_main_window_export_excel(qapp):
    core = DummyCore()
    window = MainWindow(core=core, on_open_mini=lambda: None)
    temp_dir = tempfile.TemporaryDirectory()
    output_path = Path(temp_dir.name) / "out.xlsx"

    window.handle_export_excel(export_path=output_path, show_message=False)

    assert core.last_export_path == output_path
    assert output_path.exists()
    assert core.last_export_filters == {"search_query": "", "tag": None, "content_type": None}
    window.close()
    temp_dir.cleanup()


def test_main_window_export_excel_with_tag_filter(qapp):
    core = DummyCore()
    window = MainWindow(core=core, on_open_mini=lambda: None)
    temp_dir = tempfile.TemporaryDirectory()
    output_path = Path(temp_dir.name) / "work.xlsx"

    tag_index = window.tag_filter.findData("工作")
    window.tag_filter.setCurrentIndex(tag_index)
    window.refresh_records()
    window.handle_export_excel(export_path=output_path, show_message=False)

    assert core.last_export_path == output_path
    assert core.last_export_filters["tag"] == "工作"
    window.close()
    temp_dir.cleanup()


def test_main_window_settings_button_calls_handler(qapp):
    core = DummyCore()
    called = {"count": 0}
    window = MainWindow(core=core, on_open_mini=lambda: None, on_open_settings=lambda: called.__setitem__("count", called["count"] + 1))

    window.btn_settings.click()

    assert called["count"] == 1
    window.close()


def test_main_window_edit_selected(qapp, monkeypatch):
    core = DummyCore()
    window = MainWindow(core=core, on_open_mini=lambda: None)
    window.refresh_records()
    window.record_list.setCurrentRow(0)

    class _FakeDialog:
        def __init__(self, *, record, parent=None):
            self.record = record

        def exec(self):
            return 1

        def get_payload(self):
            return {
                "tags": "工作 更新",
                "text_content": "edited content",
                "note": "edited note",
                "image_path": self.record.get("image_path", ""),
            }

    monkeypatch.setattr("DesktopAssistant.ui.main_window.EditEntryDialog", _FakeDialog)
    window.handle_edit_selected(show_message=False)

    assert core.last_update is not None
    assert core.last_update["record_id"] == 1
    assert core.last_update["tags"] == "工作 更新"
    assert core.last_update["text_content"] == "edited content"
    window.close()

def test_main_window_edit_selected_with_replacement_image(qapp, monkeypatch):
    core = DummyCore()
    window = MainWindow(core=core, on_open_mini=lambda: None)
    window.refresh_records()
    window.record_list.setCurrentRow(1)

    temp_dir = tempfile.TemporaryDirectory()
    replacement_image = Path(temp_dir.name) / "replacement.png"
    Image.new("RGB", (8, 8), color="red").save(replacement_image)

    class _FakeDialog:
        def __init__(self, *, record, parent=None):
            self.record = record

        def exec(self):
            return 1

        def get_payload(self):
            return {
                "tags": "项目 更新",
                "text_content": "edited with image",
                "note": "edited note",
                "image_path": self.record.get("image_path", ""),
                "replacement_image_file": str(replacement_image),
            }

    monkeypatch.setattr("DesktopAssistant.ui.main_window.EditEntryDialog", _FakeDialog)
    window.handle_edit_selected(show_message=False)

    assert core.last_update is not None
    assert core.last_update["record_id"] == 2
    assert core.last_update["image"].size == (8, 8)

    window.close()
    temp_dir.cleanup()


def test_main_window_shows_readable_chinese_labels(qapp):
    core = DummyCore()
    window = MainWindow(core=core, on_open_mini=lambda: None)

    assert window.windowTitle() == "桌面助手 - 管理"
    assert window.search_input.placeholderText() == "搜索标题/内容/标签..."
    assert window.tag_filter.itemText(0) == "全部标签"
    assert window.type_filter.itemText(0) == "全部类型"
    assert window.type_filter.itemText(1) == "纯文本"
    assert window.type_filter.itemText(2) == "截图"
    assert window.type_filter.itemText(3) == "混合"
    assert window.btn_new.text() == "新建"
    assert window.btn_delete.text() == "删除"
    assert window.btn_edit.text() == "编辑"
    assert window.btn_export.text() == "导出Excel"
    assert "共 " in window.status_label.text()
    assert "条记录" in window.status_label.text()

    window.record_list.setCurrentRow(0)
    assert "创建时间:" in window.detail_text.toPlainText()
    assert "ID:" not in window.detail_text.toPlainText()
    assert "标签:" not in window.detail_text.toPlainText()
    assert "类型:" not in window.detail_text.toPlainText()
    assert "备注:" in window.detail_text.toPlainText()

    window.close()

def test_main_window_edit_selected_with_recaptured_image(qapp, monkeypatch):
    core = DummyCore()
    window = MainWindow(core=core, on_open_mini=lambda: None)
    window.refresh_records()
    window.record_list.setCurrentRow(1)

    class _FakeDialog:
        def __init__(self, *, record, parent=None):
            self.record = record

        def exec(self):
            return 1

        def get_payload(self):
            return {
                "tags": "project updated",
                "text_content": "edited with recapture",
                "note": "edited note",
                "image_path": self.record.get("image_path", ""),
                "replacement_image_file": "",
                "replacement_image": Image.new("RGB", (11, 7), color="green"),
            }

    monkeypatch.setattr("DesktopAssistant.ui.main_window.EditEntryDialog", _FakeDialog)
    window.handle_edit_selected(show_message=False)

    assert core.last_update is not None
    assert core.last_update["record_id"] == 2
    assert core.last_update["image"].size == (11, 7)

    window.close()

def test_main_window_edit_selected_does_not_use_modal_exec_for_real_qdialog(qapp, monkeypatch):
    core = DummyCore()
    window = MainWindow(core=core, on_open_mini=lambda: None)
    window.refresh_records()
    window.record_list.setCurrentRow(0)

    class _NonModalDialog(QDialog):
        def __init__(self, *, record, parent=None):
            super().__init__(parent)
            self.record = record
            QTimer.singleShot(0, self.accept)

        def exec(self):
            raise AssertionError("handle_edit_selected should not call dialog.exec() for real QDialog")

        def get_payload(self):
            return {
                "tags": "work updated",
                "text_content": "edited content",
                "note": "edited note",
                "image_path": self.record.get("image_path", ""),
                "replacement_image_file": "",
                "replacement_image": None,
            }

    monkeypatch.setattr("DesktopAssistant.ui.main_window.EditEntryDialog", _NonModalDialog)
    window.handle_edit_selected(show_message=False)

    assert core.last_update is not None
    assert core.last_update["record_id"] == 1
    assert core.last_update["tags"] == "work updated"
    window.close()

def test_main_window_edit_selected_dialog_is_enabled(qapp, monkeypatch):
    core = DummyCore()
    window = MainWindow(core=core, on_open_mini=lambda: None)
    window.refresh_records()
    window.record_list.setCurrentRow(0)

    observed = {"dialog_enabled": None}

    class _InspectableDialog(QDialog):
        def __init__(self, *, record, parent=None):
            super().__init__(parent)
            self.record = record

            def _capture_and_accept():
                observed["dialog_enabled"] = self.isEnabled()
                self.accept()

            QTimer.singleShot(0, _capture_and_accept)

        def get_payload(self):
            return {
                "tags": "work updated",
                "text_content": "edited content",
                "note": "edited note",
                "image_path": self.record.get("image_path", ""),
                "replacement_image_file": "",
                "replacement_image": None,
            }

    monkeypatch.setattr("DesktopAssistant.ui.main_window.EditEntryDialog", _InspectableDialog)
    window.handle_edit_selected(show_message=False)

    assert observed["dialog_enabled"] is True
    window.close()

def test_main_window_pagination_navigation_updates_offset_and_buttons(qapp):
    core = DummyCore()
    core.records = [
        {
            "id": i,
            "created_at": f"2026-02-24T10:{i:02d}:00",
            "tags": "work",
            "content_type": "text",
            "text_content": f"row-{i}",
            "image_path": "",
            "note": "",
        }
        for i in range(1, 46)
    ]

    window = MainWindow(core=core, on_open_mini=lambda: None)

    assert core.last_list_kwargs["limit"] == 20
    assert core.last_list_kwargs["offset"] == 0
    assert window.btn_first_page.isEnabled() is False
    assert window.btn_prev_page.isEnabled() is False
    assert window.btn_next_page.isEnabled() is True
    assert window.btn_last_page.isEnabled() is True

    window.btn_next_page.click()
    assert core.last_list_kwargs["offset"] == 20
    assert window.btn_first_page.isEnabled() is True
    assert window.btn_prev_page.isEnabled() is True
    assert window.btn_next_page.isEnabled() is True
    assert window.btn_last_page.isEnabled() is True

    window.btn_next_page.click()
    assert core.last_list_kwargs["offset"] == 40
    assert window.btn_next_page.isEnabled() is False
    assert window.btn_last_page.isEnabled() is False

    window.btn_prev_page.click()
    assert core.last_list_kwargs["offset"] == 20
    window.close()


def test_main_window_pagination_status_shows_current_range_and_total(qapp):
    core = DummyCore()
    core.records = [
        {
            "id": i,
            "created_at": f"2026-02-24T10:{i:02d}:00",
            "tags": "work",
            "content_type": "text",
            "text_content": f"row-{i}",
            "image_path": "",
            "note": "",
        }
        for i in range(1, 46)
    ]

    window = MainWindow(core=core, on_open_mini=lambda: None)
    assert "1-20/45" in window.status_label.text()

    window.btn_next_page.click()
    assert "21-40/45" in window.status_label.text()

    window.btn_next_page.click()
    assert "41-45/45" in window.status_label.text()
    window.close()


def test_main_window_jump_to_page_updates_offset(qapp):
    core = DummyCore()
    core.records = [
        {
            "id": i,
            "created_at": f"2026-02-24T10:{i:02d}:00",
            "tags": "work",
            "content_type": "text",
            "text_content": f"row-{i}",
            "image_path": "",
            "note": "",
        }
        for i in range(1, 46)
    ]

    window = MainWindow(core=core, on_open_mini=lambda: None)
    window.page_jump_input.setText("3")
    window.btn_jump_page.click()
    assert window.current_page == 3
    assert core.last_list_kwargs["offset"] == 40

    window.page_jump_input.setText("99")
    window.btn_jump_page.click()
    assert window.current_page == 3
    assert core.last_list_kwargs["offset"] == 40

    window.page_jump_input.setText("2")
    window.page_jump_input.returnPressed.emit()
    assert window.current_page == 2
    assert core.last_list_kwargs["offset"] == 20
    window.close()


def test_main_window_first_last_page_buttons(qapp):
    core = DummyCore()
    core.records = [
        {
            "id": i,
            "created_at": f"2026-02-24T10:{i:02d}:00",
            "tags": "work",
            "content_type": "text",
            "text_content": f"row-{i}",
            "image_path": "",
            "note": "",
        }
        for i in range(1, 46)
    ]

    window = MainWindow(core=core, on_open_mini=lambda: None)
    window.btn_last_page.click()
    assert window.current_page == 3
    assert core.last_list_kwargs["offset"] == 40

    window.btn_first_page.click()
    assert window.current_page == 1
    assert core.last_list_kwargs["offset"] == 0
    window.close()


def test_main_window_page_size_selector_changes_limit_and_resets_page(qapp):
    core = DummyCore()
    core.records = [
        {
            "id": i,
            "created_at": f"2026-02-24T10:{i:02d}:00",
            "tags": "work",
            "content_type": "text",
            "text_content": f"row-{i}",
            "image_path": "",
            "note": "",
        }
        for i in range(1, 46)
    ]

    window = MainWindow(core=core, on_open_mini=lambda: None)
    window.btn_next_page.click()
    assert window.current_page == 2
    assert core.last_list_kwargs["offset"] == 20

    page_size_index = window.page_size_combo.findData(50)
    window.page_size_combo.setCurrentIndex(page_size_index)
    assert window.page_size == 50
    assert window.current_page == 1
    assert core.last_list_kwargs["limit"] == 50
    assert core.last_list_kwargs["offset"] == 0
    assert "1-45/45" in window.status_label.text()
    assert window.btn_next_page.isEnabled() is False
    window.close()


def test_main_window_filter_change_resets_pagination_to_first_page(qapp):
    core = DummyCore()
    core.records = [
        {
            "id": i,
            "created_at": f"2026-02-24T10:{i:02d}:00",
            "tags": "work",
            "content_type": "text",
            "text_content": f"row-{i}",
            "image_path": "",
            "note": "",
        }
        for i in range(1, 31)
    ]

    window = MainWindow(core=core, on_open_mini=lambda: None)
    window.btn_next_page.click()
    assert core.last_list_kwargs["offset"] == 20

    window.search_input.setText("row-1")
    assert core.last_list_kwargs["offset"] == 0
    assert window.btn_prev_page.isEnabled() is False

    window.close()


def test_main_window_open_image_preview_from_detail(qapp, monkeypatch):
    core = DummyCore()
    window = MainWindow(core=core, on_open_mini=lambda: None)
    temp_dir = tempfile.TemporaryDirectory()
    image_file = Path(temp_dir.name) / "preview.png"
    Image.new("RGB", (120, 80), color="orange").save(image_file)

    class _ImageManager:
        def get_absolute_path(self, relative_path):
            if relative_path == "images/a.png":
                return image_file
            return image_file

    core.image_manager = _ImageManager()
    window.refresh_records()
    window.record_list.setCurrentRow(1)

    called = {"count": 0}

    def _fake_exec(self):
        called["count"] += 1
        return int(QDialog.DialogCode.Accepted)

    monkeypatch.setattr("DesktopAssistant.ui.main_window.QDialog.exec", _fake_exec)

    window._open_image_preview()
    assert called["count"] == 1

    window.record_list.setCurrentRow(0)
    window._open_image_preview()
    assert called["count"] == 1

    window.close()
    temp_dir.cleanup()
