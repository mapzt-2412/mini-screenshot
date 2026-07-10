#!/usr/bin/env python3
"""
tray.py - Icon tren system tray (topbar) GNOME cho Mini Screenshot Tool.

Bam icon -> menu xo ra, chon mode chup. Sau khi chup xong se tu mo
EditorWindow (editor.py) giong het khi chay `python3 main.py`.

Cac mode:
    - Chup toan man hinh          -> capture.capture_fullscreen()
    - Chup vung chon              -> capture.capture_region()
    - Chup cua so hien tai        -> capture.capture_window()
    - Chup cua so (style macOS)   -> capture.capture_window(mac_style=True)
    - Chon cua so tu danh sach    -> liet ke cac cua so dang mo (wmctrl),
                                      focus cua so duoc chon, roi chup no

GIOI HAN QUAN TRONG (da ghi trong capture.py):
    Tren GNOME Wayland, khong co API chinh thuc de liet ke + chon 1 cua so
    cu the tu ben ngoai (gioi han bao mat cua Wayland portal). Menu "Chon
    cua so tu danh sach" o day dung `wmctrl`, chi thay duoc cac cua so
    chay qua XWayland (phan lon app pho bien tren Ubuntu GNOME hien nay
    van chay qua XWayland nen thuong van hoat dong). Cua so Wayland-native
    thuan tuy se KHONG xuat hien trong danh sach nay - do la gioi han cua
    Wayland, khong phai loi cua script.

YEU CAU HE THONG THEM (ngoai nhung gi main.py da can):
    sudo apt install python3-gi gir1.2-appindicator3-0.1 wmctrl
    + extension "AppIndicator and KStatusNotifierItem Support" tren GNOME
      (https://extensions.gnome.org/extension/615/appindicator-support/)
      neu khong thi icon se khong hien tren topbar.

CHAY:
    python3 tray.py
    # hoac
    python3 main.py --tray
"""

import os
import sys
import shutil
import subprocess
import time

import gi
gi.require_version("Gtk", "3.0")
try:
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3
    HAS_INDICATOR = True
except (ImportError, ValueError):
    HAS_INDICATOR = False

from gi.repository import Gtk, GLib

import capture

APP_ID = "mini-screenshot-tray"
ICON_NAME = "camera-photo-symbolic"

# so giay delay ap dung cho lan chup tiep theo (bat/tat qua menu checkbox)
_state = {"delay": 0}


# ---------------------------------------------------------------------------
# Mo Editor trong 1 tien trinh rieng, tranh chay chung event loop Qt voi
# event loop GTK cua tray (2 main loop khac nhau trong cung 1 process de
# xung dot / deadlock).
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
_EDITOR_LAUNCHER = os.path.join(_HERE, "_open_editor.py")


def _open_editor(image_path):
    if not image_path or not os.path.exists(image_path):
        return
    subprocess.Popen([sys.executable, _EDITOR_LAUNCHER, image_path], cwd=_HERE)


# ---------------------------------------------------------------------------
# Cac hanh dong chup - deu chay qua capture.py that su cua repo
# ---------------------------------------------------------------------------

def _run_capture(fn, *args, **kwargs):
    """Chay 1 ham capture.* , co ap dung delay dang bat (neu co)."""
    delay = _state["delay"]
    try:
        if delay > 0 and fn is capture.capture_fullscreen:
            path = capture.capture_with_delay(delay, mode="fullscreen")
        elif delay > 0 and fn is capture.capture_region:
            path = capture.capture_with_delay(delay, mode="region")
        elif delay > 0 and fn is capture.capture_window:
            path = capture.capture_with_delay(
                delay, mode="window", mac_style=kwargs.get("mac_style", False)
            )
        else:
            path = fn(*args, **kwargs)
    except SystemExit:
        # capture.py goi sys.exit(1) neu thieu tool he thong
        return
    _open_editor(path)


def do_capture_full(_=None):
    _run_capture(capture.capture_fullscreen)


def do_capture_region(_=None):
    _run_capture(capture.capture_region)


def do_capture_window(_=None):
    _run_capture(capture.capture_window)


def do_capture_window_mac(_=None):
    _run_capture(capture.capture_window, mac_style=True)


def toggle_delay(item):
    _state["delay"] = 3 if item.get_active() else 0


def open_current_dir(_=None):
    subprocess.Popen(["xdg-open", "/tmp"])


def quit_app(_=None):
    Gtk.main_quit()


# ---------------------------------------------------------------------------
# Chon cua so tu danh sach (best-effort qua wmctrl, xem gioi han o dau file)
# ---------------------------------------------------------------------------

def _list_windows():
    if not shutil.which("wmctrl"):
        return None  # None = wmctrl chua cai, khac voi [] = khong co cua so nao
    try:
        out = subprocess.run(
            ["wmctrl", "-lx"], capture_output=True, text=True, check=True
        ).stdout
    except Exception:
        return None

    windows = []
    for line in out.splitlines():
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        win_id, _desktop, _wm_class, _host, title = parts
        title = title.strip()
        if title:
            windows.append((win_id, title))
    return windows


def _capture_specific_window(win_id):
    if shutil.which("wmctrl"):
        subprocess.run(["wmctrl", "-ia", win_id])
        time.sleep(0.4)  # doi GNOME chuyen focus xong roi moi chup
    _run_capture(capture.capture_window)


def _build_window_submenu():
    submenu = Gtk.Menu()
    windows = _list_windows()

    if windows is None:
        item = Gtk.MenuItem(label="Chua cai wmctrl (sudo apt install wmctrl)")
        item.set_sensitive(False)
        submenu.append(item)
    elif not windows:
        item = Gtk.MenuItem(label="Khong tim thay cua so nao (XWayland)")
        item.set_sensitive(False)
        submenu.append(item)
    else:
        for win_id, title in windows:
            label = title if len(title) <= 55 else title[:52] + "..."
            item = Gtk.MenuItem(label=label)
            item.connect("activate", lambda w, wid=win_id: _capture_specific_window(wid))
            submenu.append(item)

    submenu.show_all()
    return submenu


# ---------------------------------------------------------------------------
# Menu chinh
# ---------------------------------------------------------------------------

def build_menu():
    menu = Gtk.Menu()

    item_full = Gtk.MenuItem(label="📷 Chụp toàn màn hình")
    item_full.connect("activate", do_capture_full)
    menu.append(item_full)

    item_region = Gtk.MenuItem(label="✂️  Chụp vùng chọn")
    item_region.connect("activate", do_capture_region)
    menu.append(item_region)

    item_window = Gtk.MenuItem(label="🪟 Chụp cửa sổ hiện tại")
    item_window.connect("activate", do_capture_window)
    menu.append(item_window)

    item_window_mac = Gtk.MenuItem(label="🪟 Chụp cửa sổ (style macOS)")
    item_window_mac.connect("activate", do_capture_window_mac)
    menu.append(item_window_mac)

    # submenu chon cua so, build lai moi lan mo de danh sach luon moi
    window_list_item = Gtk.MenuItem(label="📋 Chọn cửa sổ từ danh sách")
    window_list_item.connect(
        "activate", lambda w: window_list_item.set_submenu(_build_window_submenu())
    )
    window_list_item.set_submenu(_build_window_submenu())
    menu.append(window_list_item)

    menu.append(Gtk.SeparatorMenuItem())

    delay_item = Gtk.CheckMenuItem(label="⏱ Đợi 3 giây trước khi chụp")
    delay_item.connect("toggled", toggle_delay)
    menu.append(delay_item)

    menu.append(Gtk.SeparatorMenuItem())

    item_quit = Gtk.MenuItem(label="Thoát")
    item_quit.connect("activate", quit_app)
    menu.append(item_quit)

    menu.show_all()
    return menu


def main():
    missing = capture.check_dependencies()
    if missing:
        print("Thieu cong cu he thong: " + ", ".join(missing))
        print("Cai dat bang: sudo apt install " + " ".join(missing))
        sys.exit(1)

    menu = build_menu()

    if HAS_INDICATOR:
        indicator = AppIndicator3.Indicator.new(
            APP_ID, ICON_NAME, AppIndicator3.IndicatorCategory.APPLICATION_STATUS
        )
        indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        indicator.set_menu(menu)
    else:
        status_icon = Gtk.StatusIcon.new_from_icon_name(ICON_NAME)
        status_icon.set_tooltip_text("Mini Screenshot")
        status_icon.connect(
            "popup-menu",
            lambda icon, button, t: menu.popup(None, None, None, icon, button, t),
        )
        status_icon.connect(
            "activate",
            lambda icon: menu.popup(None, None, None, icon, 0, Gtk.get_current_event_time()),
        )

    Gtk.main()


if __name__ == "__main__":
    main()
