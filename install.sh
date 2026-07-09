#!/usr/bin/env bash
# Cai dat dependencies cho Mini Screenshot Tool tren Ubuntu 22.04 (Wayland)
set -e

echo ">> Cai dat cong cu he thong..."
echo "   (gnome-screenshot cho GNOME Wayland; grim/slurp cho wlroots neu can)"
sudo apt update
sudo apt install -y gnome-screenshot wl-clipboard python3-pip tesseract-ocr tesseract-ocr-vie
# grim + slurp chi can neu ban dung Sway/Hyprland (wlroots-based), khong bat
# buoc tren GNOME nhung cai them cung khong hai gi:
sudo apt install -y grim slurp || true

echo ">> Cai dat thu vien Python..."
pip3 install --break-system-packages PyQt5 Pillow pytesseract

echo ""
echo "Xong! Chay thu bang:"
echo "  python3 main.py"
echo ""
echo "Goi y: xem README.md de gan phim tat (vi du Ctrl+Shift+S)."
