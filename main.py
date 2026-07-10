#!/usr/bin/env python3
"""
main.py - Mini Screenshot Tool cho Ubuntu (Wayland)

Cach dung:
    python3 main.py                 # chup vung chon (mac dinh)
    python3 main.py --full          # chup toan man hinh
    python3 main.py --window        # chup 1 cua so (co popup cho chon cua so tren GNOME)
    python3 main.py --window --mac-style   # chup 1 cua so, bo goc + shadow + nen trong suot kieu macOS
    python3 main.py --delay 3       # doi 3 giay roi chup vung chon
    python3 main.py --delay 3 --full
    python3 main.py --tray          # mo icon tren system tray (topbar) de chon mode bang menu

Che do --window:
    - Tren GNOME (mac dinh Ubuntu): se hien 1 popup liet ke cac cua so dang
      mo (qua wmctrl) de ban CHON dung cua so muon chup, roi tu dong focus
      + chup cua so do. Neu chua cai wmctrl, se fallback ve chup cua so
      dang active (giong hanh vi cu).
    - Tren Sway/Hyprland (wlroots): giu nguyen slurp -w, cho click chon
      truc tiep 1 cua so bat ky tren man hinh.

Sau khi chup, cua so Edit se tu mo de ban ve/annotate.
"""

import argparse
import sys
import os

# QUAN TRONG: phai set truoc khi PyQt5 duoc import (o day hoac o cac module
# duoc import ben duoi nhu editor.py). Tren GNOME Wayland, app PyQt5 chay
# bang plugin 'wayland' doi khi bi loi khong nhan duoc focus/click cho cua
# so moi mo (dialog, popup...) - cua so hien ra nhung bam vao vo tri. Ep
# Qt chay qua XWayland (platform 'xcb') giai quyet duoc loi nay trong da
# so truong hop. Neu ban da tu set QT_QPA_PLATFORM roi thi giu nguyen,
# khong ghi de.
if os.environ.get("WAYLAND_DISPLAY") and not os.environ.get("QT_QPA_PLATFORM"):
    os.environ["QT_QPA_PLATFORM"] = "xcb"

import capture
from editor import launch_editor


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
    """Hien popup PyQt cho nguoi dung chon 1 cua so trong danh sach (wmctrl).

    Tra ve win_id da chon, hoac None neu:
      - chua cai wmctrl (se in huong dan roi fallback chup cua so active)
      - khong tim thay cua so nao
      - nguoi dung bam Cancel
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

    from PyQt5.QtWidgets import QApplication, QInputDialog
    from PyQt5.QtCore import Qt

    app = QApplication.instance() or QApplication(sys.argv)
    titles = [title for _win_id, title in windows]

    dlg = QInputDialog()
    dlg.setWindowTitle("Chon cua so can chup")
    dlg.setLabelText("Chon 1 cua so trong danh sach:")
    dlg.setComboBoxItems(titles)
    dlg.setOption(QInputDialog.UseListViewForComboBoxItems, True)
    dlg.setWindowModality(Qt.ApplicationModal)
    # Ep dialog len tren cung + nhan focus - tren GNOME Wayland cua so moi
    # mo doi khi khong tu duoc cap focus nen bam vao khong an thua gi.
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
        import tray
        tray.main()
        return

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
