"""Extract text from images via pytesseract + tesseract-ocr."""

import io
import shutil
import subprocess

from PyQt5.QtGui import QPixmap


def is_available():
    """Return True if tesseract and pytesseract are available."""
    if shutil.which("tesseract") is None:
        return False
    try:
        import pytesseract  # noqa: F401
        return True
    except ImportError:
        return False


def missing_dependencies():
    """Tra ve danh sach goi/thu vien con thieu."""
    missing = []
    if shutil.which("tesseract") is None:
        missing.append("tesseract-ocr")
    try:
        import pytesseract  # noqa: F401
    except ImportError:
        missing.append("python3-pytesseract")
    return missing


def _default_lang():
    """Chon ngon ngu OCR: eng+vie neu co traineddata, khong thi eng."""
    try:
        out = subprocess.run(
            ["tesseract", "--list-langs"],
            capture_output=True, text=True, check=False,
        )
        langs = out.stdout.splitlines()
        has_eng = any(l.strip() == "eng" for l in langs)
        has_vie = any(l.strip() == "vie" for l in langs)
        if has_eng and has_vie:
            return "eng+vie"
        if has_vie:
            return "vie"
        if has_eng:
            return "eng"
    except OSError:
        pass
    return "eng"


def pixmap_to_pil(pixmap):
    """Chuyen QPixmap sang PIL Image."""
    from PIL import Image
    from PyQt5.QtCore import QBuffer, QIODevice

    buf = QBuffer()
    buf.open(QIODevice.WriteOnly)
    pixmap.save(buf, "PNG")
    return Image.open(io.BytesIO(buf.data()))


def extract_text(pixmap, lang=None):
    """
  Trich xuat text tu QPixmap.
  Tra ve chuoi text (da strip). Neu khong doc duoc gi, tra ve "".
    """
    import pytesseract

    if lang is None:
        lang = _default_lang()

    img = pixmap_to_pil(pixmap)
    text = pytesseract.image_to_string(img, lang=lang)
    return text.strip()
