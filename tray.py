#!/usr/bin/env python3
"""Thin tray entry — delegates to ``mini_screenshot.tray``.

Also used as the GNOME custom-shortcut target for ``--hotkey``.
"""

from mini_screenshot.tray import main

if __name__ == "__main__":
    raise SystemExit(main())
