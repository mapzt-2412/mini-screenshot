#!/usr/bin/env python3
"""Pin a screenshot as a small always-on-top floating window.

Spawned as a separate process by the tray (same pattern as
``open_editor.py``) so it doesn't fight the tray's Gtk main loop.

Controls:
    - Drag the title bar to move
    - Mouse wheel to change opacity
    - Ctrl + / Ctrl - to resize
    - Double-click image or Esc / close button to dismiss
"""

import os
import sys

_PKG_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

from mini_screenshot.qt_env import ensure_qt_platform

ensure_qt_platform()

from PyQt5.QtCore import Qt, QPoint, QSize
from PyQt5.QtGui import QCursor, QKeySequence, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QHBoxLayout, QLabel, QPushButton, QShortcut,
    QVBoxLayout, QWidget,
)

_BG = "#1e2128"
_BG_BAR = "#262a33"
_BORDER = "#3a3f4b"
_TEXT = "#c8ccd4"
_TEXT_MUTED = "#8b919d"

class PinWindow(QWidget):
    BAR_H = 28

    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Mini Screenshot — Ghim")
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            sys.exit(1)

        screen = QApplication.primaryScreen().availableGeometry()
        max_w, max_h = int(screen.width() * 0.55), int(screen.height() * 0.55)
        if pixmap.width() > max_w or pixmap.height() > max_h:
            pixmap = pixmap.scaled(
                max_w, max_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

        self._base_pixmap = QPixmap(image_path)
        self._display_size = pixmap.size()
        self._drag_pos = None
        self._opacity = 1.0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(0)

        card = QWidget()
        card.setObjectName("pinCard")
        card.setStyleSheet(f"""
            QWidget#pinCard {{
                background: {_BG_BAR};
                border: 1px solid {_BORDER};
                border-radius: 10px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        self._bar = QWidget()
        self._bar.setFixedHeight(self.BAR_H)
        self._bar.setStyleSheet(f"""
            background: {_BG_BAR};
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            border-bottom: 1px solid {_BORDER};
        """)
        bar_layout = QHBoxLayout(self._bar)
        bar_layout.setContentsMargins(10, 0, 6, 0)
        bar_layout.setSpacing(6)

        pin_label = QLabel("📌 Ghim")
        pin_label.setStyleSheet(f"color: {_TEXT}; font-size: 11px; font-weight: 600;")
        bar_layout.addWidget(pin_label)

        self._opacity_label = QLabel("100%")
        self._opacity_label.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 10px;")
        self._opacity_label.setAlignment(Qt.AlignCenter)
        self._opacity_label.setFixedWidth(36)
        bar_layout.addWidget(self._opacity_label)

        bar_layout.addStretch()

        hint = QLabel("Ctrl±")
        hint.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 10px;")
        hint.setToolTip("Ctrl + / Ctrl - để đổi kích thước")
        bar_layout.addWidget(hint)

        close_btn = QPushButton("×")
        close_btn.setFixedSize(22, 22)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setToolTip("Đóng (Esc)")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {_TEXT_MUTED};
                border: none;
                border-radius: 11px;
                font-size: 16px;
                font-weight: bold;
                padding: 0;
            }}
            QPushButton:hover {{
                background: #ff3b30;
                color: white;
            }}
        """)
        close_btn.clicked.connect(self.close)
        bar_layout.addWidget(close_btn)

        card_layout.addWidget(self._bar)

        self._label = QLabel()
        self._label.setPixmap(pixmap)
        self._label.setAlignment(Qt.AlignCenter)
        self._label.setStyleSheet(f"""
            background: {_BG};
            border-bottom-left-radius: 10px;
            border-bottom-right-radius: 10px;
        """)
        card_layout.addWidget(self._label)

        outer.addWidget(card)

        total_w = pixmap.width() + 16
        total_h = pixmap.height() + self.BAR_H + 16
        self.resize(total_w, total_h)
        self.move(QCursor.pos() - QPoint(total_w // 2, total_h // 3))
        self.setWindowOpacity(self._opacity)

        QShortcut(QKeySequence("Escape"), self, activated=self.close)
        QShortcut(QKeySequence("Ctrl+="), self, activated=lambda: self._scale(1.15))
        QShortcut(QKeySequence("Ctrl+-"), self, activated=lambda: self._scale(1 / 1.15))

    def _update_opacity_label(self):
        self._opacity_label.setText(f"{int(round(self._opacity * 100))}%")

    def _scale(self, factor):
        new_w = max(80, int(self._display_size.width() * factor))
        new_h = max(60, int(self._display_size.height() * factor))
        self._display_size = QSize(new_w, new_h)
        self._label.setPixmap(
            self._base_pixmap.scaled(
                self._display_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
        )
        self.resize(self._display_size.width() + 16, self._display_size.height() + self.BAR_H + 16)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            bar_top = self._bar.mapToGlobal(QPoint(0, 0)).y()
            bar_bottom = bar_top + self.BAR_H
            if bar_top <= event.globalY() <= bar_bottom:
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        self.setCursor(Qt.ArrowCursor)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            bar_top = self._bar.mapToGlobal(QPoint(0, 0)).y()
            if event.globalY() > bar_top + self.BAR_H:
                self.close()

    def wheelEvent(self, event):
        delta = 0.08 if event.angleDelta().y() > 0 else -0.08
        self._opacity = min(1.0, max(0.25, self._opacity + delta))
        self.setWindowOpacity(self._opacity)
        self._update_opacity_label()

    def enterEvent(self, event):
        self._bar.setStyleSheet(f"""
            background: #2e3340;
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            border-bottom: 1px solid {_BORDER};
        """)

    def leaveEvent(self, event):
        self._bar.setStyleSheet(f"""
            background: {_BG_BAR};
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            border-bottom: 1px solid {_BORDER};
        """)


def main(argv=None):
    argv = argv if argv is not None else sys.argv
    if len(argv) < 2:
        print("Usage: pin_window.py <image_path>")
        return 1
    app = QApplication.instance() or QApplication(sys.argv)
    win = PinWindow(argv[1])
    win.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
