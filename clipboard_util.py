#!/usr/bin/env python3
"""Copy PNG to clipboard (wl-copy + Qt) and show a short notification."""

import os
import subprocess
import sys


def copy_png_file(path):
    """Copy image at path to clipboard. Returns True if at least one method worked."""
    if not path or not os.path.exists(path):
        return False

    ok = False
    try:
        with open(path, "rb") as f:
            result = subprocess.run(
                ["wl-copy", "--type", "image/png"],
                stdin=f,
                check=False,
            )
        if result.returncode == 0:
            ok = True
    except FileNotFoundError:
        pass

    if not ok:
        try:
            from PyQt5.QtGui import QImage
            from PyQt5.QtWidgets import QApplication

            app = QApplication.instance() or QApplication(sys.argv)
            image = QImage(path)
            if not image.isNull():
                app.clipboard().setImage(image)
                ok = True
        except Exception:
            pass

    return ok


def notify(title, body):
    try:
        subprocess.run(
            ["notify-send", title, body],
            check=False,
            capture_output=True,
        )
    except FileNotFoundError:
        print(f"{title}: {body}", flush=True)


def copy_capture_to_clipboard(path, cleanup=True):
    """Copy capture PNG, optionally delete it, notify. Returns True on success."""
    ok = copy_png_file(path)
    if cleanup and path and os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass
    if ok:
        notify("Mini Screenshot", "Đã copy vào clipboard")
    else:
        notify("Mini Screenshot", "Không copy được vào clipboard")
    return ok
