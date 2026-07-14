"""Recent-capture history.

Keeps a small on-disk copy of the last N captures (independent of the
temp files used mid-capture, which may get deleted right after a
clipboard-only shot) plus a tiny JSON index. Used by the tray's
"Lich su" submenu and by the "pin" feature.
"""

import json
import os
import shutil
import time

MAX_ITEMS = 12


def _dir():
    base = os.environ.get("XDG_STATE_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "state"
    )
    d = os.path.join(base, "mini-screenshot", "history")
    os.makedirs(d, exist_ok=True)
    return d


def _index_path():
    return os.path.join(_dir(), "index.json")


def _load_index():
    path = _index_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def _save_index(items):
    try:
        with open(_index_path(), "w", encoding="utf-8") as f:
            json.dump(items, f)
    except OSError:
        pass


def _prune(kept_items):
    """Delete on-disk files that fell off the index (best-effort)."""
    kept = {it["path"] for it in kept_items}
    d = _dir()
    try:
        names = os.listdir(d)
    except OSError:
        return
    for name in names:
        if name == "index.json":
            continue
        full = os.path.join(d, name)
        if full not in kept:
            try:
                os.remove(full)
            except OSError:
                pass


def add(source_path, max_items=MAX_ITEMS):
    """Copy ``source_path`` into the history dir and record it.

    Returns the stored path, or None if the source was missing / copy
    failed. Safe to call even if ``source_path`` will be deleted right
    after (e.g. clipboard-only capture) — this makes an independent copy.
    """
    if not source_path or not os.path.exists(source_path):
        return None

    items = _load_index()
    ts = int(time.time() * 1000)
    dest = os.path.join(_dir(), f"shot_{ts}.png")
    try:
        shutil.copy2(source_path, dest)
    except OSError:
        return None

    items.insert(0, {"path": dest, "ts": ts})
    items = items[:max_items]
    _save_index(items)
    _prune(items)
    return dest


def list_recent():
    """Return recent items (most recent first), skipping any that vanished."""
    items = [it for it in _load_index() if os.path.exists(it["path"])]
    if len(items) != len(_load_index()):
        _save_index(items)
    return items


def clear():
    for it in _load_index():
        try:
            os.remove(it["path"])
        except OSError:
            pass
    _save_index([])


def label_for(item):
    """Short human label, e.g. '14:32:05'."""
    return time.strftime("%H:%M:%S", time.localtime(item["ts"] / 1000))
