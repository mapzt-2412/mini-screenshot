# Clipboard-only capture (hotkeys)

**Date:** 2026-07-10  
**Status:** Approved  
**Scope:** Capture to clipboard without opening the editor, triggered by dedicated hotkeys when the tray is running.

## Goal

Keep the existing capture → Editor flow, and add a parallel **clipboard-only** mode: capture → copy image to clipboard → delete temp file → desktop notification → done (no Editor).

## Non-goals

- No new CLI flag (`--clipboard`)
- No new tray menu items for clipboard mode
- No change to Editor Save / Copy behavior
- No permanent file under Pictures/Screenshots (capture already uses temp files)

## Hotkeys

When `tray.py` / `main.py --tray` is running:

| Binding | Action ID | Behavior |
|---------|-----------|----------|
| `Ctrl+Shift+3` | `full` | Fullscreen → open Editor (unchanged) |
| `Ctrl+Shift+4` | `region` | Region → open Editor (unchanged) |
| `Ctrl+Shift+5` | `window` | Active window → open Editor (unchanged) |
| `Ctrl+Alt+Shift+3` | `clip-full` | Fullscreen → clipboard only |
| `Ctrl+Alt+Shift+4` | `clip-region` | Region → clipboard only |
| `Ctrl+Alt+Shift+5` | `clip-window` | Active window → clipboard only |

Clipboard hotkeys follow the same registration path as existing ones (GNOME `custom-keybindings` first, Keybinder fallback on X11).

## Flow

```
hotkey clip-* 
  → same capture path as full/region/window (respect delay toggle)
  → temp PNG path
  → copy PNG to clipboard (wl-copy preferred; Qt clipboard fallback)
  → delete temp PNG
  → notify-send "Mini Screenshot" "Đã copy vào clipboard"
  → do NOT open Editor
```

If capture is cancelled (no region / missing tools), do nothing (no notification).

## Components

### `hotkeys.py`

- Extend `HOTKEYS` with the three `clip-*` bindings and labels.
- GNOME registration already loops `HOTKEYS`; new entries register automatically.
- Keybinder aliases: bind cooked forms if needed for Alt+Shift+digit layouts (same pattern as existing `#/$/%` aliases where applicable).

### `tray.py`

- Extend `_on_hotkey` to handle `clip-full`, `clip-region`, `clip-window`.
- Add a clipboard capture helper that reuses `_run_capture` capture logic but, instead of `_open_editor`, calls a shared copy + notify + cleanup path.
- Window clipboard mode uses the same “current window + mac-style” behavior as `do_capture_window_current`.

### Clipboard helper (shared)

Extract or mirror Editor’s Wayland-safe copy:

1. Prefer `wl-copy --type image/png` with the PNG file as stdin.
2. Fallback: Qt `QClipboard.setImage` if a Qt app instance is available / cheap to create; otherwise skip if `wl-copy` succeeded.
3. Always attempt to remove the temp capture file after a successful copy.

Prefer a small shared function (e.g. in a tiny util or next to capture) so Editor and clipboard-only mode do not drift. Minimal change is acceptable: duplicate the `wl-copy` block in tray if extracting would touch Editor more than needed — prefer extract if both call sites stay one-liners.

### Notification

- `notify-send "Mini Screenshot" "Đã copy vào clipboard"` (libnotify / `notify-send`).
- If `notify-send` is missing: print the same message to stdout; do not fail the capture.

## Error handling

| Case | Behavior |
|------|----------|
| User cancels region select | Silent exit; no notify |
| Missing capture deps | Existing capture error path; no notify |
| `wl-copy` missing / fails | Try Qt clipboard if feasible; if both fail, notify failure or print error |
| Temp delete fails | Ignore (best-effort cleanup) |

## Testing

1. Tray running: `Ctrl+Alt+Shift+4` → select region → paste into GIMP/LibreOffice/browser → image appears; Editor does not open; notification shows; no leftover `screenshot_capture_*.png` in `/tmp` for that shot.
2. `Ctrl+Shift+4` still opens Editor.
3. Delay toggle still applies to clipboard hotkeys.
4. Quit tray → clipboard hotkeys unregister (same as existing).

## Out of scope / later

- Tray menu entries or CLI `--clipboard`
- Sound / shutter feedback
- Thumbnail in the notification
