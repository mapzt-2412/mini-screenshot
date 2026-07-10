"""Vector toolbar icons drawn with QPainter (no emoji/font dependency)."""

import math

from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import (
    QColor, QFont, QIcon, QPainter, QPainterPath, QPen, QPixmap,
)


def _canvas(size=28):
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    return pm, p


def _finish(pm, p):
    p.end()
    return QIcon(pm)


def icon_pen(color="#e8e8e8", size=28):
    pm, p = _canvas(size)
    pen = QPen(QColor(color), 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    path = QPainterPath()
    path.moveTo(6, 22)
    path.cubicTo(10, 18, 14, 12, 20, 6)
    p.drawPath(path)
    p.setBrush(QColor(color))
    p.drawEllipse(QPointF(21, 5), 2.3, 2.3)
    return _finish(pm, p)


def icon_line(color="#e8e8e8", size=28):
    pm, p = _canvas(size)
    p.setPen(QPen(QColor(color), 2.4, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(6, 22, 22, 6)
    return _finish(pm, p)


def icon_arrow(color="#e8e8e8", size=28):
    pm, p = _canvas(size)
    p.setPen(QPen(QColor(color), 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawLine(6, 22, 21, 7)
    angle = math.atan2(7 - 22, 21 - 6)
    tip = QPointF(21, 7)
    for da in (0.5, -0.5):
        ax = tip.x() - 7 * math.cos(angle - da)
        ay = tip.y() - 7 * math.sin(angle - da)
        p.drawLine(tip, QPointF(ax, ay))
    return _finish(pm, p)


def icon_rect(color="#e8e8e8", size=28):
    pm, p = _canvas(size)
    p.setPen(QPen(QColor(color), 2.2))
    p.drawRoundedRect(QRectF(5, 7, 18, 14), 2, 2)
    return _finish(pm, p)


def icon_ellipse(color="#e8e8e8", size=28):
    pm, p = _canvas(size)
    p.setPen(QPen(QColor(color), 2.2))
    p.drawEllipse(QRectF(5, 7, 18, 14))
    return _finish(pm, p)


def icon_highlighter(color="#e8e8e8", size=28):
    pm, p = _canvas(size)
    hl = QColor("#ffd23f")
    hl.setAlpha(210)
    p.setPen(Qt.NoPen)
    p.setBrush(hl)
    p.drawRect(6, 17, 16, 6)
    p.setPen(QPen(QColor(color), 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawLine(9, 17, 19, 7)
    p.drawLine(19, 7, 22, 10)
    p.drawLine(22, 10, 12, 20)
    return _finish(pm, p)


def icon_text(color="#e8e8e8", size=28):
    pm, p = _canvas(size)
    p.setPen(QPen(QColor(color), 2.0, Qt.SolidLine, Qt.RoundCap))
    font = QFont("Sans", 14, QFont.Bold)
    p.setFont(font)
    p.drawText(pm.rect(), Qt.AlignCenter, "T")
    return _finish(pm, p)


def icon_step(color="#e8e8e8", size=28):
    pm, p = _canvas(size)
    p.setPen(QPen(QColor(color), 2.0))
    p.setBrush(QColor(color))
    p.drawEllipse(QRectF(5, 5, 18, 18))
    p.setPen(QPen(QColor("#1c1c1c"), 1))
    font = QFont("Sans", 9, QFont.Bold)
    p.setFont(font)
    p.drawText(pm.rect(), Qt.AlignCenter, "1")
    return _finish(pm, p)


def icon_blur(color="#e8e8e8", size=28):
    pm, p = _canvas(size)
    p.setPen(Qt.NoPen)
    c = QColor(color)
    for i, (dx, dy, r, a) in enumerate([
        (10, 10, 6, 60), (16, 12, 7, 90), (13, 17, 6, 130), (18, 18, 5, 180)
    ]):
        c2 = QColor(c)
        c2.setAlpha(a)
        p.setBrush(c2)
        p.drawEllipse(QPointF(dx, dy), r * 0.5, r * 0.5)
    return _finish(pm, p)


def icon_pixelate(color="#e8e8e8", size=28):
    pm, p = _canvas(size)
    p.setPen(Qt.NoPen)
    c = QColor(color)
    blocks = [(6, 6, 210), (13, 6, 120), (20, 6, 180),
              (6, 13, 150), (13, 13, 230), (20, 13, 100),
              (6, 20, 190), (13, 20, 140), (20, 20, 210)]
    for x, y, a in blocks:
        c2 = QColor(c)
        c2.setAlpha(a)
        p.setBrush(c2)
        p.drawRect(x, y, 6, 6)
    return _finish(pm, p)


def icon_crop(color="#e8e8e8", size=28):
    pm, p = _canvas(size)
    pen = QPen(QColor(color), 2.2, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
    p.setPen(pen)
    # goc trai-tren
    p.drawLine(8, 5, 8, 8)
    p.drawLine(8, 8, 5, 8)
    p.drawLine(5, 8, 5, 20)
    p.drawLine(5, 20, 8, 20)
    # goc phai-duoi
    p.drawLine(20, 8, 23, 8)
    p.drawLine(23, 8, 23, 20)
    p.drawLine(23, 20, 20, 20)
    p.drawLine(8, 5, 20, 5)
    return _finish(pm, p)


def icon_picker(color="#e8e8e8", size=28):
    pm, p = _canvas(size)
    p.setPen(QPen(QColor(color), 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.drawLine(8, 20, 15, 13)
    p.setBrush(QColor(color))
    p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(19, 9), 4.5, 4.5)
    p.setPen(QPen(QColor(color), 2.0, Qt.SolidLine, Qt.RoundCap))
    p.drawLine(6, 22, 9, 19)
    return _finish(pm, p)


def icon_undo(color="#e8e8e8", size=28):
    pm, p = _canvas(size)
    p.setPen(QPen(QColor(color), 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(6, 6, 16, 16), 30 * 16, 260 * 16)
    p.setBrush(QColor(color))
    p.setPen(Qt.NoPen)
    path = QPainterPath()
    path.moveTo(9, 6)
    path.lineTo(4, 9)
    path.lineTo(9, 13)
    path.closeSubpath()
    p.drawPath(path)
    return _finish(pm, p)


def icon_redo(color="#e8e8e8", size=28):
    pm, p = _canvas(size)
    p.setPen(QPen(QColor(color), 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(6, 6, 16, 16), (180 - 30) * 16, 260 * 16)
    p.setBrush(QColor(color))
    p.setPen(Qt.NoPen)
    path = QPainterPath()
    path.moveTo(19, 6)
    path.lineTo(24, 9)
    path.lineTo(19, 13)
    path.closeSubpath()
    p.drawPath(path)
    return _finish(pm, p)


def icon_save(color="#e8e8e8", size=28):
    pm, p = _canvas(size)
    p.setPen(QPen(QColor(color), 2.0, Qt.SolidLine, Qt.SquareCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(QRectF(5, 5, 18, 18), 2, 2)
    p.setBrush(QColor(color))
    p.setPen(Qt.NoPen)
    p.drawRect(9, 5, 10, 6)
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(QColor("#1c1c1c"), 1.6))
    p.drawRect(9, 15, 10, 7)
    return _finish(pm, p)


def icon_copy(color="#e8e8e8", size=28):
    pm, p = _canvas(size)
    p.setPen(QPen(QColor(color), 2.0, Qt.SolidLine, Qt.SquareCap, Qt.RoundJoin))
    p.drawRoundedRect(QRectF(9, 9, 14, 15), 2, 2)
    p.drawRoundedRect(QRectF(5, 4, 14, 15), 2, 2)
    return _finish(pm, p)


def icon_ocr(color="#e8e8e8", size=28):
    """Icon chu 'T' trong khung + duong scan (Extract Text)."""
    pm, p = _canvas(size)
    p.setPen(QPen(QColor(color), 2.0, Qt.SolidLine, Qt.SquareCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(QRectF(5, 5, 18, 18), 2, 2)
    font = QFont("Sans", 11, QFont.Bold)
    p.setFont(font)
    p.drawText(QRectF(5, 4, 18, 14), Qt.AlignCenter, "T")
    pen = QPen(QColor(color), 1.4, Qt.SolidLine, Qt.RoundCap)
    p.setPen(pen)
    for y in (17, 20):
        p.drawLine(8, y, 20, y)
    return _finish(pm, p)


ICON_MAKERS = {
    "pen": icon_pen,
    "line": icon_line,
    "arrow": icon_arrow,
    "rect": icon_rect,
    "ellipse": icon_ellipse,
    "highlighter": icon_highlighter,
    "text": icon_text,
    "step": icon_step,
    "blur": icon_blur,
    "pixelate": icon_pixelate,
    "crop": icon_crop,
    "picker": icon_picker,
    "undo": icon_undo,
    "redo": icon_redo,
    "save": icon_save,
    "copy": icon_copy,
    "ocr": icon_ocr,
}


def make_icon(key, color="#e8e8e8", size=28):
    maker = ICON_MAKERS.get(key)
    if maker is None:
        raise ValueError(f"Khong co icon cho: {key}")
    return maker(color=color, size=size)


def color_swatch_icon(qcolor, size=22):
    """Icon hinh vuong bo tron the hien mau hien tai (dung cho nut chon mau)."""
    pm, p = _canvas(size)
    p.setPen(QPen(QColor("#555555"), 1.4))
    p.setBrush(qcolor)
    p.drawRoundedRect(QRectF(2, 2, size - 4, size - 4), 4, 4)
    return _finish(pm, p)
