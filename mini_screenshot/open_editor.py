#!/usr/bin/env python3
"""Open the editor in a separate process (spawned by the tray).

Avoids fighting the tray's Gtk.main() event loop.
"""

import os
import sys

# Allow ``python3 path/to/open_editor.py`` when PYTHONPATH is not set.
_PKG_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PKG_PARENT not in sys.path:
    sys.path.insert(0, _PKG_PARENT)

from mini_screenshot.qt_env import ensure_qt_platform

ensure_qt_platform()

from mini_screenshot.editor import launch_editor


def main(argv=None):
    argv = argv if argv is not None else sys.argv
    if len(argv) < 2:
        print("Usage: open_editor.py <image_path>")
        return 1

    image_path = argv[1]
    app, win = launch_editor(image_path)
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
