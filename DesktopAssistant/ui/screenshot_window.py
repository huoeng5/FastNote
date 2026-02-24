"""Fullscreen screenshot selection window."""

from __future__ import annotations

from typing import Optional

from PIL import Image
from PyQt6.QtCore import QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QApplication, QPushButton, QWidget


def normalized_rect(start: QPoint, end: QPoint) -> QRect:
    """Build a QRect from two points with normalized bounds."""
    left = min(start.x(), end.x())
    top = min(start.y(), end.y())
    right = max(start.x(), end.x())
    bottom = max(start.y(), end.y())
    return QRect(QPoint(left, top), QPoint(right, bottom))


def _pixmap_to_pil(pixmap: QPixmap) -> Image.Image:
    image = pixmap.toImage().convertToFormat(pixmap.toImage().Format.Format_RGBA8888)
    width = image.width()
    height = image.height()
    bits = image.bits()
    bits.setsize(width * height * 4)
    return Image.frombuffer("RGBA", (width, height), bytes(bits), "raw", "RGBA", 0, 1).copy()


class ScreenshotWindow(QWidget):
    """Capture a region from the current desktop."""

    screenshot_taken = pyqtSignal(object)  # PIL.Image
    capture_canceled = pyqtSignal()

    def __init__(self, *, show_copy_clipboard_button: bool = True) -> None:
        super().__init__(None)
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.show_copy_clipboard_button = show_copy_clipboard_button

        self._screen_pixmap: Optional[QPixmap] = None
        self._selection_start: Optional[QPoint] = None
        self._selection_end: Optional[QPoint] = None
        self._is_selecting = False

        self.confirm_button = QPushButton("确认截图", self)
        self.copy_clipboard_button = QPushButton("仅复制到粘贴板", self)
        self.cancel_button = QPushButton("取消", self)
        self.confirm_button.clicked.connect(self._confirm_capture)
        self.copy_clipboard_button.clicked.connect(self._copy_capture_to_clipboard)
        self.cancel_button.clicked.connect(self._cancel_capture)
        self._init_action_buttons()

    def _init_action_buttons(self) -> None:
        button_style = (
            "QPushButton {"
            "background-color: rgba(30, 30, 30, 220);"
            "color: white;"
            "border: 1px solid rgba(255, 255, 255, 120);"
            "border-radius: 6px;"
            "padding: 6px 12px;"
            "}"
            "QPushButton:hover {"
            "background-color: rgba(55, 55, 55, 230);"
            "}"
        )
        self.confirm_button.setStyleSheet(button_style)
        self.copy_clipboard_button.setStyleSheet(button_style)
        self.cancel_button.setStyleSheet(button_style)
        self.confirm_button.hide()
        self.copy_clipboard_button.hide()
        self.cancel_button.hide()

    def _selection_rect(self) -> Optional[QRect]:
        if self._selection_start is None or self._selection_end is None:
            return None
        rect = normalized_rect(self._selection_start, self._selection_end)
        if rect.width() <= 1 or rect.height() <= 1:
            return None
        return rect

    def _update_action_buttons(self) -> None:
        rect = self._selection_rect()
        if rect is None:
            self.confirm_button.hide()
            self.copy_clipboard_button.hide()
            self.cancel_button.hide()
            return

        button_width = 96
        button_height = 34
        gap = 10
        buttons = [self.confirm_button]
        if self.show_copy_clipboard_button:
            buttons.append(self.copy_clipboard_button)
        else:
            self.copy_clipboard_button.hide()
        buttons.append(self.cancel_button)

        total_width = button_width * len(buttons) + gap * (len(buttons) - 1)
        x = rect.center().x() - total_width // 2
        x = max(8, min(x, self.width() - total_width - 8))

        y_below = rect.bottom() + 12
        y_above = rect.top() - button_height - 12
        if y_below + button_height <= self.height() - 8:
            y = y_below
        elif y_above >= 8:
            y = y_above
        else:
            y = max(8, self.height() - button_height - 8)

        for idx, button in enumerate(buttons):
            button_x = x + idx * (button_width + gap)
            button.setGeometry(button_x, y, button_width, button_height)
            button.show()
            button.raise_()

    def begin_capture(self) -> None:
        app = QApplication.instance()
        if app is None:
            return
        screen = app.primaryScreen()
        if screen is None:
            return
        self._screen_pixmap = screen.grabWindow(0)
        self._selection_start = None
        self._selection_end = None
        self._is_selecting = False
        self._update_action_buttons()
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

    def keyPressEvent(self, event) -> None:  # type: ignore[override]
        if event.key() in (Qt.Key.Key_Escape,):
            self._cancel_capture()
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._confirm_capture()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton:
            point = event.position().toPoint()
            self._selection_start = point
            self._selection_end = point
            self._is_selecting = True
            self._update_action_buttons()
            self.update()

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._is_selecting and self._selection_start is not None:
            self._selection_end = event.position().toPoint()
            self._update_action_buttons()
            self.update()

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.MouseButton.LeftButton and self._is_selecting:
            self._is_selecting = False
            self._selection_end = event.position().toPoint()
            self._update_action_buttons()
            self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 120))

        if self._screen_pixmap is None:
            return
        if self._selection_start is None or self._selection_end is None:
            return

        rect = normalized_rect(self._selection_start, self._selection_end)
        if rect.width() <= 1 or rect.height() <= 1:
            return

        source = self._screen_pixmap.copy(rect)
        painter.drawPixmap(rect, source)
        painter.setPen(QPen(QColor(0, 170, 255), 2))
        painter.drawRect(rect)

    def _confirm_capture(self) -> None:
        if self._screen_pixmap is None:
            self._cancel_capture()
            return
        rect = self._selection_rect()
        if rect is None:
            self._cancel_capture()
            return

        selected = self._screen_pixmap.copy(rect)
        self.confirm_button.hide()
        self.copy_clipboard_button.hide()
        self.cancel_button.hide()
        self.hide()
        self.screenshot_taken.emit(_pixmap_to_pil(selected))

    def _copy_capture_to_clipboard(self) -> None:
        if self._screen_pixmap is None:
            self._cancel_capture()
            return
        rect = self._selection_rect()
        if rect is None:
            self._cancel_capture()
            return

        selected = self._screen_pixmap.copy(rect)
        app = QApplication.instance()
        if app is not None:
            app.clipboard().setPixmap(selected)
        self.confirm_button.hide()
        self.copy_clipboard_button.hide()
        self.cancel_button.hide()
        self.hide()

    def _cancel_capture(self) -> None:
        self.confirm_button.hide()
        self.copy_clipboard_button.hide()
        self.cancel_button.hide()
        self.hide()
        self.capture_canceled.emit()
