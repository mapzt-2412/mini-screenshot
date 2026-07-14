#!/usr/bin/env python3
"""System tray for Mini Screenshot (GNOME AppIndicator / StatusIcon).

Capture modes open the same editor as ``main.py``. Window shots use
macOS-style post-processing. Hotkeys (macOS-like) register while the tray
runs and unregister on exit. Every successful capture also gets a copy
recorded to a small on-disk history (see ``history.py``), independent of
the temp file used mid-capture — this backs the "Lich su" submenu and the
"pin" (float on top) action.

Extra deps: ``python3-gi``, ``gir1.2-appindicator3-0.1``, ``wmctrl``;
optional ``gir1.2-keybinder-3.0`` (X11). On GNOME, enable the AppIndicator
extension so the icon appears in the top bar.

Dark CSS applies to native Gtk menus; Shell-redrawn AppIndicator menus
follow the system theme instead.

Run: ``python3 tray.py`` or ``python3 main.py --tray``.
"""

import os
import subprocess
import sys

import gi

gi.require_version("Gtk", "3.0")
try:
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3
    HAS_INDICATOR = True
except (ImportError, ValueError):
    HAS_INDICATOR = False

from gi.repository import Gdk, Gtk

from . import capture, clipboard_util, history, hotkeys

APP_ID = "mini-screenshot-tray"
ICON_NAME = "camera-photo-symbolic"

# Shared state for the next capture (toggled from the menu).
_state = {"delay": 0, "busy": False}


# ---------------------------------------------------------------------------
# Dark theme (native GtkMenu only — see module docstring)
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
    """Non-clickable menu header: icon + app name."""
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
# Open the editor / pin window in a separate process (avoid Qt vs Gtk
# main-loop clash).
# ---------------------------------------------------------------------------

_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_PKG_DIR)
_EDITOR_LAUNCHER = os.path.join(_PKG_DIR, "open_editor.py")
_PIN_LAUNCHER = os.path.join(_PKG_DIR, "pin_window.py")
_TRAY_ENTRY = os.path.join(_ROOT_DIR, "tray.py")


def _spawn_qt_process(script_path, image_path):
    if not image_path or not os.path.exists(image_path):
        return
    env = os.environ.copy()
    # Ensure the package parent is importable when spawned as a script.
    env["PYTHONPATH"] = (
        _ROOT_DIR + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    )
    subprocess.Popen(
        [sys.executable, script_path, image_path],
        cwd=_ROOT_DIR,
        env=env,
    )


def _open_editor(image_path):
    _spawn_qt_process(_EDITOR_LAUNCHER, image_path)


def _open_pin(image_path):
    _spawn_qt_process(_PIN_LAUNCHER, image_path)


# ---------------------------------------------------------------------------
# Capture actions (via capture.py)
# ---------------------------------------------------------------------------

def _run_capture(fn, *args, clipboard_only=False, **kwargs):
    """Run a capture.* helper, applying the current delay if set."""
    if _state["busy"]:
        return
    _state["busy"] = True
    delay = _state["delay"]
    path = None
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

    if not path or not os.path.exists(path):
        return

    # Independent copy for the "Lich su" submenu / pin — do this before any
    # clipboard-only cleanup deletes the original temp file.
    history.add(path)

    if clipboard_only:
        clipboard_util.copy_capture_to_clipboard(path)
    else:
        _open_editor(path)


def do_capture_full(_=None):
    _run_capture(capture.capture_fullscreen)


def do_capture_region(_=None):
    _run_capture(capture.capture_region)


def do_capture_window_current(_=None):
    """Chup cua so dang active, luon ap dung style macOS."""
    _run_capture(capture.capture_window, mac_style=True)


def do_clip_full(_=None):
    _run_capture(capture.capture_fullscreen, clipboard_only=True)


def do_clip_region(_=None):
    _run_capture(capture.capture_region, clipboard_only=True)


def do_clip_window(_=None):
    _run_capture(capture.capture_window, mac_style=True, clipboard_only=True)


def do_pin_last(_=None):
    """Ghim ban chup gan nhat thanh cua so noi always-on-top."""
    recent = history.list_recent()
    if not recent:
        return
    _open_pin(recent[0]["path"])


def _on_hotkey(action_id):
    if action_id == "full":
        do_capture_full()
    elif action_id == "region":
        do_capture_region()
    elif action_id == "window":
        do_capture_window_current()
    elif action_id == "clip-full":
        do_clip_full()
    elif action_id == "clip-region":
        do_clip_region()
    elif action_id == "clip-window":
        do_clip_window()


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
# Window picker (best-effort via wmctrl — see module docstring)
# ---------------------------------------------------------------------------

def _list_windows():
    # None = wmctrl missing; [] = no windows found.
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
    if not path or not os.path.exists(path):
        return
    history.add(path)
    _open_editor(path)


def _build_window_submenu(parent_item):
    """Window submenu: current window, refresh, and wmctrl list."""
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
# Lich su (recent captures)
# ---------------------------------------------------------------------------

def _build_history_submenu(parent_item):
    submenu = Gtk.Menu()

    recent = history.list_recent()

    if not recent:
        item = Gtk.MenuItem(label="Chưa có ảnh nào")
        item.set_sensitive(False)
        submenu.append(item)
    else:
        for entry in recent:
            row = Gtk.Menu()
            row_item = Gtk.MenuItem(label=history.label_for(entry))
            row_item.set_submenu(row)

            open_item = Gtk.MenuItem(label="Mở trong Editor")
            open_item.connect("activate", lambda w, p=entry["path"]: _open_editor(p))
            row.append(open_item)

            pin_item = Gtk.MenuItem(label="Ghim (luôn nổi)")
            pin_item.connect("activate", lambda w, p=entry["path"]: _open_pin(p))
            row.append(pin_item)

            copy_item = Gtk.MenuItem(label="Copy vào clipboard")
            copy_item.connect(
                "activate",
                lambda w, p=entry["path"]: clipboard_util.copy_capture_to_clipboard(
                    p, cleanup=False
                ),
            )
            row.append(copy_item)

            row.show_all()
            submenu.append(row_item)

        submenu.append(Gtk.SeparatorMenuItem())
        clear_item = Gtk.MenuItem(label="Xóa lịch sử")
        clear_item.connect("activate", lambda w: (
            history.clear(),
            parent_item.set_submenu(_build_history_submenu(parent_item)),
        ))
        submenu.append(clear_item)

    refresh_item = Gtk.MenuItem(label="Làm mới")
    refresh_item.connect(
        "activate", lambda w: parent_item.set_submenu(_build_history_submenu(parent_item))
    )
    submenu.append(refresh_item)

    submenu.show_all()
    return submenu


# ---------------------------------------------------------------------------
# Main menu
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

    history_item = Gtk.MenuItem(label="Lịch sử")
    history_item.set_submenu(_build_history_submenu(history_item))
    menu.append(history_item)

    menu.append(_menu_item_with_accel("Ghim ảnh gần nhất", "", do_pin_last))

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

    # Root tray.py is the stable GNOME shortcut target (supports --hotkey).
    tray_script = _TRAY_ENTRY if os.path.isfile(_TRAY_ENTRY) else os.path.abspath(__file__)
    backend = hotkeys.install(_on_hotkey, tray_script)
    if backend:
        print(
            "Phim tat: Ctrl+Shift+3/4/5 (editor), "
            f"Ctrl+Alt+Shift+3/4/5 (clipboard) (backend: {backend})"
        )
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
