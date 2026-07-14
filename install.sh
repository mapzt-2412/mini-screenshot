#!/usr/bin/env bash
# Cai dat dependencies cho Mini Screenshot Tool tren Ubuntu 22.04 (Wayland)
set -e

echo ">> Cai dat cong cu he thong..."
echo "   (gnome-screenshot cho GNOME Wayland; grim/slurp cho wlroots neu can;"
echo "    wmctrl de cho phep popup chon cua so khi chup --window)"
sudo apt update
sudo apt install -y gnome-screenshot wl-clipboard python3-pip tesseract-ocr tesseract-ocr-vie wmctrl
# grim + slurp chi can neu ban dung Sway/Hyprland (wlroots-based), khong bat
# buoc tren GNOME nhung cai them cung khong hai gi:
sudo apt install -y grim slurp || true

echo ">> Cai dat thu vien Python..."
pip3 install --break-system-packages PyQt5 Pillow pytesseract

echo ""
echo "Done! Try:"
echo "  python3 main.py"
echo "  python3 -m mini_screenshot --tray"
echo ""
echo "See README.md for hotkeys (e.g. Ctrl+Shift+S)."
