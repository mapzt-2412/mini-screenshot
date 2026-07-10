#!/usr/bin/env python3
"""CLI entry for Mini Screenshot (Ubuntu / Wayland).

Usage:
    python3 main.py                 # region (default)
    python3 main.py --full          # fullscreen
    python3 main.py --window        # window picker on GNOME; click on wlroots
    python3 main.py --window --mac-style
    python3 main.py --delay 3
    python3 main.py --tray          # system tray

After capture, the Edit window opens for annotation.
"""

import argparse
import os
import sys

from .qt_env import ensure_qt_platform

ensure_qt_platform()

from . import capture
from .editor import launch_editor


def parse_args():
    parser = argparse.ArgumentParser(description="Mini Screenshot Tool (Wayland)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--full", action="store_true", help="Chup toan man hinh")
    mode.add_argument("--window", action="store_true", help="Chup 1 cua so cu the")
    parser.add_argument("--delay", type=int, default=0,
                         help="So giay cho truoc khi chup")
    parser.add_argument("--mac-style", action="store_true",
                         help="Chi ap dung voi --window: bo goc + drop shadow "
                              "+ nen trong suot kieu macOS")
    parser.add_argument("--tray", action="store_true",
                         help="Mo icon tren system tray (topbar) thay vi chup ngay")
    return parser.parse_args()


def _pick_window_gnome():
    """Show a PyQt dialog to pick a window from the wmctrl list.

    Returns win_id, or None if wmctrl is missing, no windows, or Cancel.
    """
    windows = capture.list_windows()

    if windows is None:
        print("Luu y: chua cai 'wmctrl' nen khong the liet ke cua so de chon.")
        print("Cai dat: sudo apt install wmctrl")
        print("-> Se chup cua so dang active thay the.")
        return None

    if not windows:
        print("Khong tim thay cua so nao de chon (co the do gioi han Wayland: "
              "wmctrl chi thay cua so chay qua XWayland).")
        print("-> Se chup cua so dang active thay the.")
        return None

    from PyQt5.QtCore import Qt
    from PyQt5.QtWidgets import QApplication, QInputDialog

    app = QApplication.instance() or QApplication(sys.argv)
    titles = [title for _win_id, title in windows]

    dlg = QInputDialog()
    dlg.setWindowTitle("Chon cua so can chup")
    dlg.setLabelText("Chon 1 cua so trong danh sach:")
    dlg.setComboBoxItems(titles)
    dlg.setOption(QInputDialog.UseListViewForComboBoxItems, True)
    dlg.setWindowModality(Qt.ApplicationModal)
    # Keep dialog on top + focused — GNOME Wayland often skips focus for new windows.
    dlg.setWindowFlags(dlg.windowFlags() | Qt.WindowStaysOnTopHint)
    dlg.show()
    dlg.raise_()
    dlg.activateWindow()

    ok = dlg.exec_()
    choice = dlg.textValue()
    if not ok or not choice:
        return None

    for win_id, title in windows:
        if title == choice:
            return win_id
    return None


def main():
    args = parse_args()

    if args.tray:
        from . import tray
        return tray.main()

    missing = capture.check_dependencies()
    if missing:
        print("Thieu cong cu he thong: " + ", ".join(missing))
        print("Cai dat bang: sudo apt install " + " ".join(missing))
        sys.exit(1)

    mode = "fullscreen" if args.full else ("window" if args.window else "region")

    if args.mac_style and mode != "window":
        print("Luu y: --mac-style chi co tac dung voi --window, se bi bo qua.")

    if mode == "window" and capture._is_gnome():
        win_id = _pick_window_gnome()
        if win_id:
            if args.delay > 0:
                print(f"Se chup sau {args.delay} giay...")
            image_path = capture.capture_window_by_id(
                win_id, mac_style=args.mac_style, delay=args.delay
            )
        elif args.delay > 0:
            print(f"Se chup sau {args.delay} giay...")
            image_path = capture.capture_with_delay(
                args.delay, mode=mode, mac_style=args.mac_style
            )
        else:
            image_path = capture.capture_window(mac_style=args.mac_style)
    elif args.delay > 0:
        print(f"Se chup sau {args.delay} giay...")
        image_path = capture.capture_with_delay(args.delay, mode=mode,
                                                  mac_style=args.mac_style)
    elif mode == "fullscreen":
        image_path = capture.capture_fullscreen()
    elif mode == "window":
        image_path = capture.capture_window(mac_style=args.mac_style)
    else:
        image_path = capture.capture_region()

    if not image_path or not os.path.exists(image_path):
        print("Da huy chup man hinh (khong co vung nao duoc chon).")
        sys.exit(0)

    app, win = launch_editor(image_path)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
