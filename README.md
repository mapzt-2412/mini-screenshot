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
- Luu file (Ctrl+S) hoac copy thang vao clipboard (Ctrl+C) de paste noi khac

## Cai dat

```bash
chmod +x install.sh
./install.sh
```

Hoac cai thu cong (tren GNOME/Ubuntu mac dinh):

```bash
sudo apt install gnome-screenshot wl-clipboard tesseract-ocr tesseract-ocr-vie
pip3 install --break-system-packages PyQt5 Pillow pytesseract
```

Neu ban dung Sway/Hyprland (wlroots), cai them:

```bash
sudo apt install grim slurp
```

## Su dung

```bash
python3 main.py                 # chup vung chon (mac dinh) - keo chuot roi tha
python3 main.py --full          # chup toan man hinh
python3 main.py --window        # click chon 1 cua so de chup
python3 main.py --delay 3       # doi 3 giay roi chup vung chon
python3 main.py --delay 5 --full
```

Khi chon vung: keo chuot -> tha ra la chup, nhan `Esc` de huy.

## Gan phim tat (khuyen nghi: Ctrl+Shift+S)

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
├── main.py               # entry point, xu ly CLI args
├── capture.py             # backend chup man hinh (gnome-screenshot / grim+slurp)
├── editor.py              # cua so edit: toolbar dark theme + canvas + cac cong cu ve
├── icons.py                # ve icon vector cho toolbar (khong phu thuoc font/emoji)
├── ocr.py                  # trich xuat text bang pytesseract
├── ocr_dialog.py           # dialog hien thi ket qua OCR + nut Copy
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
gnome-screenshot, wl-clipboard) neu chua co. Thu vien `pytesseract` duoc dong goi san trong
file .deb (khong can pip).

Sau khi cai xong:
- Go lenh `mini-screenshot` trong terminal o bat ky thu muc nao, HOAC
- Mo **Activities** (GNOME) go "Mini Screenshot" se thay icon ung dung

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

## Tinh nang co the them sau (chua co trong ban dau)

- Scrolling capture (chup toan trang dai)
- Lich su cac ban chup gan day
- Pin anh thanh cua so noi luon-tren-cung
