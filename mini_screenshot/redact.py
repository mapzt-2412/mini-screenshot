"""Auto-detect likely-sensitive text regions (email / phone / card number)
in a screenshot via OCR word boxes + regex, so the editor can blur them
with one click.

Detection is intentionally conservative (regex-based, not a full PII
model) — false negatives are expected; this is a time-saver, not a
guarantee. Always let the user review the result before sharing.
"""

import re

from PyQt5.QtCore import QRect

from .ocr import _default_lang, pixmap_to_pil

PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    # VN mobile: 0xxxxxxxxx / +84xxxxxxxxx (9-10 digits after prefix)
    "phone_vn": re.compile(r"(?:\+84|0)(?:\d[\s.-]?){9,10}"),
    # Generic card-like run of 13-19 digits, optionally grouped by 4.
    "card": re.compile(r"\b(?:\d[ -]?){13,19}\b"),
    # VN CCCD/CMND: 9 or 12 digits standalone.
    "cccd": re.compile(r"\b\d{12}\b|\b\d{9}\b"),
}


def _matches_any(text):
    for pat in PATTERNS.values():
        if pat.search(text):
            return True
    return False


def find_sensitive_regions(pixmap, lang=None):
    """Return a list of ``QRect`` (image coordinates) around text that
    looks sensitive, using tesseract's per-word bounding boxes grouped
    by line (so multi-word matches like "0901 234 567" are still caught).
    """
    import pytesseract

    if lang is None:
        lang = _default_lang()

    img = pixmap_to_pil(pixmap)
    data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)

    n = len(data.get("text", []))
    boxes = []

    line_key = None
    buf_words = []
    buf_rect = None

    def flush():
        if buf_words and buf_rect is not None:
            joined = " ".join(buf_words)
            if _matches_any(joined):
                boxes.append(buf_rect)

    for i in range(n):
        text = (data["text"][i] or "").strip()
        key = (data.get("block_num", [0] * n)[i],
               data.get("par_num", [0] * n)[i],
               data.get("line_num", [0] * n)[i])
        if key != line_key:
            flush()
            buf_words.clear()
            buf_rect = None
            line_key = key
        if not text:
            continue
        x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
        r = QRect(x, y, w, h)
        buf_rect = buf_rect.united(r) if buf_rect is not None else r
        buf_words.append(text)

    flush()
    return boxes
