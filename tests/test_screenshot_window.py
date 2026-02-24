from PIL import Image
from PyQt6.QtCore import QPoint
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import QApplication

from DesktopAssistant.ui.screenshot_window import ScreenshotWindow, normalized_rect


def test_normalized_rect():
    rect = normalized_rect(QPoint(50, 100), QPoint(10, 20))
    assert rect.x() == 10
    assert rect.y() == 20
    assert rect.width() == 41
    assert rect.height() == 81


def test_screenshot_window_has_confirm_and_cancel_buttons(qapp):
    window = ScreenshotWindow()
    assert window.confirm_button.text() == "确认截图"
    assert window.copy_clipboard_button.text() == "仅复制到粘贴板"
    assert window.cancel_button.text() == "取消"
    assert not window.confirm_button.isVisible()
    assert not window.copy_clipboard_button.isVisible()
    assert not window.cancel_button.isVisible()
    window.close()


def test_action_buttons_show_after_selection(qapp):
    window = ScreenshotWindow()
    window.resize(600, 400)
    window.show()
    window._screen_pixmap = QPixmap(600, 400)
    window._screen_pixmap.fill(QColor("white"))
    window._selection_start = QPoint(100, 100)
    window._selection_end = QPoint(300, 220)

    window._update_action_buttons()

    assert window.confirm_button.isVisible()
    assert window.copy_clipboard_button.isVisible()
    assert window.cancel_button.isVisible()
    window.close()


def test_confirm_button_emits_screenshot(qapp):
    window = ScreenshotWindow()
    window.resize(300, 200)
    window._screen_pixmap = QPixmap(300, 200)
    window._screen_pixmap.fill(QColor("red"))
    window._selection_start = QPoint(20, 20)
    window._selection_end = QPoint(100, 80)
    window._update_action_buttons()

    captured = []
    window.screenshot_taken.connect(lambda img: captured.append(img))
    window.confirm_button.click()

    assert len(captured) == 1
    assert isinstance(captured[0], Image.Image)
    window.close()


def test_copy_clipboard_button_copies_only(qapp):
    window = ScreenshotWindow()
    window.resize(300, 200)
    window._screen_pixmap = QPixmap(300, 200)
    window._screen_pixmap.fill(QColor("green"))
    window._selection_start = QPoint(20, 20)
    window._selection_end = QPoint(100, 80)
    window._update_action_buttons()

    captured = []
    canceled = []
    window.screenshot_taken.connect(lambda img: captured.append(img))
    window.capture_canceled.connect(lambda: canceled.append(True))

    clipboard = QApplication.instance().clipboard()
    clipboard.clear()
    window.copy_clipboard_button.click()

    copied_image = clipboard.image()
    assert not copied_image.isNull()
    assert captured == []
    assert canceled == []
    window.close()


def test_screenshot_window_can_disable_copy_clipboard_button(qapp):
    window = ScreenshotWindow(show_copy_clipboard_button=False)
    window.resize(300, 200)
    window.show()
    window._screen_pixmap = QPixmap(300, 200)
    window._screen_pixmap.fill(QColor("white"))
    window._selection_start = QPoint(20, 20)
    window._selection_end = QPoint(100, 80)

    window._update_action_buttons()

    assert window.confirm_button.isVisible()
    assert not window.copy_clipboard_button.isVisible()
    assert window.cancel_button.isVisible()
    window.close()
