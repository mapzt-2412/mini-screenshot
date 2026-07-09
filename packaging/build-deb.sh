#!/usr/bin/env bash
#
# build-deb.sh - dong goi Mini Screenshot Tool thanh file .deb de cai dat
# bang: sudo apt install ./mini-screenshot_1.0.0_all.deb
#
# Sau khi cai, go lenh `mini-screenshot` o bat ky dau, hoac tim
# "Mini Screenshot" trong app launcher (GNOME Activities).

set -e

APP_NAME="mini-screenshot"
VERSION="1.0.0"
ARCH="all"
PKG_DIR="build/${APP_NAME}_${VERSION}_${ARCH}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo ">> Don dep build cu (neu co)..."
rm -rf "${ROOT_DIR}/build"
mkdir -p "${ROOT_DIR}/${PKG_DIR}"
cd "${ROOT_DIR}"

echo ">> Tao cau truc thu muc goi .deb..."
mkdir -p "${PKG_DIR}/DEBIAN"
mkdir -p "${PKG_DIR}/usr/lib/${APP_NAME}"
mkdir -p "${PKG_DIR}/usr/bin"
mkdir -p "${PKG_DIR}/usr/share/applications"
mkdir -p "${PKG_DIR}/usr/share/icons/hicolor/scalable/apps"

echo ">> Copy source code..."
cp main.py capture.py editor.py icons.py ocr.py ocr_dialog.py "${PKG_DIR}/usr/lib/${APP_NAME}/"

echo ">> Vendor pytesseract (khong co goi apt python3-pytesseract tren Ubuntu)..."
VENDOR_DIR="${PKG_DIR}/usr/lib/${APP_NAME}/vendor"
pip3 install pytesseract packaging --target "${VENDOR_DIR}" --no-deps --quiet

echo ">> Tao file DEBIAN/control..."
cat > "${PKG_DIR}/DEBIAN/control" << EOF
Package: ${APP_NAME}
Version: ${VERSION}
Section: graphics
Priority: optional
Architecture: ${ARCH}
Depends: python3 (>= 3.8), python3-pyqt5, python3-pil, tesseract-ocr, tesseract-ocr-vie, gnome-screenshot, wl-clipboard
Recommends: grim, slurp
Maintainer: Ban <you@example.com>
Description: Mini Screenshot Tool - chup va chinh sua anh man hinh
 Cong cu chup man hinh mini cho Ubuntu/GNOME Wayland, ho tro chon vung,
 ve/annotate (but, mui ten, chu nhat, hinh tron, highlight, text, danh so
 buoc), blur/pixelate che thong tin nhay cam, crop, color picker,
 undo/redo, luu file hoac copy thang vao clipboard.
EOF

echo ">> Tao script khoi chay usr/bin/${APP_NAME}..."
cat > "${PKG_DIR}/usr/bin/${APP_NAME}" << EOF
#!/bin/bash
export PYTHONPATH="/usr/lib/${APP_NAME}/vendor\${PYTHONPATH:+:\$PYTHONPATH}"
exec python3 /usr/lib/${APP_NAME}/main.py "\$@"
EOF
chmod +x "${PKG_DIR}/usr/bin/${APP_NAME}"

echo ">> Tao icon ung dung..."
cp packaging/app-icon.svg "${PKG_DIR}/usr/share/icons/hicolor/scalable/apps/${APP_NAME}.svg"

echo ">> Tao file .desktop (app launcher)..."
cat > "${PKG_DIR}/usr/share/applications/${APP_NAME}.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Mini Screenshot
Comment=Chup va chinh sua anh man hinh
Exec=${APP_NAME}
Icon=${APP_NAME}
Terminal=false
Categories=Graphics;Utility;
Keywords=screenshot;capture;chup man hinh;
EOF

echo ">> Set quyen chuan cho package..."
find "${PKG_DIR}" -type d -exec chmod 755 {} \;
find "${PKG_DIR}" -type f -not -path "*/DEBIAN/*" -exec chmod 644 {} \;
chmod +x "${PKG_DIR}/usr/bin/${APP_NAME}"

echo ">> Build file .deb..."
dpkg-deb --root-owner-group --build "${PKG_DIR}"

OUT_DEB="build/${APP_NAME}_${VERSION}_${ARCH}.deb"
echo ""
echo "Xong! File .deb da tao tai: ${OUT_DEB}"
echo ""
echo "Cai dat bang:"
echo "  sudo apt install ./${OUT_DEB}"
echo ""
echo "Sau khi cai, chay bang lenh: ${APP_NAME}"
echo "hoac tim 'Mini Screenshot' trong app launcher."
