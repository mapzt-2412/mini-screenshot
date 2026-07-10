#!/usr/bin/env python3
"""
hotkeys.py - Phim tat global kieu macOS khi tray dang chay.

Mac:
    Cmd+Shift+3  -> toan man hinh
    Cmd+Shift+4  -> vung chon
    Cmd+Shift+5  -> cua so / screenshot UI
    Ctrl+Cmd+Shift+3/4/5 -> copy clipboard (khong mo editor)

Linux:
    Ctrl+Shift+3  -> toan man hinh
    Ctrl+Shift+4  -> vung chon
    Ctrl+Shift+5  -> cua so dang active
    Ctrl+Alt+Shift+3/4/5 -> copy clipboard (khong mo editor)

Backend (uu tien GNOME vi Keybinder lech keysym Shift+so tren layout US):
    1. GNOME gsettings custom-keybindings — dang ky luc mo tray, go luc thoat
    2. Keybinder3 (X11) — bind ca raw Ctrl+Shift+N lan cooked Ctrl+#/$/%
"""

from __future__ import annotations

import os
import shlex
import socket
import sys

from gi.repository import GLib, Gio

# (gsettings_binding, action_id, label)
HOTKEYS = (
    ("<Control><Shift>3", "full", "Ctrl+Shift+3"),
    ("<Control><Shift>4", "region", "Ctrl+Shift+4"),
    ("<Control><Shift>5", "window", "Ctrl+Shift+5"),
    ("<Control><Alt><Shift>3", "clip-full", "Ctrl+Alt+Shift+3"),
    ("<Control><Alt><Shift>4", "clip-region", "Ctrl+Alt+Shift+4"),
    ("<Control><Alt><Shift>5", "clip-window", "Ctrl+Alt+Shift+5"),
)

# Tren layout US: Shift+3/4/5 = #/$/% — Keybinder cooked can bind them.
_KEYBINDER_ALIASES = {
    "full": ("<Control><Shift>3", "<Control>numbersign"),
    "region": ("<Control><Shift>4", "<Control>dollar"),
    "window": ("<Control><Shift>5", "<Control>percent"),
    "clip-full": ("<Control><Alt><Shift>3", "<Control><Alt>numbersign"),
    "clip-region": ("<Control><Alt><Shift>4", "<Control><Alt>dollar"),
    "clip-window": ("<Control><Alt><Shift>5", "<Control><Alt>percent"),
}

_ACTION_IDS = frozenset(h[1] for h in HOTKEYS)

_GNOME_PATH_PREFIX = (
    "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/"
    "mini-screenshot-"
)
_SOCK_NAME = "mini-screenshot.sock"

_backend = None  # "gnome" | "keybinder" | None
_sock_server = None
_sock_path = None
_bound_keybinder = []
_gnome_paths = []
_actions = {}


def socket_path():
    runtime = os.environ.get("XDG_RUNTIME_DIR") or "/tmp"
    return os.path.join(runtime, _SOCK_NAME)


def _make_cb(on_action, action_id):
    def _cb(_keystr=None, _data=None):
        print(f"[hotkey] {action_id}", flush=True)
        GLib.idle_add(lambda: on_action(action_id) or False)
    return _cb


def _try_keybinder(on_action):
    try:
        import gi
        gi.require_version("Keybinder", "3.0")
        from gi.repository import Keybinder
    except (ImportError, ValueError):
        return False

    Keybinder.init()
    if not Keybinder.supported():
        return False

    bound = []

    # 1) Raw modifiers+digit (layout-independent neu WM gui dung)
    Keybinder.set_use_cooked_accelerators(False)
    for action_id, accels in _KEYBINDER_ALIASES.items():
        raw = accels[0]
        if Keybinder.bind(raw, _make_cb(on_action, action_id), None):
            bound.append(raw)

    # 2) Cooked symbol (# $ %) — dung cho layout US khi bam Ctrl+Shift+3/4/5
    Keybinder.set_use_cooked_accelerators(True)
    for action_id, accels in _KEYBINDER_ALIASES.items():
        for accel in accels[1:]:
            if Keybinder.bind(accel, _make_cb(on_action, action_id), None):
                bound.append(accel)

    if not bound:
        return False

    global _bound_keybinder
    _bound_keybinder = bound
    print(f"[hotkey] keybinder bound: {bound}", flush=True)
    return True


def _unbind_keybinder():
    if not _bound_keybinder:
        return
    try:
        import gi
        gi.require_version("Keybinder", "3.0")
        from gi.repository import Keybinder
        for accel in _bound_keybinder:
            try:
                Keybinder.unbind(accel)
            except Exception:
                pass
    except Exception:
        pass
    _bound_keybinder.clear()


def _start_socket_server(on_action):
    global _sock_server, _sock_path
    path = socket_path()
    try:
        if os.path.exists(path):
            os.unlink(path)
    except OSError:
        pass

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(path)
    os.chmod(path, 0o600)
    server.listen(5)
    server.setblocking(False)
    _sock_server = server
    _sock_path = path

    def _on_io(_fd, _cond):
        try:
            conn, _ = server.accept()
        except BlockingIOError:
            return True
        try:
            data = conn.recv(64).decode("utf-8", errors="ignore").strip()
        finally:
            conn.close()
        if data in _ACTION_IDS:
            print(f"[hotkey] socket -> {data}", flush=True)
            GLib.idle_add(lambda d=data: on_action(d) or False)
        return True

    GLib.io_add_watch(server.fileno(), GLib.IO_IN, _on_io)
    return path


def _stop_socket_server():
    global _sock_server, _sock_path
    if _sock_server is not None:
        try:
            _sock_server.close()
        except OSError:
            pass
        _sock_server = None
    if _sock_path and os.path.exists(_sock_path):
        try:
            os.unlink(_sock_path)
        except OSError:
            pass
    _sock_path = None


def _gnome_available():
    try:
        src = Gio.SettingsSchemaSource.get_default()
        if src is None:
            return False
        return (
            src.lookup("org.gnome.settings-daemon.plugins.media-keys", True) is not None
            and src.lookup(
                "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding",
                True,
            )
            is not None
        )
    except Exception:
        return False


def _try_gnome(on_action, tray_script):
    if not _gnome_available():
        return False

    _start_socket_server(on_action)

    media = Gio.Settings.new("org.gnome.settings-daemon.plugins.media-keys")
    existing = list(media.get_strv("custom-keybindings"))
    paths = []

    cmd_prefix = f"{shlex.quote(sys.executable)} {shlex.quote(tray_script)} --hotkey"
    for binding, action_id, _label in HOTKEYS:
        path = f"{_GNOME_PATH_PREFIX}{action_id}/"
        custom = Gio.Settings.new_with_path(
            "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding",
            path,
        )
        custom.set_string("name", f"Mini Screenshot ({action_id})")
        custom.set_string("command", f"{cmd_prefix} {action_id}")
        custom.set_string("binding", binding)
        if path not in existing:
            existing.append(path)
        paths.append(path)

    media.set_strv("custom-keybindings", existing)
    Gio.Settings.sync()

    global _gnome_paths
    _gnome_paths = paths
    print(f"[hotkey] gnome registered: {paths}", flush=True)
    return True


def _unregister_gnome():
    if not _gnome_paths:
        return
    try:
        media = Gio.Settings.new("org.gnome.settings-daemon.plugins.media-keys")
        existing = [
            p for p in media.get_strv("custom-keybindings") if p not in _gnome_paths
        ]
        media.set_strv("custom-keybindings", existing)
        for path in _gnome_paths:
            custom = Gio.Settings.new_with_path(
                "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding",
                path,
            )
            custom.set_string("binding", "")
            custom.set_string("command", "")
            custom.set_string("name", "")
        Gio.Settings.sync()
    except Exception:
        pass
    _gnome_paths.clear()


def install(on_action, tray_script):
    """Dang ky phim tat. Tra ve ten backend hoac None neu that bai."""
    global _backend, _actions
    _actions = {h[1]: h for h in HOTKEYS}

    # GNOME truoc: xu ly dung Ctrl+Shift+so, khong bi lech #/$/%
    if _try_gnome(on_action, tray_script):
        _backend = "gnome"
        return _backend

    if _try_keybinder(on_action):
        _backend = "keybinder"
        return _backend

    _backend = None
    return None


def uninstall():
    """Go bo phim tat (goi khi thoat tray)."""
    global _backend
    _unbind_keybinder()
    _unregister_gnome()
    _stop_socket_server()
    _backend = None


def ping(action_id):
    """Gui action toi tray dang chay (dung boi --hotkey). Tra ve True neu ok."""
    path = socket_path()
    if not os.path.exists(path):
        print(f"[hotkey] ping fail: no socket {path}", flush=True)
        return False
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(1.0)
        sock.connect(path)
        sock.sendall(action_id.encode("utf-8"))
        sock.close()
        return True
    except OSError as exc:
        print(f"[hotkey] ping fail: {exc}", flush=True)
        return False


def display_label(action_id):
    for _binding, aid, label in HOTKEYS:
        if aid == action_id:
            return label
    return ""
