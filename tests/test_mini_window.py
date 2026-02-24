from PIL import Image

from DesktopAssistant.ui.mini_window import MiniWindow


class DummyCore:
    def __init__(self):
        self.saved_payloads = []
        self.config = {"shortcut_main": "Alt+F1", "show_hints": True}

    def save_entry(self, **kwargs):
        self.saved_payloads.append(kwargs)
        return {
            "id": len(self.saved_payloads),
            **kwargs,
            "content_type": "mixed" if kwargs.get("image") else "text",
            "image_path": "images/a.png" if kwargs.get("image") else "",
        }


class _DictConfig:
    def __init__(self, data):
        self._data = dict(data)

    def get(self, key, default=None):
        return self._data.get(key, default)


def test_mini_window_save_text(qapp):
    core = DummyCore()
    window = MiniWindow(core=core, on_open_manager=lambda: None, on_start_screenshot=lambda: None)

    window.text_edit.setPlainText("hello")
    window.tags_input.setText("工作 账号")
    window.note_input.setText("账号备注")
    window.handle_save(show_message=False)

    assert len(core.saved_payloads) == 1
    assert core.saved_payloads[0]["text"] == "hello"
    assert core.saved_payloads[0]["tags"] == "工作 账号"
    assert core.saved_payloads[0]["note"] == "账号备注"
    assert window.text_edit.toPlainText() == ""
    assert window.note_input.text() == ""
    window.close()


def test_mini_window_save_with_image(qapp):
    core = DummyCore()
    window = MiniWindow(core=core, on_open_manager=lambda: None, on_start_screenshot=lambda: None)

    image = Image.new("RGB", (10, 10), color="red")
    window.set_pending_image(image)
    window.handle_save(show_message=False)

    assert len(core.saved_payloads) == 1
    assert core.saved_payloads[0]["image"] is not None
    assert window.pending_image is None
    window.close()


def test_mini_window_show_success_message_after_save(qapp, monkeypatch):
    core = DummyCore()
    window = MiniWindow(core=core, on_open_manager=lambda: None, on_start_screenshot=lambda: None)
    called = {"count": 0}

    def _fake_info(*args, **kwargs):
        called["count"] += 1
        return None

    monkeypatch.setattr("DesktopAssistant.ui.mini_window.QMessageBox.information", _fake_info)
    window.text_edit.setPlainText("saved")
    window.handle_save()

    assert called["count"] == 1
    window.close()


def test_mini_window_has_note_input(qapp):
    core = DummyCore()
    window = MiniWindow(core=core, on_open_manager=lambda: None, on_start_screenshot=lambda: None)

    assert window.note_input is not None
    assert "备注" in window.note_input.placeholderText()
    window.close()

def test_mini_window_open_manager_hides_quick_window(qapp):
    core = DummyCore()
    called = {"count": 0}
    window = MiniWindow(
        core=core,
        on_open_manager=lambda: called.__setitem__("count", called["count"] + 1),
        on_start_screenshot=lambda: None,
    )
    window.show()

    window.btn_open_manager.click()

    assert called["count"] == 1
    assert window.isVisible() is False
    window.close()


def test_mini_window_hint_uses_configured_shortcut(qapp):
    core = DummyCore()
    core.config = _DictConfig({"shortcut_main": "P", "show_hints": True})
    window = MiniWindow(core=core, on_open_manager=lambda: None, on_start_screenshot=lambda: None)

    assert "P" in window.hint_label.text()
    assert "Alt+F1" not in window.hint_label.text()
    window.close()


def test_mini_window_refresh_hints_updates_text_after_config_change(qapp):
    core = DummyCore()
    core.config = _DictConfig({"shortcut_main": "Alt+F1", "show_hints": True})
    window = MiniWindow(core=core, on_open_manager=lambda: None, on_start_screenshot=lambda: None)

    core.config = _DictConfig({"shortcut_main": "P", "show_hints": True})
    window.refresh_hints()

    assert "P" in window.hint_label.text()
    assert "Alt+F1" not in window.hint_label.text()
    window.close()
