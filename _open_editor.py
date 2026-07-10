#!/usr/bin/env python3
"""
_open_editor.py

Chi lam 1 viec: nhan duong dan anh qua argv, mo EditorWindow (editor.py)
va chay Qt event loop cua rieng no. Duoc tray.py goi bang subprocess.Popen
de khong bi xung dot voi Gtk.main() dang chay trong tien trinh tray.
"""
import sys
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
