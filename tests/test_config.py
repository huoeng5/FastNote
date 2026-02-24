import os
import tempfile
from pathlib import Path

from DesktopAssistant.config import ConfigManager


class TestConfigManager:
    def setup_method(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = Path(self.temp_dir.name) / 'config.json'

    def teardown_method(self):
        self.temp_dir.cleanup()

    def test_default_values(self):
        config = ConfigManager(config_path=str(self.config_path))

        assert config.get('shortcut_main') == 'Alt+F1'
        assert config.get('shortcut_screenshot') == 'Alt+F2'
        assert config.get('after_screenshot') == 'open_mini_window'
        assert config.get('default_screenshot_tags') == '截图 待整理'
        assert config.get('tag_alias_map') == {'1': '工作'}

    def test_set_and_get(self):
        config = ConfigManager(config_path=str(self.config_path))

        config.set('shortcut_main', 'Ctrl+Shift+A')
        assert config.get('shortcut_main') == 'Ctrl+Shift+A'

    def test_persistence(self):
        config1 = ConfigManager(config_path=str(self.config_path))
        config1.set('shortcut_main', 'Ctrl+`')

        config2 = ConfigManager(config_path=str(self.config_path))
        assert config2.get('shortcut_main') == 'Ctrl+`'

    def test_reset_single_key_and_all(self):
        config = ConfigManager(config_path=str(self.config_path))
        config.set('shortcut_main', 'Ctrl+Q')
        config.reset('shortcut_main')
        assert config.get('shortcut_main') == 'Alt+F1'

        config.set('show_hints', False)
        config.reset()
        assert config.get('show_hints') is True
