# 桌面助手实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** 构建一个基于 PyQt6 的桌面助手应用，支持快捷键唤起、截图、数据存储到 Excel，并提供管理界面。

**Architecture:** 应用采用模块化设计，核心包含配置管理、Excel 数据库操作、三个 UI 窗口（迷你输入、截图、管理）以及全局快捷键监听。数据以 Excel 为主存储，图片单独存放。

**Tech Stack:** Python 3.11+, PyQt6, openpyxl, Pillow, pynput, PyInstaller

---

## 项目准备

### Task 0: 创建项目结构和虚拟环境

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: Directory structure

**Step 1: Create project directory structure**

```bash
mkdir -p DesktopAssistant/{database,ui,utils,resources/icons,tests}
touch DesktopAssistant/__init__.py
touch DesktopAssistant/database/__init__.py
touch DesktopAssistant/ui/__init__.py
touch DesktopAssistant/utils/__init__.py
```

**Step 2: Create requirements.txt**

```
PyQt6>=6.6.0
openpyxl>=3.1.0
Pillow>=10.0.0
pynput>=1.7.6
```

**Step 3: Create .gitignore**

```
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
dist/
*.spec
.venv/
venv/
ENV/
.idea/
.vscode/
*.xlsx
!tests/data/*.xlsx
images/
screenshots/
```

**Step 4: Create virtual environment and install dependencies**

```bash
cd DesktopAssistant
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Step 5: Verify installation**

```bash
python -c "import PyQt6; import openpyxl; import PIL; import pynput; print('All dependencies installed')"
```

Expected output: `All dependencies installed`

**Step 6: Commit**

```bash
git init
git add .
git commit -m "chore: initial project setup with dependencies"
```

---

## Phase 1: 核心基础设施

### Task 1: 配置管理模块

**Files:**
- Create: `DesktopAssistant/config.py`
- Test: `tests/test_config.py`

**Step 1: Write the failing test**

```python
# tests/test_config.py
import os
import sys
import tempfile
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from config import ConfigManager


class TestConfigManager:
    def setup_method(self):
        """Create temporary directory for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, 'config.json')

    def teardown_method(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_default_values(self):
        """Test that ConfigManager has correct default values"""
        config = ConfigManager(config_path=self.config_path)

        assert config.get('shortcut_main') == 'Alt+F1'
        assert config.get('shortcut_screenshot') == 'Alt+F2'
        assert config.get('after_screenshot') == 'open_mini_window'
        assert config.get('default_screenshot_tags') == '截图 待整理'

    def test_set_and_get(self):
        """Test setting and getting config values"""
        config = ConfigManager(config_path=self.config_path)

        config.set('shortcut_main', 'Ctrl+Shift+A')
        assert config.get('shortcut_main') == 'Ctrl+Shift+A'

    def test_persistence(self):
        """Test that config persists to disk"""
        config1 = ConfigManager(config_path=self.config_path)
        config1.set('shortcut_main', 'Ctrl+`')

        # Create new instance with same path
        config2 = ConfigManager(config_path=self.config_path)
        assert config2.get('shortcut_main') == 'Ctrl+`'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

**Step 2: Run test to verify it fails**

```bash
cd DesktopAssistant
python -m pytest tests/test_config.py -v
```

Expected: ImportError or ModuleNotFoundError for `config`

**Step 3: Write minimal implementation**

```python
# DesktopAssistant/config.py
"""Configuration management module."""

import json
import os
from pathlib import Path
from typing import Any, Optional


class ConfigManager:
    """Manages application configuration with persistence."""

    DEFAULTS = {
        # Hotkeys
        'shortcut_main': 'Alt+F1',
        'shortcut_screenshot': 'Alt+F2',

        # Screenshot behavior
        'after_screenshot': 'open_mini_window',  # open_mini_window / silent_save / copy_only
        'default_screenshot_tags': '截图 待整理',

        # Image quality
        'image_quality': 95,

        # Window settings
        'mini_window_position': None,  # (x, y)
        'mini_window_size': (300, 200),
        'main_window_position': None,
        'main_window_size': (800, 600),

        # Behavior
        'minimize_to_tray': True,
        'auto_start': False,
        'show_hints': True,
    }

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager.

        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Default: %APPDATA%/DesktopAssistant/config.json (Windows)
            # or ~/.config/desktop-assistant/config.json (Linux/Mac)
            if os.name == 'nt':  # Windows
                app_data = os.environ.get('APPDATA', Path.home())
                self.config_path = Path(app_data) / 'DesktopAssistant' / 'config.json'
            else:  # Linux/Mac
                self.config_path = Path.home() / '.config' / 'desktop-assistant' / 'config.json'

        self._config = {}
        self._load()

    def _load(self):
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                # Merge with defaults
                self._config = {**self.DEFAULTS, **loaded}
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to load config: {e}")
                self._config = self.DEFAULTS.copy()
        else:
            self._config = self.DEFAULTS.copy()
            self.save()  # Create default config file

    def save(self):
        """Save configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Error: Failed to save config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """Set configuration value and save.

        Args:
            key: Configuration key
            value: Value to set
        """
        self._config[key] = value
        self.save()

    def reset(self, key: str = None):
        """Reset configuration to defaults.

        Args:
            key: Specific key to reset, or None to reset all
        """
        if key:
            if key in self.DEFAULTS:
                self._config[key] = self.DEFAULTS[key]
        else:
            self._config = self.DEFAULTS.copy()
        self.save()


# Convenience function for quick access
def get_config(config_path: str = None) -> ConfigManager:
    """Get or create singleton config instance.

    Args:
        config_path: Optional custom config path

    Returns:
        ConfigManager instance
    """
    if not hasattr(get_config, '_instance'):
        get_config._instance = ConfigManager(config_path)
    return get_config._instance
```

**Step 4: Run test to verify it passes**

```bash
cd DesktopAssistant
python -m pytest tests/test_config.py -v
```

Expected: All 4 tests pass

**Step 5: Commit**

```bash
git add DesktopAssistant/config.py tests/test_config.py
git commit -m "feat(config): add configuration management module with persistence"
```

---

（由于篇幅限制，此处省略 Task 2-15 的详细内容。完整计划包含以下任务：）

### Task 2: Excel 数据库管理模块
### Task 3: 图片管理模块
### Task 4: 系统托盘模块
### Task 5: 全局快捷键监听模块
### Task 6: 迷你输入窗口
### Task 7: 截图选择窗口
### Task 8: 管理主窗口
### Task 9: 应用主类集成
### Task 10: 设置对话框
### Task 11: 打包配置（PyInstaller）
### Task 12: 集成测试
### Task 13: 文档编写
### Task 14: 首次运行引导
### Task 15: 性能优化和最终打包

---

## 执行方式选择

**计划已完成并保存到 `docs/plans/2025-02-22-desktop-assistant-implementation.md`**

两个执行选项：

**1. 子代理驱动（当前会话）** - 我为每个任务分派新的子代理，在任务之间进行审查，快速迭代

**2. 并行会话（独立）** - 在工作树中打开新会话，使用 executing-plans 进行批量执行并设置检查点

**您选择哪种方式？**