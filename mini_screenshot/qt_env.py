"""Qt platform helpers (must run before any PyQt5 import)."""

import os


def ensure_qt_platform():
    """Force Qt through XWayland on GNOME Wayland so dialogs get focus.

    Respects an existing ``QT_QPA_PLATFORM`` if the user already set one.
    """
    if os.environ.get("WAYLAND_DISPLAY") and not os.environ.get("QT_QPA_PLATFORM"):
        os.environ["QT_QPA_PLATFORM"] = "xcb"
