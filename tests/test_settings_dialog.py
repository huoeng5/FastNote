import tempfile
from pathlib import Path

from DesktopAssistant.config import ConfigManager
from DesktopAssistant.ui.settings_dialog import SettingsDialog


def test_settings_dialog_load_and_save(qapp):
    temp_dir = tempfile.TemporaryDirectory()
    config_path = Path(temp_dir.name) / "config.json"
    config = ConfigManager(config_path=str(config_path))

    dialog = SettingsDialog(config=config)
    assert dialog.shortcut_main_input.text() == "Alt+F1"
    assert dialog.shortcut_screenshot_input.text() == "Alt+F2"
    assert dialog.default_tags_input.text() == "截图 待整理"
    assert dialog.tag_alias_map_input.text() == "1=工作"

    dialog.shortcut_main_input.setText("Ctrl+Shift+A")
    dialog.shortcut_screenshot_input.setText("Ctrl+Shift+S")
    dialog.default_tags_input.setText("截图 待处理")
    dialog.after_screenshot_combo.setCurrentIndex(1)  # silent_save
    dialog.tag_alias_map_input.setText("1=工作,2=账号")
    dialog.handle_save()

    reloaded = ConfigManager(config_path=str(config_path))
    assert reloaded.get("shortcut_main") == "Ctrl+Shift+A"
    assert reloaded.get("shortcut_screenshot") == "Ctrl+Shift+S"
    assert reloaded.get("default_screenshot_tags") == "截图 待处理"
    assert reloaded.get("after_screenshot") == "silent_save"
    assert reloaded.get("tag_alias_map") == {"1": "工作", "2": "账号"}

    dialog.close()
    temp_dir.cleanup()
