# Mini Screenshot

A lightweight screenshot + annotation tool for **Ubuntu / GNOME Wayland**, written in Python and PyQt5.

It auto-detects your desktop and picks the right capture backend:

| Desktop | Backend |
|---------|---------|
| **GNOME Shell** (default on Ubuntu) | `gnome-screenshot` via D-Bus (`org.gnome.Shell.Screenshot`) |
| **Sway / Hyprland / wlroots** | `grim` + `slurp` |

> **Why two backends?** `grim`/`slurp` need the `wlr-screencopy` protocol. GNOME’s Mutter does **not** expose it — on GNOME, `slurp` shows no overlay and looks like a cancelled selection.

---

## Features

- **Region**, **fullscreen**, or **window** capture
  - GNOME: pick a window from a list (`wmctrl`), then focus + shoot
  - wlroots: click the window directly (`slurp -w`)
- Optional **countdown delay** before capture
- Dark-themed **editor** that opens automatically after every shot:
  - Pen, line, arrow, rectangle, ellipse
  - Highlighter, text, numbered steps
  - **Spotlight** — dim everything except the selected area
  - **Ruler** — measure pixel distance between two points
  - Blur / pixelate, crop, color picker (hex → clipboard)
  - **Auto-redact** — OCR-based one-click detection & blur of emails, phone
    numbers, card numbers, and CCCD/CMND-style IDs (regex-based; always
    review the result before sharing — it's a time-saver, not a guarantee)
  - Quick color presets + full color picker
  - OCR (full image or selection) via Tesseract
  - Copy image, **copy file path**, or **copy as Markdown** (`![](path)`)
  - Undo / Redo (`Ctrl+Z` / `Ctrl+Shift+Z`)
- Save (`Ctrl+S`) or copy to clipboard (`Ctrl+C`)
- System tray with macOS-style hotkeys; `Ctrl+Alt+Shift+3/4/5` copy straight to clipboard (no editor)
- **Lịch sử (History)** — the last 12 captures are kept in a tray submenu; reopen any of them in the Editor, copy again, or pin them
- **Pin** — float any capture as a small always-on-top window (drag to move, scroll to adjust opacity, `Ctrl +`/`Ctrl -` to resize, `Esc`/double-click to close)

---

## Install

```bash
chmod +x install.sh
./install.sh
```

Or manually (GNOME / Ubuntu):

```bash
sudo apt install gnome-screenshot wl-clipboard tesseract-ocr tesseract-ocr-vie wmctrl
pip3 install --break-system-packages PyQt5 Pillow pytesseract
```

> `wmctrl` is optional. Without it, `--window` falls back to the **currently focused** window (no picker popup).

For Sway / Hyprland:

```bash
sudo apt install grim slurp
```

---

## Usage

```bash
python3 main.py                      # region (default)
python3 main.py --full               # fullscreen
python3 main.py --window             # window picker (GNOME) / click (wlroots)
python3 main.py --window --mac-style # rounded corners + shadow + transparent PNG
python3 main.py --delay 3            # wait 3s, then region
python3 main.py --delay 5 --full
python3 main.py --tray               # system tray
python3 -m mini_screenshot --tray    # same, via package module
```

- **Region:** drag to select, `Esc` to cancel
- **Window (GNOME):** pick from the list → OK; Cancel / no `wmctrl` → active window
- After any capture, the **Edit** window opens for annotate / crop / blur / OCR

### Editor tool cheatsheet

| Tool | What it does |
|------|---------------|
| Spotlight | Drag a box — everything outside it gets dimmed, drawing the eye to what's inside |
| Ruler | Drag between two points — draws tick marks + a `NNNpx` label |
| Auto-redact (toolbar button, top-right) | Runs OCR, regex-matches likely emails/phones/card numbers/IDs, pixelates each match |
| Copy `⋯` menu (next to Copy) | "Copy đường dẫn file" / "Copy dạng Markdown" — saves the current edit to history first, then copies the path or `![](path)` |

---

## Hotkeys

### Built-in (while tray is running)

Khi `python3 tray.py` (hoặc `main.py --tray`) đang chạy:

| Phím | Mac tương ứng | Hành động |
|------|---------------|-----------|
| `Ctrl+Shift+3` | ⌘⇧3 | Toàn màn hình (mở Editor) |
| `Ctrl+Shift+4` | ⌘⇧4 | Vùng chọn (mở Editor) |
| `Ctrl+Shift+5` | ⌘⇧5 | Cửa sổ đang active (mở Editor) |
| `Ctrl+Alt+Shift+3` | ⌃⌘⇧3 | Toàn màn hình → clipboard |
| `Ctrl+Alt+Shift+4` | ⌃⌘⇧4 | Vùng chọn → clipboard |
| `Ctrl+Alt+Shift+5` | ⌃⌘⇧5 | Cửa sổ active → clipboard |

Hotkeys unregister when the tray exits. X11 needs `gir1.2-keybinder-3.0`; on GNOME Wayland they register via Settings.

### Manual shortcut (no tray)

1. **Settings → Keyboard → View and Customize Shortcuts → Custom Shortcuts**
2. Add:
   - **Name:** `Mini Screenshot`
   - **Command:** `python3 /path/to/mini-screenshot/main.py`
   - **Shortcut:** e.g. `Ctrl+Shift+S`

Optional wrapper:

```bash
sudo tee /usr/local/bin/mini-screenshot > /dev/null << 'EOF'
#!/bin/bash
cd /path/to/mini-screenshot
python3 main.py "$@"
EOF
sudo chmod +x /usr/local/bin/mini-screenshot
```

---

## Project layout

```
mini-screenshot/
├── main.py                 # Thin CLI entry → mini_screenshot.cli
├── tray.py                 # Thin tray entry (+ GNOME --hotkey target)
├── mini_screenshot/        # Application package
│   ├── __init__.py
│   ├── __main__.py         # python3 -m mini_screenshot
│   ├── cli.py               # Argparse + capture → editor flow
│   ├── capture.py           # GNOME / grim+slurp + wmctrl window list
│   ├── editor.py             # Dark annotate UI (incl. spotlight/ruler/redact/copy-as)
│   ├── icons.py              # Vector toolbar icons
│   ├── ocr.py / ocr_dialog.py
│   ├── redact.py             # NEW — OCR + regex sensitive-info detection
│   ├── history.py            # NEW — recent-capture index on disk
│   ├── pin_window.py         # NEW — floating always-on-top viewer
│   ├── tray.py               # AppIndicator menu, history + pin + capture actions
│   ├── hotkeys.py            # Global hotkeys (gsettings / Keybinder)
│   ├── clipboard_util.py     # PNG → clipboard
│   ├── mac_window_style.py   # Rounded window + shadow post-process
│   ├── open_editor.py        # Spawn editor from tray (separate Qt process)
│   └── qt_env.py             # QT_QPA_PLATFORM helper
├── install.sh
├── packaging/
│   ├── build-deb.sh
│   ├── app-icon.svg
│   └── VERSION
└── README.md
```

---

## Package as `.deb`

```bash
chmod +x packaging/build-deb.sh
./packaging/build-deb.sh
```

Install:

```bash
sudo apt install ./build/mini-screenshot_<version>_all.deb
```

`apt install ./file.deb` pulls system deps automatically. `pytesseract` is vendored inside the package (no pip needed).

After install:

- Default: **tray** + **autostart** on login
- `mini-screenshot` with no args → tray; still supports `--full` / `--window` / …
- Activities → “Mini Screenshot”
- Tray hotkeys: `Ctrl+Shift+3/4/5`

Remove:

```bash
sudo apt remove mini-screenshot
```

Rebuild after code changes: run `./packaging/build-deb.sh` again, then `sudo apt install ./build/mini-screenshot_<version>_all.deb`.

---

## Notes

- Tested on **GNOME Wayland**. On X11, `grim`/`slurp` often still work; report issues if not.
- If `Ctrl+C` paste fails elsewhere, install `wl-clipboard` — the app prefers `wl-copy` for compatibility.
- GNOME window picker uses `wmctrl` (XWayland windows). Pure Wayland-native windows may be missing — a Wayland security limit, not an app bug.
- History files live under `$XDG_STATE_HOME/mini-screenshot/history` (falls back to `~/.local/state/...`); only the last 12 captures are kept, older ones are pruned automatically.
- Auto-redact is regex-based (email / VN phone / card-like digit runs / CCCD-CMND-like IDs) and only as good as the OCR read — always eyeball the result before sharing a screenshot.

---

## Roadmap

- [ ] Scrolling / long-page capture
- [ ] Short screen recording (GIF) via `wf-recorder`
- [ ] OCR result → quick translate
