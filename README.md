# FastNote

FastNote 是一个基于 **PyQt6** 的本地桌面记录工具，支持快速录入文本、截图、备注与标签，并提供管理、检索与导出能力。

## 功能特性

- 快速记录窗口（文本 + 标签 + 备注）
- 截图流程（确认截图 / 取消 / 仅复制到粘贴板）
- 管理页面列表检索与关键词高亮
- 分页浏览（上一页/下一页/首页/末页/跳页/每页条数）
- 批量删除记录（多选）
- 详情图片点击放大预览
- 编辑记录时支持替换图片与重新截图
- 导出 Excel
- 可配置全局快捷键

## 技术栈

- Python 3.12+
- PyQt6
- Pillow
- openpyxl
- pytest

## 本地运行

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

## 运行测试

```powershell
pytest
```

## 目录结构

```text
DesktopAssistant/
  app_core.py
  config.py
  database/
  ui/
  utils/
tests/
main.py
requirements.txt
```

## 许可证

本项目采用 [MIT License](./LICENSE)。
