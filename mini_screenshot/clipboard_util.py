#!/usr/bin/env python3
"""Copy PNG to clipboard (Wayland / X11) and show a short notification.

Priority: wl-copy → Gtk.Clipboard → xclip → Qt clipboard (needs Qt loop).
"""

import os
import subprocess
import sys


def _copy_wl(path):
    if not os.environ.get("WAYLAND_DISPLAY"):
        return False
    try:
        with open(path, "rb") as f:
            result = subprocess.run(
                ["wl-copy", "--type", "image/png"],
                stdin=f,
                check=False,
                capture_output=True,
            )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def _copy_gtk(path):
    try:
        import gi

        gi.require_version("Gtk", "3.0")
        from gi.repository import Gdk, GdkPixbuf, Gtk
    except Exception:
        return False

    try:
        # Can display connection; tray da Gtk.init qua Gtk.main.
        if not Gtk.init_check(sys.argv)[0] and Gdk.Display.get_default() is None:
            return False
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_image(pixbuf)
        # Luu vao clipboard manager de van paste duoc neu owner thoat.
        clipboard.store()
        return True
    except Exception:
        return False


def _copy_xclip(path):
    try:
        with open(path, "rb") as f:
            result = subprocess.run(
                ["xclip", "-selection", "clipboard", "-t", "image/png", "-i"],
                stdin=f,
                check=False,
                capture_output=True,
            )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def _copy_qt(path):
    try:
        from PyQt5.QtGui import QImage
        from PyQt5.QtWidgets import QApplication

        app = QApplication.instance() or QApplication(sys.argv)
        image = QImage(path)
        if image.isNull():
            return False
        app.clipboard().setImage(image)
        return True
    except Exception:
        return False


def copy_png_file(path):
    """Copy image at path to clipboard. Returns True if at least one method worked."""
    if not path or not os.path.exists(path):
        return False

    for fn in (_copy_wl, _copy_gtk, _copy_xclip, _copy_qt):
        if fn(path):
            return True
    return False


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
