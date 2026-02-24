from PIL import Image
from PyQt6.QtCore import QObject, QTimer, Qt, pyqtSignal

from DesktopAssistant.ui.edit_entry_dialog import EditEntryDialog


def test_edit_entry_dialog_load_and_save(qapp):
    record = {
        "id": 1,
        "tags": "work mail",
        "text_content": "original text",
        "note": "original note",
        "image_path": "images/a.png",
    }
    dialog = EditEntryDialog(record=record)

    assert dialog.tags_input.text() == "work mail"
    assert dialog.note_input.text() == "original note"
    assert "images/a.png" in dialog.image_info_label.text()

    dialog.tags_input.setText("work updated")
    dialog.text_edit.setPlainText("edited text")
    dialog.note_input.setText("edited note")
    dialog.remove_image_checkbox.setChecked(True)
    dialog.handle_save()

    payload = dialog.get_payload()
    assert payload["tags"] == "work updated"
    assert payload["text_content"] == "edited text"
    assert payload["note"] == "edited note"
    assert payload["image_path"] == ""
    dialog.close()


def test_edit_entry_dialog_choose_replacement_image(qapp, monkeypatch):
    record = {
        "id": 2,
        "tags": "work",
        "text_content": "",
        "note": "",
        "image_path": "images/a.png",
    }
    dialog = EditEntryDialog(record=record)
    dialog.remove_image_checkbox.setChecked(True)

    monkeypatch.setattr(
        "DesktopAssistant.ui.edit_entry_dialog.QFileDialog.getOpenFileName",
        lambda *args, **kwargs: ("C:/tmp/new-image.png", ""),
    )

    dialog.btn_select_image.click()
    payload = dialog.get_payload()

    assert payload["replacement_image_file"] == "C:/tmp/new-image.png"
    assert dialog.remove_image_checkbox.isChecked() is False
    assert "new-image.png" in dialog.selected_image_label.text()
    dialog.close()


def test_edit_entry_dialog_recapture_sets_replacement_image(qapp):
    record = {
        "id": 3,
        "tags": "work",
        "text_content": "",
        "note": "",
        "image_path": "images/a.png",
    }
    dialog = EditEntryDialog(record=record)
    dialog.remove_image_checkbox.setChecked(True)

    recaptured = Image.new("RGB", (16, 10), color="blue")
    dialog._on_screenshot_taken(recaptured)
    payload = dialog.get_payload()

    assert payload["replacement_image"] is not None
    assert payload["replacement_image"].size == (16, 10)
    assert payload["replacement_image_file"] == ""
    assert dialog.remove_image_checkbox.isChecked() is False
    assert "重新截图" in dialog.selected_image_label.text()
    dialog.close()


def test_edit_entry_dialog_recapture_does_not_close_exec_loop(qapp):
    class _FakeScreenshotWindow(QObject):
        screenshot_taken = pyqtSignal(object)
        capture_canceled = pyqtSignal()

        def __init__(self):
            super().__init__()
            self.begin_called = False

        def begin_capture(self):
            self.begin_called = True

        def close(self):
            return None

    holder = {}

    def _factory():
        window = _FakeScreenshotWindow()
        holder["window"] = window
        return window

    dialog = EditEntryDialog(
        record={"id": 4, "tags": "work", "text_content": "x", "note": "", "image_path": "images/a.png"},
        screenshot_factory=_factory,
    )

    observed = {"ran": False, "modality": None}

    def _verify_during_exec():
        observed["ran"] = True
        observed["modality"] = dialog.windowModality()
        if "window" in holder:
            holder["window"].capture_canceled.emit()
        dialog.reject()

    QTimer.singleShot(0, dialog.btn_recapture_image.click)
    QTimer.singleShot(60, _verify_during_exec)
    dialog.exec()

    assert observed["ran"] is True
    assert holder["window"].begin_called is True
    assert observed["modality"] == Qt.WindowModality.NonModal


def test_edit_entry_dialog_default_screenshot_window_disables_copy_only_button(qapp):
    dialog = EditEntryDialog(
        record={"id": 5, "tags": "work", "text_content": "x", "note": "", "image_path": "images/a.png"}
    )
    screenshot_window = dialog._screenshot_factory()
    assert screenshot_window.show_copy_clipboard_button is False
    screenshot_window.close()
    dialog.close()
