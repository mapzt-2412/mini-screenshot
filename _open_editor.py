#!/usr/bin/env python3
"""
_open_editor.py

Chi lam 1 viec: nhan duong dan anh qua argv, mo EditorWindow (editor.py)
va chay Qt event loop cua rieng no. Duoc tray.py goi bang subprocess.Popen
de khong bi xung dot voi Gtk.main() dang chay trong tien trinh tray.
"""
import sys
import os

# Xem giai thich chi tiet trong main.py - ep Qt chay qua XWayland de tranh
# loi cua so/dialog khong nhan focus tren GNOME Wayland. Phai set truoc
# khi import editor.py (vi editor.py import PyQt5).
if os.environ.get("WAYLAND_DISPLAY") and not os.environ.get("QT_QPA_PLATFORM"):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

from editor import launch_editor


def main():
    if len(sys.argv) < 2:
        print("Usage: _open_editor.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    app, win = launch_editor(image_path)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
