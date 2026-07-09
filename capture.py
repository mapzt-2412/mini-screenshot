"""
capture.py

Chup man hinh tren Wayland.

QUAN TRONG:
- grim/slurp CHI hoat dong tren cac compositor dong wlroots (Sway, Hyprland...).
  GNOME Shell (Mutter) KHONG ho tro protocol wlr-screencopy ma grim/slurp can,
  nen tren GNOME Wayland, slurp se khong hien gi ca va tra ve rong.
- Vi vay module nay tu dong nhan dien desktop environment:
    + Neu la GNOME       -> dung gnome-screenshot (co san tren Ubuntu)
    + Neu la wlroots-based -> dung grim + slurp

- capture_window() ho tro them tham so mac_style=True: sau khi chup xong se
  goi mac_window_style.apply_mac_style() de bo goc + ve drop shadow + xuat
  PNG nen trong suot, gia lap style cua so tren macOS. Day la hau xu ly
  (post-processing) bang Pillow, vi gnome-screenshot/grim+slurp chi tra ve
  anh raster hinh chu nhat thuan tuy, khong co shadow/alpha nhu macOS
  WindowServer render san.
"""

import subprocess
import tempfile
import os
import sys
import time

from mac_window_style import apply_mac_style


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
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        print("Loi: khong tim thay 'gnome-screenshot'. "
              "Cai dat: sudo apt install gnome-screenshot")
        sys.exit(1)
    except subprocess.CalledProcessError:
        return None  # nguoi dung nhan Esc / huy chon vung

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
    duoc do gioi han cua Wayland portal).

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
