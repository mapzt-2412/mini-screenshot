# Mini Screenshot Tool (Ubuntu 22.04 / Wayland)

App chup man hinh mini viet bang Python + PyQt5. App tu dong nhan dien
desktop environment de chon backend chup man hinh phu hop tren Wayland:

- **GNOME Shell** (mac dinh tren Ubuntu) -> dung `gnome-screenshot`
  (goi D-Bus API `org.gnome.Shell.Screenshot` co san cua he thong)
- **Sway / Hyprland / cac compositor dong wlroots** -> dung `grim` + `slurp`

> Ly do phai tach 2 backend: `grim`/`slurp` chi hoat dong tren compositor
> dong wlroots. GNOME Shell (Mutter) KHONG ho tro protocol
> `wlr-screencopy` ma 2 tool nay can, nen neu dung grim/slurp tren GNOME,
> `slurp` se khong hien overlay gi ca va bao "huy chon vung".

## Tinh nang

- Chup vung chon (keo tha chuot), chup toan man hinh, hoac chup 1 cua so
  - Chup cua so: tren GNOME se hien **popup cho chon cua so** trong danh
    sach cac cua so dang mo (can cai `wmctrl`, xem phan Cai dat), roi tu
    dong focus + chup dung cua so ban chon. Tren Sway/Hyprland (wlroots)
    thi click truc tiep vao cua so muon chup (slurp -w).
- Chup co delay (dem nguoc N giay)
- Giao dien Edit dark theme, icon vector rieng cho tung cong cu, group ro rang:
  - But ve tu do, duong thang, mui ten, hinh chu nhat, hinh tron
  - Highlighter (danh dau mau vang/trong suot)
  - Chen text
  - Danh so buoc (1, 2, 3...) - hop cho huong dan/tutorial
  - Blur / Pixelate - che thong tin nhay cam
  - Crop lai anh
  - Color picker - click vao anh de lay ma mau hex (tu dong copy clipboard)
  - **OCR Extract Text** - trich xuat text tu toan anh (nut toolbar) hoac vung chon (cong cu OCR)
  - Undo / Redo (Ctrl+Z / Ctrl+Shift+Z)
  - Nut chon mau hien thi truc tiep mau dang dung + spin box do day net
- Chup xong se TU DONG mo cua so Edit de ve/annotate ngay, khong can lam
  gi them
- Luu file (Ctrl+S) hoac copy thang vao clipboard (Ctrl+C) de paste noi khac

## Cai dat

```bash
chmod +x install.sh
./install.sh
```

Hoac cai thu cong (tren GNOME/Ubuntu mac dinh):

```bash
sudo apt install gnome-screenshot wl-clipboard tesseract-ocr tesseract-ocr-vie wmctrl
pip3 install --break-system-packages PyQt5 Pillow pytesseract
```

> `wmctrl` khong bat buoc, nhung neu khong cai thi khi chup cua so
> (`--window`) app se KHONG hien popup chon cua so duoc - se tu dong
> fallback ve chup cua so dang active (giong nhu truoc).

Neu ban dung Sway/Hyprland (wlroots), cai them:

```bash
sudo apt install grim slurp
```

## Su dung

```bash
python3 main.py                 # chup vung chon (mac dinh) - keo chuot roi tha
python3 main.py --full          # chup toan man hinh
python3 main.py --window        # hien popup chon 1 cua so, roi chup no
python3 main.py --window --mac-style   # chup 1 cua so da chon, bo goc + shadow + nen trong suot kieu macOS
python3 main.py --delay 3       # doi 3 giay roi chup vung chon
python3 main.py --delay 5 --full
```

Khi chon vung: keo chuot -> tha ra la chup, nhan `Esc` de huy.

Khi chup cua so tren GNOME: mot popup se hien danh sach cua so dang mo,
chon 1 cai roi bam OK - app se tu focus cua so do va chup ngay. Neu bam
Cancel hoac chua cai `wmctrl`, app se chup cua so dang active thay the.

Sau khi chup xong (bat ky mode nao), cua so **Edit** se tu mo ra ngay voi
tam anh vua chup de ban ve/annotate, crop, blur, OCR, v.v.

## Gan phim tat

### Noi tai khi chay tray (kieu macOS)

Khi `python3 tray.py` (hoac `main.py --tray`) dang chay:

| Phim | Mac tuong ung | Hanh dong |
|------|---------------|-----------|
| `Ctrl+Shift+3` | ⌘⇧3 | Toan man hinh |
| `Ctrl+Shift+4` | ⌘⇧4 | Vung chon |
| `Ctrl+Shift+5` | ⌘⇧5 | Cua so dang active |

Phim tat tu go khi thoat tray. Tren X11 can `gir1.2-keybinder-3.0`;
tren GNOME Wayland app tu dang ky qua Settings.

### Thu cong (khong can tray)

1. Mo **Settings > Keyboard > View and Customize Shortcuts > Custom Shortcuts**
2. Bam **+** de them shortcut moi:
   - Name: `Mini Screenshot`
   - Command: `python3 /duong/dan/toi/screenshot-app/main.py`
     (dung full path, hoac tao 1 script wrapper trong `/usr/local/bin`)
   - Shortcut: `Ctrl+Shift+S`

Goi y tao wrapper de khong phai go full path:

```bash
sudo tee /usr/local/bin/mini-screenshot > /dev/null << 'EOF'
#!/bin/bash
cd /duong/dan/toi/screenshot-app
python3 main.py "$@"
EOF
sudo chmod +x /usr/local/bin/mini-screenshot
```

Roi dung `mini-screenshot` lam Command trong buoc gan phim tat.

## Cau truc project

```
screenshot-app/
├── main.py               # entry point, xu ly CLI args + popup chon cua so
├── capture.py             # backend chup man hinh (gnome-screenshot / grim+slurp) + chon cua so qua wmctrl
├── editor.py              # cua so edit: toolbar dark theme + canvas + cac cong cu ve
├── icons.py                # ve icon vector cho toolbar (khong phu thuoc font/emoji)
├── ocr.py                  # trich xuat text bang pytesseract
├── ocr_dialog.py           # dialog hien thi ket qua OCR + nut Copy
├── tray.py                # system tray + menu + goi hotkeys
├── hotkeys.py              # phim tat global kieu macOS (Keybinder / GNOME)
├── install.sh              # script cai dependencies (chay truc tiep bang python3)
├── packaging/
│   ├── build-deb.sh        # script dong goi thanh file .deb
│   └── app-icon.svg        # icon ung dung dung trong app launcher
└── README.md
```

## Dong goi thanh file .deb (cai nhu app that)

Neu ban muon cai dat nhu mot ung dung Ubuntu binh thuong (co trong app
launcher, go lenh `mini-screenshot` o bat ky dau), dong goi thanh `.deb`:

```bash
chmod +x packaging/build-deb.sh
./packaging/build-deb.sh
```

Script se tao file `build/mini-screenshot_1.0.0_all.deb`. Cai dat bang:

```bash
sudo apt install ./build/mini-screenshot_1.0.0_all.deb
```

`apt install ./file.deb` (thay vi `dpkg -i`) se tu dong cai luon cac
dependencies (python3-pyqt5, python3-pil, tesseract-ocr, tesseract-ocr-vie,
gnome-screenshot, wl-clipboard, wmctrl) neu chua co. Thu vien `pytesseract`
duoc dong goi san trong file .deb (khong can pip).

Sau khi cai xong:
- Mac dinh mo **tray** (icon topbar) + **autostart** khi dang nhap
- Go `mini-screenshot` (khong args) = tray; van dung duoc
  `mini-screenshot --full` / `--window` / ... de chup 1 lan
- Mo **Activities** go "Mini Screenshot" cung mo tray
- Phim tat khi tray chay: `Ctrl+Shift+3/4/5`

Go bo:
```bash
sudo apt remove mini-screenshot
```

Cap nhat sau khi sua code: chi can chay lai `./packaging/build-deb.sh` roi
`sudo apt install ./build/mini-screenshot_1.0.0_all.deb` de cai de len ban
cu (apt tu nhan dien va update).

## Ghi chu

- App test tren Wayland (GNOME). Neu ban dung X11, `grim`/`slurp` van hoat
  dong binh thuong tren nhieu compositor, nhung neu gap loi hay bao lai.
- Neu Ctrl+C khong paste duoc sang app khac, kiem tra da cai `wl-clipboard`
  chua (`sudo apt install wl-clipboard`) - app da tu dong fallback dung
  `wl-copy` de tang tuong thich.
- Popup chon cua so (GNOME) dung `wmctrl`, chi thay duoc cac cua so chay
  qua XWayland (da so app pho bien tren Ubuntu GNOME hien nay). Cua so
  Wayland-native thuan tuy se khong xuat hien trong danh sach - day la
  gioi han bao mat cua Wayland, khong phai loi cua app.

## Tinh nang co the them sau (chua co trong ban dau)

- Scrolling capture (chup toan trang dai)
- Lich su cac ban chup gan day
- Pin anh thanh cua so noi luon-tren-cung
