#!/usr/bin/env python3
"""
tray.py - Icon tren system tray (topbar) GNOME cho Mini Screenshot Tool.

Bam icon -> menu xo ra, chon mode chup. Sau khi chup xong se tu mo
EditorWindow (editor.py) giong het khi chay `python3 main.py`.

Cac mode:
    - Chup toan man hinh          -> capture.capture_fullscreen()
    - Chup vung chon              -> capture.capture_region()
    - Chup cua so (submenu)       -> chup "Cua so hien tai" hoac chon dung
                                      1 cua so trong danh sach (wmctrl).
                                      Moi lan chup cua so deu ap dung style
                                      macOS (bo goc + shadow) noi tai.

Phim tat noi tai (kieu macOS, chi khi tray dang chay):
    Ctrl+Shift+3  -> toan man hinh   (≈ Cmd+Shift+3)
    Ctrl+Shift+4  -> vung chon       (≈ Cmd+Shift+4)
    Ctrl+Shift+5  -> cua so active   (≈ Cmd+Shift+5)
    X11: Keybinder3.  Wayland/GNOME: dang ky custom shortcut qua gsettings,
    go bo khi thoat tray.

GIOI HAN QUAN TRONG (da ghi trong capture.py):
    Tren GNOME Wayland, khong co API chinh thuc de liet ke + chon 1 cua so
    cu the tu ben ngoai (gioi han bao mat cua Wayland portal). Danh sach
    cua so o day dung `wmctrl`, chi thay duoc cac cua so chay qua XWayland
    (phan lon app pho bien tren Ubuntu GNOME hien nay van chay qua XWayland
    nen thuong van hoat dong). Cua so Wayland-native thuan tuy se KHONG
    xuat hien trong danh sach nay - do la gioi han cua Wayland, khong phai
    loi cua script.

    Danh sach cua so chi duoc build luc mo submenu / bam "Lam moi danh
    sach" (AppIndicator/libdbusmenu khong tu fire su kien khi hover vao
    submenu nen khong the auto-refresh moi lan mo).

YEU CAU HE THONG THEM (ngoai nhung gi main.py da can):
    sudo apt install python3-gi gir1.2-appindicator3-0.1 wmctrl
    + (khuyen nghi, X11) gir1.2-keybinder-3.0  — phim tat global
    + extension "AppIndicator and KStatusNotifierItem Support" tren GNOME
      (https://extensions.gnome.org/extension/615/appindicator-support/)
      neu khong thi icon se khong hien tren topbar.

GIAO DIEN / DARK THEME:
    Menu duoc style dark bang 1 CssProvider ap dung cho toan Screen (xem
    _apply_dark_theme()). Luu y: neu topbar dang dung extension
    "AppIndicator and KStatusNotifierItem Support", menu duoc GNOME Shell
    ve lai bang widget rieng cua Shell (St), KHONG phai GtkMenu thuan, nen
    CSS o day co the KHONG anh huong toi giao dien do - trong truong hop
    do, dark/light theme cua menu se theo theme he thong (Settings >
    Appearance) chu khong theo app nay dieu khien duoc. Neu chay qua
    Gtk.StatusIcon fallback (khong co appindicator extension) thi CSS
    chac chan co tac dung vi do la GtkMenu thuan cua chinh app.

CHAY:
    python3 tray.py
    # hoac
    python3 main.py --tray
"""

import os
import sys
import subprocess

import gi
gi.require_version("Gtk", "3.0")
try:
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3
    HAS_INDICATOR = True
except (ImportError, ValueError):
    HAS_INDICATOR = False

from gi.repository import Gtk, Gdk

import capture
import hotkeys

APP_ID = "mini-screenshot-tray"
ICON_NAME = "camera-photo-symbolic"

# trang thai dung chung cho lan chup tiep theo (bat/tat qua menu)
_state = {"delay": 0, "busy": False}


# ---------------------------------------------------------------------------
# Dark theme cho menu (chi co tac dung neu menu duoc ve bang GtkMenu thuan -
# xem ghi chu o dau file)
# ---------------------------------------------------------------------------

_MENU_CSS = b"""
menu {
    background-color: #16181d;
    color: #eef0f4;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 6px;
    box-shadow: 0 16px 40px rgba(0, 0, 0, 0.5);
}
menuitem {
    color: #eef0f4;
    border-radius: 9px;
    padding: 9px 14px;
    margin: 1px 0px;
    min-height: 22px;
    font-size: 10.5pt;
    font-weight: 500;
}
menuitem:hover, menuitem:selected {
    background-color: #2b3344;
    color: #ffffff;
}
menuitem:disabled {
    color: #6a7180;
    font-weight: 400;
}
menuitem check, menuitem radio {
    color: #6ea8ff;
    min-height: 14px;
    min-width: 14px;
}
menu separator {
    background-color: rgba(255, 255, 255, 0.08);
    min-height: 1px;
    margin: 6px 8px;
}
arrow {
    color: #8b93a3;
    min-height: 10px;
    min-width: 10px;
}
"""

_HEADER_CSS = b"""
label.mini-screenshot-header-title {
    color: #ffffff;
    font-weight: 700;
    font-size: 11.5pt;
    letter-spacing: 0.2px;
}
label.mini-screenshot-header-subtitle {
    color: #8b93a3;
    font-size: 8.5pt;
}
label.mini-screenshot-accel {
    color: #8b93a3;
    font-size: 9pt;
    font-weight: 400;
}
"""


def _apply_dark_theme():
    for css in (_MENU_CSS, _HEADER_CSS):
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        screen = Gdk.Screen.get_default()
        if screen is not None:
            Gtk.StyleContext.add_provider_for_screen(
                screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )


def _build_header():
    """Hang dau menu khong bam duoc - icon + ten app."""
    item = Gtk.MenuItem()
    item.set_sensitive(False)

    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    box.set_margin_start(6)
    box.set_margin_end(6)
    box.set_margin_top(4)
    box.set_margin_bottom(6)

    icon = Gtk.Image.new_from_icon_name(ICON_NAME, Gtk.IconSize.LARGE_TOOLBAR)
    box.pack_start(icon, False, False, 0)

    text_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
    title = Gtk.Label(label="Mini Screenshot", xalign=0)
    title.get_style_context().add_class("mini-screenshot-header-title")
    subtitle = Gtk.Label(label="Chụp nhanh · chỉnh sửa ngay", xalign=0)
    subtitle.get_style_context().add_class("mini-screenshot-header-subtitle")
    text_box.pack_start(title, False, False, 0)
    text_box.pack_start(subtitle, False, False, 0)
    box.pack_start(text_box, True, True, 0)

    item.add(box)
    return item


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
    if _state["busy"]:
        return
    _state["busy"] = True
    delay = _state["delay"]
    try:
        if delay > 0 and fn is capture.capture_fullscreen:
            path = capture.capture_with_delay(delay, mode="fullscreen")
        elif delay > 0 and fn is capture.capture_region:
            path = capture.capture_with_delay(delay, mode="region")
        elif delay > 0 and fn is capture.capture_window:
            path = capture.capture_with_delay(
                delay, mode="window", mac_style=True
            )
        else:
            path = fn(*args, **kwargs)
    except SystemExit:
        # capture.py goi sys.exit(1) neu thieu tool he thong
        return
    finally:
        _state["busy"] = False
    _open_editor(path)


def do_capture_full(_=None):
    _run_capture(capture.capture_fullscreen)


def do_capture_region(_=None):
    _run_capture(capture.capture_region)


def do_capture_window_current(_=None):
    """Chup cua so dang active, luon ap dung style macOS."""
    _run_capture(capture.capture_window, mac_style=True)


def _on_hotkey(action_id):
    if action_id == "full":
        do_capture_full()
    elif action_id == "region":
        do_capture_region()
    elif action_id == "window":
        do_capture_window_current()


def toggle_delay(item):
    _state["delay"] = 3 if item.get_active() else 0


def quit_app(_=None):
    hotkeys.uninstall()
    Gtk.main_quit()


def _menu_item_with_accel(label, accel_text, callback):
    """Menu item co hint phim tat ben phai (kieu macOS)."""
    item = Gtk.MenuItem()
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=28)
    name = Gtk.Label(label=label, xalign=0)
    name.set_hexpand(True)
    hint = Gtk.Label(label=accel_text, xalign=1)
    hint.get_style_context().add_class("mini-screenshot-accel")
    box.pack_start(name, True, True, 0)
    box.pack_end(hint, False, False, 0)
    item.add(box)
    item.connect("activate", callback)
    return item


# ---------------------------------------------------------------------------
# Chon cua so tu danh sach (best-effort qua wmctrl, xem gioi han o dau file)
# ---------------------------------------------------------------------------

def _list_windows():
    # None = wmctrl chua cai, khac voi [] = khong co cua so nao.
    return capture.list_windows()


def _capture_specific_window(win_id):
    if _state["busy"]:
        return
    _state["busy"] = True
    delay = _state["delay"]
    try:
        path = capture.capture_window_by_id(
            win_id, mac_style=True, delay=delay
        )
    except SystemExit:
        return
    finally:
        _state["busy"] = False
    _open_editor(path)


def _build_window_submenu(parent_item):
    """Submenu 'Chup cua so': cua so hien tai, lam moi, danh sach cua so."""
    submenu = Gtk.Menu()

    current_item = _menu_item_with_accel(
        "Cửa sổ hiện tại",
        hotkeys.display_label("window"),
        do_capture_window_current,
    )
    submenu.append(current_item)

    refresh_item = Gtk.MenuItem(label="Làm mới danh sách")
    refresh_item.connect(
        "activate", lambda w: parent_item.set_submenu(_build_window_submenu(parent_item))
    )
    submenu.append(refresh_item)

    submenu.append(Gtk.SeparatorMenuItem())

    windows = _list_windows()

    if windows is None:
        item = Gtk.MenuItem(label="Chưa cài wmctrl — sudo apt install wmctrl")
        item.set_sensitive(False)
        submenu.append(item)
    elif not windows:
        item = Gtk.MenuItem(label="Không tìm thấy cửa sổ (XWayland)")
        item.set_sensitive(False)
        submenu.append(item)
    else:
        for win_id, title in windows:
            label = title if len(title) <= 48 else title[:45] + "…"
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

    menu.append(_build_header())
    menu.append(Gtk.SeparatorMenuItem())

    menu.append(_menu_item_with_accel(
        "Toàn màn hình", hotkeys.display_label("full"), do_capture_full
    ))
    menu.append(_menu_item_with_accel(
        "Vùng chọn", hotkeys.display_label("region"), do_capture_region
    ))

    window_item = Gtk.MenuItem(label="Cửa sổ")
    window_item.set_submenu(_build_window_submenu(window_item))
    menu.append(window_item)

    menu.append(Gtk.SeparatorMenuItem())

    delay_item = Gtk.CheckMenuItem(label="Đợi 3 giây trước khi chụp")
    delay_item.connect("toggled", toggle_delay)
    menu.append(delay_item)

    menu.append(Gtk.SeparatorMenuItem())

    item_quit = Gtk.MenuItem(label="Thoát")
    item_quit.connect("activate", quit_app)
    menu.append(item_quit)

    menu.show_all()
    return menu


def main():
    # Che do ping tu GNOME custom shortcut (Wayland) — khong mo tray moi.
    if len(sys.argv) >= 3 and sys.argv[1] == "--hotkey":
        ok = hotkeys.ping(sys.argv[2])
        sys.exit(0 if ok else 1)

    missing = capture.check_dependencies()
    if missing:
        print("Thieu cong cu he thong: " + ", ".join(missing))
        print("Cai dat bang: sudo apt install " + " ".join(missing))
        sys.exit(1)

    _apply_dark_theme()
    menu = build_menu()

    backend = hotkeys.install(_on_hotkey, os.path.abspath(__file__))
    if backend:
        print(f"Phim tat: Ctrl+Shift+3/4/5 (backend: {backend})")
    else:
        print(
            "Canh bao: khong dang ky duoc phim tat global. "
            "Cai gir1.2-keybinder-3.0 (X11) hoac dung GNOME."
        )

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

    try:
        Gtk.main()
    finally:
        hotkeys.uninstall()


if __name__ == "__main__":
    main()
