#!/usr/bin/env python3
"""
main.py - Mini Screenshot Tool cho Ubuntu (Wayland)

Cach dung:
    python3 main.py                 # chup vung chon (mac dinh)
    python3 main.py --full          # chup toan man hinh
    python3 main.py --window        # chup 1 cua so
    python3 main.py --window --mac-style   # chup 1 cua so, bo goc + shadow + nen trong suot kieu macOS
    python3 main.py --delay 3       # doi 3 giay roi chup vung chon
    python3 main.py --delay 3 --full

Sau khi chup, cua so Edit se tu mo de ban ve/annotate.
"""

import argparse
import sys
import os

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
    return parser.parse_args()


def main():
    args = parse_args()

    missing = capture.check_dependencies()
    if missing:
        print("Thieu cong cu he thong: " + ", ".join(missing))
        print("Cai dat bang: sudo apt install " + " ".join(missing))
        sys.exit(1)

    mode = "fullscreen" if args.full else ("window" if args.window else "region")

    if args.mac_style and mode != "window":
        print("Luu y: --mac-style chi co tac dung voi --window, se bi bo qua.")

    if args.delay > 0:
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
