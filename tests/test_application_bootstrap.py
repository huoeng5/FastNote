from DesktopAssistant.main import DesktopAssistantApplication



def test_application_components_init(qapp):
    app = DesktopAssistantApplication(test_mode=True)
    assert app.core is not None
    assert app.mini_window is not None
    assert app.main_window is not None
    app.quit()


def test_open_settings_dialog_refreshes_mini_hint_shortcut(qapp, monkeypatch, tmp_path):
    app = DesktopAssistantApplication(base_dir=tmp_path, test_mode=True)
    app.core.config.set("shortcut_main", "Alt+F1")
    app.mini_window.refresh_hints()
    assert "Alt+F1" in app.mini_window.hint_label.text()

    class _FakeDialog:
        def __init__(self, *, config, parent=None):
            self.saved = True
            self._config = config

        def exec(self):
            self._config.set("shortcut_main", "P")
            return 0

    monkeypatch.setattr("DesktopAssistant.main.SettingsDialog", _FakeDialog)
    app.open_settings_dialog()

    assert "P" in app.mini_window.hint_label.text()
    assert "Alt+F1" not in app.mini_window.hint_label.text()
    app.quit()
