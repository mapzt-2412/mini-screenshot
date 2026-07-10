"""
editor.py
Cua so chinh sua anh chup man hinh: ve hinh chu nhat, ellipse, mui ten, duong
thang, but ve tu do, highlighter, text, danh so buoc, blur/pixelate, crop,
color picker, undo/redo, luu file / copy clipboard.
"""
import os
import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QToolBar, QAction, QColorDialog,
    QFileDialog, QInputDialog, QLabel, QSpinBox, QMessageBox, QActionGroup,
    QVBoxLayout, QScrollArea, QSizePolicy, QToolButton, QFrame, QStatusBar
)
from PyQt5.QtGui import (
    QPixmap, QPainter, QPen, QColor, QIcon, QPolygonF, QFont, QCursor, QImage
)
from PyQt5.QtCore import Qt, QPoint, QPointF, QRect, QRectF, QSize, pyqtSignal
import math

import clipboard_util
import icons
import ocr
from ocr_dialog import OcrResultDialog


TOOLS = [
    "select", "pen", "line", "arrow", "rect", "ellipse",
    "highlighter", "text", "step", "blur", "pixelate", "crop", "picker", "ocr",
]


class Canvas(QWidget):
    """Vung ve chinh: giu 1 pixmap goc (day du chat luong) va cho phep ve
    annotation len tren. Ho tro ZOOM rieng cho phan XEM (khong dung chat
    luong anh that): khi anh qua to (vd chup toan man hinh 4K), Canvas se
    hien thi thu nho lai cho vua man hinh, nhung du lieu pixel thuc su
    (dung khi Luu/Copy/OCR) van giu nguyen do phan giai goc - xem
    get_final_pixmap()."""

    status_message = pyqtSignal(str)
    ocr_requested = pyqtSignal(object)
    zoom_changed = pyqtSignal(float)

    MIN_ZOOM = 0.1
    MAX_ZOOM = 4.0

    def __init__(self, pixmap, parent=None):
        super().__init__(parent)
        self.base_pixmap = pixmap.copy()
        self.zoom = 1.0
        self._apply_zoom_size()

        self.tool = "pen"
        self.pen_color = QColor(255, 0, 0)
        self.pen_width = 3
        self.fill_shape = False

        self.undo_stack = [self.base_pixmap.copy()]
        self.redo_stack = []

        self.drawing = False
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.step_counter = 1

        self.setMouseTracking(True)
        self.setCursor(Qt.CrossCursor)

    # ---------- zoom ----------
    def _apply_zoom_size(self):
        pm = self.current_pixmap() if hasattr(self, "undo_stack") and self.undo_stack else self.base_pixmap
        w = max(1, round(pm.width() * self.zoom))
        h = max(1, round(pm.height() * self.zoom))
        self.setFixedSize(w, h)

    def set_zoom(self, zoom, emit=True):
        self.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, zoom))
        self._apply_zoom_size()
        self.update()
        if emit:
            self.zoom_changed.emit(self.zoom)

    def zoom_in(self):
        self.set_zoom(self.zoom * 1.25)

    def zoom_out(self):
        self.set_zoom(self.zoom / 1.25)

    def zoom_to_fit(self, available_size):
        """Tinh zoom sao cho anh vua khung available_size (khong phong to
        qua 100% neu anh von da nho hon khung)."""
        pm = self.current_pixmap()
        aw, ah = max(1, available_size.width()), max(1, available_size.height())
        fit = min(aw / pm.width(), ah / pm.height())
        self.set_zoom(min(1.0, fit))

    def zoom_actual_size(self):
        self.set_zoom(1.0)

    def _map_to_image(self, pos):
        """Chuyen toa do chuot (khong gian widget da zoom) ve toa do that
        su tren anh goc (khong gian pixmap)."""
        return QPoint(int(pos.x() / self.zoom), int(pos.y() / self.zoom))

    # ---------- helpers ----------
    def current_pixmap(self):
        return self.undo_stack[-1]

    def push_undo(self, pixmap):
        self.undo_stack.append(pixmap)
        self.redo_stack.clear()
        self._apply_zoom_size()
        self.update()

    def undo(self):
        if len(self.undo_stack) > 1:
            self.redo_stack.append(self.undo_stack.pop())
            self._apply_zoom_size()
            self.update()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.redo_stack.pop())
            self._apply_zoom_size()
            self.update()

    def set_tool(self, tool):
        self.tool = tool
        if tool == "picker":
            self.setCursor(Qt.PointingHandCursor)
        elif tool == "text":
            self.setCursor(Qt.IBeamCursor)
        else:
            self.setCursor(Qt.CrossCursor)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    # ---------- painting ----------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.scale(self.zoom, self.zoom)
        painter.drawPixmap(0, 0, self.current_pixmap())
        if self.drawing and self.tool not in ("crop", "blur", "pixelate", "ocr"):
            self._draw_preview(painter)
        elif self.drawing and self.tool in ("crop", "blur", "pixelate", "ocr"):
            pen = QPen(QColor(0, 150, 255), max(1, round(1 / self.zoom)), Qt.DashLine)
            painter.setPen(pen)
            painter.drawRect(QRect(self.start_point, self.end_point))

    def _draw_preview(self, painter):
        pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine,
                    Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        if self.tool == "rect":
            painter.drawRect(QRect(self.start_point, self.end_point))
        elif self.tool == "ellipse":
            painter.drawEllipse(QRect(self.start_point, self.end_point))
        elif self.tool == "line":
            painter.drawLine(self.start_point, self.end_point)
        elif self.tool == "arrow":
            self._draw_arrow(painter, self.start_point, self.end_point)

    def _draw_arrow(self, painter, p1, p2):
        painter.drawLine(p1, p2)
        angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())
        arrow_size = 12 + self.pen_width
        for da in (math.pi / 7, -math.pi / 7):
            ax = p2.x() - arrow_size * math.cos(angle - da)
            ay = p2.y() - arrow_size * math.sin(angle - da)
            painter.drawLine(p2, QPoint(int(ax), int(ay)))

    # ---------- mouse events ----------
    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        pos = self._map_to_image(event.pos())

        if self.tool == "picker":
            color = QColor(self.current_pixmap().toImage().pixel(pos))
            self.pen_color = color
            QApplication.clipboard().setText(color.name())
            self.status_message.emit(f"Da copy ma mau: {color.name()}")
            return

        if self.tool == "text":
            text, ok = QInputDialog.getText(self, "Nhap text", "Noi dung:")
            if ok and text:
                pm = self.current_pixmap().copy()
                painter = QPainter(pm)
                painter.setPen(QPen(self.pen_color))
                font = QFont("Sans", 10 + self.pen_width * 2)
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(pos, text)
                painter.end()
                self.push_undo(pm)
            return

        if self.tool == "step":
            pm = self.current_pixmap().copy()
            painter = QPainter(pm)
            painter.setRenderHint(QPainter.Antialiasing)
            r = 12 + self.pen_width
            painter.setBrush(self.pen_color)
            painter.setPen(QPen(Qt.white, 1))
            painter.drawEllipse(pos, r, r)
            painter.setPen(QPen(Qt.white))
            font = QFont("Sans", 9 + self.pen_width // 2)
            font.setBold(True)
            painter.setFont(font)
            painter.drawText(QRect(pos.x() - r, pos.y() - r, 2 * r, 2 * r),
                              Qt.AlignCenter, str(self.step_counter))
            painter.end()
            self.step_counter += 1
            self.push_undo(pm)
            return

        if self.tool == "pen":
            self.drawing = True
            self.start_point = pos
            self.end_point = pos
            self._free_path = [pos]
            return

        self.drawing = True
        self.start_point = pos
        self.end_point = pos

    def mouseMoveEvent(self, event):
        if not self.drawing:
            return
        pos = self._map_to_image(event.pos())

        if self.tool == "pen":
            pm = self.current_pixmap()
            painter = QPainter(pm)
            pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine,
                       Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.end_point, pos)
            painter.end()
            self.end_point = pos
            self.update()
            return

        if self.tool == "highlighter":
            pm = self.current_pixmap()
            painter = QPainter(pm)
            color = QColor(self.pen_color)
            color.setAlpha(90)
            pen = QPen(color, self.pen_width * 5, Qt.SolidLine,
                       Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawLine(self.end_point, pos)
            painter.end()
            self.end_point = pos
            self.update()
            return

        self.end_point = pos
        self.update()

    def mouseReleaseEvent(self, event):
        if not self.drawing or event.button() != Qt.LeftButton:
            return
        self.drawing = False
        pos = self._map_to_image(event.pos())

        if self.tool in ("pen", "highlighter"):
            self.push_undo(self.current_pixmap().copy())
            return

        rect = QRect(self.start_point, pos).normalized()

        if self.tool in ("rect", "ellipse", "line", "arrow"):
            pm = self.current_pixmap().copy()
            painter = QPainter(pm)
            pen = QPen(self.pen_color, self.pen_width, Qt.SolidLine,
                       Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            if self.tool == "rect":
                painter.drawRect(rect)
            elif self.tool == "ellipse":
                painter.drawEllipse(rect)
            elif self.tool == "line":
                painter.drawLine(self.start_point, pos)
            elif self.tool == "arrow":
                self._draw_arrow(painter, self.start_point, pos)
            painter.end()
            self.push_undo(pm)

        elif self.tool == "crop":
            if rect.width() > 3 and rect.height() > 3:
                cropped = self.current_pixmap().copy(rect)
                self.base_pixmap = cropped
                self.push_undo(cropped)
                self.status_message.emit("Da crop anh")

        elif self.tool in ("blur", "pixelate"):
            if rect.width() > 3 and rect.height() > 3:
                pm = self._apply_censor(self.current_pixmap(), rect, self.tool)
                self.push_undo(pm)

        elif self.tool == "ocr":
            if rect.width() > 3 and rect.height() > 3:
                region = self.current_pixmap().copy(rect)
                self.ocr_requested.emit(region)

        self.update()

    def _apply_censor(self, pixmap, rect, mode):
        """Lam mo/pixelate 1 vung cua anh bang cach scale down/up."""
        pm = pixmap.copy()
        region = pm.copy(rect)
        img = region.toImage().convertToFormat(QImage.Format_RGB32)
        w, h = max(1, img.width()), max(1, img.height())

        block = max(4, min(w, h) // 15) if mode == "pixelate" else max(3, min(w, h) // 25)
        small = img.scaled(max(1, w // block), max(1, h // block),
                            Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        result = small.scaled(w, h, Qt.IgnoreAspectRatio,
                               Qt.FastTransformation if mode == "pixelate" else Qt.SmoothTransformation)

        painter = QPainter(pm)
        painter.drawImage(rect.topLeft(), result)
        painter.end()
        return pm

    def get_final_pixmap(self):
        return self.current_pixmap()


# ---------------------------------------------------------------------------
# Bang mau / theme
# ---------------------------------------------------------------------------
BG_DARK = "#20232a"
BG_TOOLBAR = "#262a33"
BG_HOVER = "#33394a"
BG_CHECKED = "#3d6bff"
BORDER = "#3a3f4b"
TEXT_MUTED = "#9aa0ac"
ICON_COLOR = "#e8eaf0"
ICON_COLOR_CHECKED = "#ffffff"
CANVAS_BG = "#14161b"

APP_QSS = f"""
QMainWindow {{
    background: {CANVAS_BG};
}}
QToolBar {{
    background: {BG_TOOLBAR};
    border: none;
    border-bottom: 1px solid {BORDER};
    padding: 6px 8px;
    spacing: 4px;
}}
QToolButton {{
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 6px;
    margin: 0px 1px;
}}
QToolButton:hover {{
    background: {BG_HOVER};
    border: 1px solid {BORDER};
}}
QToolButton:checked {{
    background: {BG_CHECKED};
    border: 1px solid {BG_CHECKED};
}}
QToolButton:pressed {{
    background: {BG_HOVER};
}}
QLabel {{
    color: {TEXT_MUTED};
    font-size: 12px;
}}
QSpinBox {{
    background: {BG_DARK};
    color: {ICON_COLOR};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 3px 6px;
    min-width: 42px;
}}
QSpinBox::up-button, QSpinBox::down-button {{
    width: 14px;
    background: {BG_HOVER};
    border-left: 1px solid {BORDER};
}}
QStatusBar {{
    background: {BG_TOOLBAR};
    color: {TEXT_MUTED};
    border-top: 1px solid {BORDER};
    padding: 4px 10px;
}}
QScrollArea {{
    background: {CANVAS_BG};
    border: none;
}}
QScrollArea > QWidget > QWidget {{
    background: {CANVAS_BG};
}}
QMenu {{
    background: {BG_TOOLBAR};
    color: {ICON_COLOR};
    border: 1px solid {BORDER};
}}
QMenu::item:selected {{
    background: {BG_CHECKED};
}}
"""


def _vsep():
    line = QFrame()
    line.setFrameShape(QFrame.VLine)
    line.setFrameShadow(QFrame.Plain)
    line.setStyleSheet(f"color: {BORDER}; margin: 4px 6px;")
    return line


class EditorWindow(QMainWindow):
    TOOL_DEFS = [
        # (key, tooltip, shortcut-hint)
        ("pen", "But ve tu do"),
        ("line", "Duong thang"),
        ("arrow", "Mui ten"),
        ("rect", "Hinh chu nhat"),
        ("ellipse", "Hinh tron / oval"),
        ("highlighter", "Highlight (danh dau)"),
        None,
        ("text", "Chen text"),
        ("step", "Danh so buoc"),
        None,
        ("blur", "Lam mo vung anh"),
        ("pixelate", "Pixelate (che thong tin)"),
        ("crop", "Crop / cat anh"),
        ("picker", "Lay ma mau (color picker)"),
        ("ocr", "OCR vung chon (keo tha chon vung)"),
    ]

    def __init__(self, image_path):
        super().__init__()
        self.setWindowTitle("Mini Screenshot Editor")
        self.setStyleSheet(APP_QSS)

        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            QMessageBox.critical(self, "Loi", f"Khong doc duoc anh: {image_path}")
            sys.exit(1)

        self.canvas = Canvas(pixmap)
        self.canvas.status_message.connect(
            lambda msg: self.statusBar().showMessage(msg, 4000)
        )
        self.canvas.ocr_requested.connect(self._run_ocr)

        scroll = QScrollArea()
        scroll.setWidget(self.canvas)
        scroll.setWidgetResizable(False)
        scroll.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(scroll)

        self._tool_buttons = {}
        self._build_toolbar()
        self.canvas.zoom_changed.connect(self._update_zoom_label)
        self.setStatusBar(QStatusBar())

        screen = QApplication.primaryScreen().availableGeometry()
        # Chua toolbar/statusbar/khung cua so - danh khoang trong cho chung
        # khi tinh khung hinh vua man hinh cho phan xem (canvas).
        chrome_w, chrome_h = 60, 140
        avail_w = max(320, screen.width() - 60 - chrome_w)
        avail_h = max(240, screen.height() - 60 - chrome_h)

        if pixmap.width() > avail_w or pixmap.height() > avail_h:
            self.canvas.zoom_to_fit(QSize(avail_w, avail_h))
            self.statusBar().showMessage(
                f"Anh lon ({pixmap.width()}x{pixmap.height()}) - da thu nho "
                f"phan xem con {int(self.canvas.zoom * 100)}% cho vua man "
                f"hinh (chat luong luu/copy van giu nguyen). Ctrl+lan chuot "
                f"hoac nut zoom tren toolbar de phong to/thu nho.",
                8000,
            )
        else:
            self.statusBar().showMessage("San sang. Chon cong cu va ve len anh.", 4000)

        w = min(self.canvas.width() + chrome_w, screen.width() - 60)
        h = min(self.canvas.height() + chrome_h, screen.height() - 60)
        self.resize(max(w, 640), max(h, 480))

    # ---------------- toolbar ----------------
    def _build_toolbar(self):
        tb = QToolBar("Cong cu")
        tb.setMovable(False)
        tb.setIconSize(QSize(20, 20))
        tb.setToolButtonStyle(Qt.ToolButtonIconOnly)
        self.addToolBar(Qt.TopToolBarArea, tb)

        group = QActionGroup(self)
        group.setExclusive(True)

        for entry in self.TOOL_DEFS:
            if entry is None:
                tb.addWidget(_vsep())
                continue
            key, tooltip = entry
            icon = icons.make_icon(key, color=ICON_COLOR)
            act = QAction(icon, "", self, checkable=True)
            act.setToolTip(tooltip)
            act.triggered.connect(lambda checked, k=key: self.canvas.set_tool(k))
            group.addAction(act)
            tb.addAction(act)
            btn = tb.widgetForAction(act)
            if btn:
                btn.setFixedSize(38, 38)
                btn.setIconSize(QSize(20, 20))
            self._tool_buttons[key] = act
            if key == "pen":
                act.setChecked(True)

        tb.addWidget(_vsep())

        # --- mau + do day net ---
        self.color_btn = QToolButton()
        self.color_btn.setFixedSize(38, 38)
        self.color_btn.setToolTip("Chon mau")
        self.color_btn.setIcon(icons.color_swatch_icon(self.canvas.pen_color))
        self.color_btn.setIconSize(QSize(22, 22))
        self.color_btn.clicked.connect(self._choose_color)
        tb.addWidget(self.color_btn)

        tb.addWidget(QLabel("  Do day "))
        spin = QSpinBox()
        spin.setRange(1, 20)
        spin.setValue(3)
        spin.setToolTip("Do day net ve")
        spin.valueChanged.connect(lambda v: setattr(self.canvas, "pen_width", v))
        tb.addWidget(spin)

        tb.addWidget(_vsep())

        # --- undo / redo ---
        undo_act = QAction(icons.make_icon("undo", color=ICON_COLOR), "", self)
        undo_act.setToolTip("Undo (Ctrl+Z)")
        undo_act.setShortcut("Ctrl+Z")
        undo_act.triggered.connect(self.canvas.undo)
        tb.addAction(undo_act)
        self._style_action_button(tb, undo_act)

        redo_act = QAction(icons.make_icon("redo", color=ICON_COLOR), "", self)
        redo_act.setToolTip("Redo (Ctrl+Shift+Z)")
        redo_act.setShortcut("Ctrl+Shift+Z")
        redo_act.triggered.connect(self.canvas.redo)
        tb.addAction(redo_act)
        self._style_action_button(tb, redo_act)

        tb.addWidget(_vsep())

        # --- zoom ---
        zoom_out_btn = QToolButton()
        zoom_out_btn.setText("−")
        zoom_out_btn.setToolTip("Thu nho (Ctrl+lăn chuột xuống)")
        zoom_out_btn.setFixedSize(30, 30)
        zoom_out_btn.clicked.connect(self.canvas.zoom_out)
        tb.addWidget(zoom_out_btn)

        self.zoom_label = QToolButton()
        self.zoom_label.setText("100%")
        self.zoom_label.setToolTip("Bấm để về 100% (kích thước thật)")
        self.zoom_label.setFixedSize(56, 30)
        self.zoom_label.clicked.connect(self.canvas.zoom_actual_size)
        tb.addWidget(self.zoom_label)

        zoom_in_btn = QToolButton()
        zoom_in_btn.setText("+")
        zoom_in_btn.setToolTip("Phóng to (Ctrl+lăn chuột lên)")
        zoom_in_btn.setFixedSize(30, 30)
        zoom_in_btn.clicked.connect(self.canvas.zoom_in)
        tb.addWidget(zoom_in_btn)

        fit_btn = QToolButton()
        fit_btn.setText("⤢")
        fit_btn.setToolTip("Thu vừa khung cửa sổ")
        fit_btn.setFixedSize(30, 30)
        fit_btn.clicked.connect(self._zoom_fit_to_window)
        tb.addWidget(fit_btn)

        # --- spacer de day export sang phai ---
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)

        # --- export ---
        save_act = QAction(icons.make_icon("save", color=ICON_COLOR), "", self)
        save_act.setToolTip("Luu file (Ctrl+S)")
        save_act.setShortcut("Ctrl+S")
        save_act.triggered.connect(self._save_file)
        tb.addAction(save_act)
        self._style_action_button(tb, save_act)

        copy_act = QAction(icons.make_icon("copy", color=ICON_COLOR), "", self)
        copy_act.setToolTip("Copy vao clipboard (Ctrl+C)")
        copy_act.setShortcut("Ctrl+C")
        copy_act.triggered.connect(self._copy_clipboard)
        tb.addAction(copy_act)
        self._style_action_button(tb, copy_act)

        ocr_act = QAction(icons.make_icon("ocr", color=ICON_COLOR), "", self)
        ocr_act.setToolTip("Extract Text — OCR toan anh")
        ocr_act.triggered.connect(self._ocr_full_image)
        tb.addAction(ocr_act)
        self._style_action_button(tb, ocr_act)

    def _style_action_button(self, tb, action):
        btn = tb.widgetForAction(action)
        if btn:
            btn.setFixedSize(38, 38)
            btn.setIconSize(QSize(20, 20))

    def _update_zoom_label(self, zoom):
        self.zoom_label.setText(f"{int(round(zoom * 100))}%")

    def _zoom_fit_to_window(self):
        # Dung kich thuoc vung cuon hien tai lam khung tham chieu.
        viewport = self.centralWidget()
        size = viewport.viewport().size() if hasattr(viewport, "viewport") else viewport.size()
        self.canvas.zoom_to_fit(size)

    def _choose_color(self):
        color = QColorDialog.getColor(self.canvas.pen_color, self, "Chon mau")
        if color.isValid():
            self.canvas.pen_color = color
            self.color_btn.setIcon(icons.color_swatch_icon(color))

    def _save_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Luu anh", "screenshot.png", "PNG Files (*.png);;JPEG Files (*.jpg)"
        )
        if path:
            self.canvas.get_final_pixmap().save(path)
            self.statusBar().showMessage(f"Da luu: {path}", 4000)

    def _ocr_full_image(self):
        self._run_ocr(self.canvas.get_final_pixmap())

    def _run_ocr(self, pixmap):
        missing = ocr.missing_dependencies()
        if missing:
            lines = []
            if "tesseract-ocr" in missing:
                lines.append("sudo apt install tesseract-ocr")
            if "python3-pytesseract" in missing:
                lines.append("pip3 install --break-system-packages pytesseract")
            QMessageBox.warning(
                self, "Thieu OCR",
                "Can cai dat:\n  " + "\n  ".join(lines),
            )
            return

        self.statusBar().showMessage("Dang chay OCR...", 0)
        QApplication.processEvents()
        try:
            text = ocr.extract_text(pixmap)
        except Exception as e:
            self.statusBar().clearMessage()
            QMessageBox.critical(self, "Loi OCR", str(e))
            return

        self.statusBar().showMessage(
            f"OCR xong — {len(text)} ky tu" if text else "OCR xong — khong tim thay text",
            4000,
        )
        dlg = OcrResultDialog(text, self)
        dlg.exec_()

    def _copy_clipboard(self):
        image = self.canvas.get_final_pixmap().toImage()
        QApplication.clipboard().setImage(image)

        # wl-copy de paste sang app khac tren Wayland (Qt clipboard khong
        # luon duoc app ngoai doc).
        tmp = "/tmp/_mini_screenshot_clip.png"
        try:
            self.canvas.get_final_pixmap().save(tmp)
            clipboard_util.copy_png_file(tmp)
        finally:
            try:
                os.remove(tmp)
            except OSError:
                pass

        self.statusBar().showMessage("Da copy anh vao clipboard", 4000)


def launch_editor(image_path):
    app = QApplication.instance() or QApplication(sys.argv)
    win = EditorWindow(image_path)
    win.show()
    return app, win
