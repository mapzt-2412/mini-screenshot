"""Wayland screenshot backends with desktop auto-detection.

- GNOME (Mutter): ``gnome-screenshot`` — grim/slurp need wlr-screencopy,
  which Mutter does not expose.
- wlroots (Sway/Hyprland): ``grim`` + ``slurp``.

Window picking on GNOME uses ``wmctrl`` (focus then shoot). Pure
Wayland-native windows may be missing from that list. On wlroots,
``slurp -w`` lets you click a window directly.

``mac_style=True`` post-processes the shot with Pillow (rounded corners,
drop shadow, transparent PNG).
"""

import os
import subprocess
import sys
import tempfile
import time

from .mac_window_style import apply_mac_style


def _check_tool(name):
    try:
        subprocess.run(["which", name], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def _is_gnome():
    desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    session = os.environ.get("DESKTOP_SESSION", "").lower()
    return "gnome" in desktop or "gnome" in session


def check_dependencies():
    """Kiem tra tool can thiet theo desktop environment hien tai."""
    missing = []
    if _is_gnome():
        if not _check_tool("gnome-screenshot"):
            missing.append("gnome-screenshot")
    else:
        for tool in ("grim", "slurp"):
            if not _check_tool(tool):
                missing.append(tool)
    return missing


def _tmp_path():
    ts = int(time.time() * 1000)
    return os.path.join(tempfile.gettempdir(), f"screenshot_capture_{ts}.png")


# ---------------------------------------------------------------------------
# Backend: GNOME (gnome-screenshot, dung D-Bus org.gnome.Shell.Screenshot)
# ---------------------------------------------------------------------------

def _gnome_capture(extra_args, delay=0):
    out_path = _tmp_path()
    cmd = ["gnome-screenshot"]
    if delay > 0:
        cmd.append(f"--delay={delay}")
    cmd += extra_args + ["-f", out_path]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        print("Loi: khong tim thay 'gnome-screenshot'. "
              "Cai dat: sudo apt install gnome-screenshot")
        sys.exit(1)

    if result.returncode != 0:
        return None  # nguoi dung nhan Esc / huy chon vung, hoac loi that su

    if not os.path.exists(out_path):
        return None
    return out_path


# ---------------------------------------------------------------------------
# Backend: wlroots (grim + slurp) - danh cho Sway, Hyprland, v.v.
# ---------------------------------------------------------------------------

def _wlroots_capture_region():
    try:
        result = subprocess.run(["slurp"], capture_output=True, text=True)
    except FileNotFoundError:
        print("Loi: khong tim thay 'slurp'. Cai dat: sudo apt install slurp")
        sys.exit(1)

    if result.returncode != 0 or not result.stdout.strip():
        return None

    geometry = result.stdout.strip()
    out_path = _tmp_path()
    try:
        subprocess.run(["grim", "-g", geometry, out_path], check=True)
    except FileNotFoundError:
        print("Loi: khong tim thay 'grim'. Cai dat: sudo apt install grim")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"grim that bai: {e}")
        return None
    return out_path


def _wlroots_capture_fullscreen():
    out_path = _tmp_path()
    try:
        subprocess.run(["grim", out_path], check=True)
    except FileNotFoundError:
        print("Loi: khong tim thay 'grim'. Cai dat: sudo apt install grim")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"grim that bai: {e}")
        return None
    return out_path


def _wlroots_capture_window():
    try:
        result = subprocess.run(["slurp", "-w"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            geometry = result.stdout.strip()
            out_path = _tmp_path()
            subprocess.run(["grim", "-g", geometry, out_path], check=True)
            return out_path
        elif result.returncode != 0 and "cancelled" in (result.stderr or "").lower():
            return None
    except FileNotFoundError:
        pass
    return _wlroots_capture_region()


# ---------------------------------------------------------------------------
# Chon cua so tu danh sach (dung chung cho GNOME, qua wmctrl)
# ---------------------------------------------------------------------------

def list_windows():
    """Liet ke cac cua so dang mo bang wmctrl.

    Tra ve:
        - list[(win_id, title)]  neu thanh cong (co the rong neu khong
          tim thay cua so nao qua XWayland)
        - None neu chua cai wmctrl (khac voi list rong)

    Loc bo cac "cua so" rac khong phai app that su - vi du GNOME Shell doi
    khi tra ve title kieu "@!1920,0;BDHF" cho cac helper window an
    (khong co tieu de that), khong co ich gi cho nguoi dung chon.
    """
    if not _check_tool("wmctrl"):
        return None
    try:
        out = subprocess.run(
            ["wmctrl", "-lx"], capture_output=True, text=True, check=True
        ).stdout
    except subprocess.CalledProcessError:
        return None

    windows = []
    for line in out.splitlines():
        parts = line.split(None, 4)
        if len(parts) < 5:
            continue
        win_id, _desktop, _wm_class, _host, title = parts
        title = title.strip()
        if not title or title.startswith("@!"):
            continue
        windows.append((win_id, title))
    return windows


def focus_window(win_id):
    """Focus 1 cua so cu the qua wmctrl, roi doi 1 chut de GNOME chuyen
    focus xong truoc khi chup (tranh chup nham cua so cu)."""
    if _check_tool("wmctrl"):
        subprocess.run(["wmctrl", "-ia", win_id], capture_output=True, text=True)
        time.sleep(0.8)


def capture_window_by_id(win_id, mac_style=False, delay=0):
    """Focus dung cua so co win_id (lay tu list_windows()) roi chup no.

    Tren GNOME: focus xong goi gnome-screenshot -w (chup cua so dang active,
    luc nay chinh la cua so vua duoc focus).
    Tren wlroots: khong can buoc nay (slurp -w da cho click chon truc tiep),
    nhung van ho tro de code goi duoc dong nhat - se chup toan man hinh
    cua so da focus bang grim (khong chinh xac bang slurp -w truc tiep).
    """
    focus_window(win_id)

    if _is_gnome():
        raw_path = _gnome_capture(["-w"], delay=delay)
    else:
        time.sleep(max(0, delay))
        raw_path = _wlroots_capture_window()

    if not raw_path:
        return None
    if mac_style:
        return apply_mac_style(raw_path)
    return raw_path


# ---------------------------------------------------------------------------
# API public - tu dong chon backend phu hop
# ---------------------------------------------------------------------------

def capture_region():
    """Chup 1 vung do nguoi dung chon."""
    if _is_gnome():
        return _gnome_capture(["-a"])
    return _wlroots_capture_region()


def capture_fullscreen():
    """Chup toan bo man hinh."""
    if _is_gnome():
        return _gnome_capture([])
    return _wlroots_capture_fullscreen()


def capture_window(mac_style=False):
    """Chup 1 cua so. Tren GNOME se chup cua so dang active (khong click-chon
    duoc do gioi han cua Wayland portal) - dung capture_window_by_id() /
    list_windows() neu muon cho nguoi dung chon dung cua so.

    mac_style=True: sau khi chup, ap dung bo goc + drop shadow + nen trong
    suot kieu macOS (xem mac_window_style.py). Tra ve duong dan anh moi.
    """
    if _is_gnome():
        raw_path = _gnome_capture(["-w"])
    else:
        raw_path = _wlroots_capture_window()

    if not raw_path:
        return None
    if mac_style:
        return apply_mac_style(raw_path)
    return raw_path


def capture_with_delay(seconds, mode="region", mac_style=False):
    """Doi N giay roi moi chup (mode: region/fullscreen/window).

    mac_style chi co tac dung khi mode="window".
    """
    if _is_gnome():
        extra = {"region": ["-a"], "fullscreen": [], "window": ["-w"]}[mode]
        raw_path = _gnome_capture(extra, delay=seconds)
        if raw_path and mode == "window" and mac_style:
            return apply_mac_style(raw_path)
        return raw_path

    time.sleep(max(0, seconds))
    if mode == "fullscreen":
        return _wlroots_capture_fullscreen()
    if mode == "window":
        raw_path = _wlroots_capture_window()
        if raw_path and mac_style:
            return apply_mac_style(raw_path)
        return raw_path
    return _wlroots_capture_region()
