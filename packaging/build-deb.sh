#!/usr/bin/env bash
#
# build-deb.sh - dong goi Mini Screenshot Tool thanh file .deb de cai dat
# bang: sudo apt install ./build/mini-screenshot_<version>_all.deb
#
# Moi lan build se doc version cu (packaging/VERSION hoac ban da cai)
# roi tu tang patch: 1.0.0 -> 1.0.1 -> 1.0.2 ...
#
# Sau khi cai, go lenh `mini-screenshot` o bat ky dau, hoac tim
# "Mini Screenshot" trong app launcher (GNOME Activities).

set -e

APP_NAME="mini-screenshot"
ARCH="all"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_FILE="${ROOT_DIR}/packaging/VERSION"
DEFAULT_VERSION="1.0.0"

version_max() {
  local a="$1" b="$2"
  if [[ -z "$a" ]]; then echo "$b"; return; fi
  if [[ -z "$b" ]]; then echo "$a"; return; fi
  printf '%s\n' "$a" "$b" | sort -V | tail -n1
}

bump_patch() {
  local v="$1"
  local major minor patch
  IFS=. read -r major minor patch <<< "${v}"
  major=${major:-0}
  minor=${minor:-0}
  patch=${patch:-0}
  echo "${major}.${minor}.$((patch + 1))"
}

# Version da luu tu lan build truoc
SAVED_VERSION=""
if [[ -f "${VERSION_FILE}" ]]; then
  SAVED_VERSION="$(tr -d '[:space:]' < "${VERSION_FILE}")"
fi

# Version dang cai tren may (neu co)
INSTALLED_VERSION=""
if command -v dpkg-query >/dev/null 2>&1; then
  INSTALLED_VERSION="$(dpkg-query -W -f='${Version}' "${APP_NAME}" 2>/dev/null || true)"
fi

if [[ -z "${SAVED_VERSION}" && -z "${INSTALLED_VERSION}" ]]; then
  VERSION="${DEFAULT_VERSION}"
  BASE_VERSION="(chua co)"
else
  BASE_VERSION="$(version_max "${SAVED_VERSION}" "${INSTALLED_VERSION}")"
  VERSION="$(bump_patch "${BASE_VERSION}")"
fi

echo "${VERSION}" > "${VERSION_FILE}"
echo ">> Version: ${VERSION} (base: ${BASE_VERSION}${INSTALLED_VERSION:+, da cai: ${INSTALLED_VERSION}})"

PKG_DIR="build/${APP_NAME}_${VERSION}_${ARCH}"

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
cp main.py tray.py "${PKG_DIR}/usr/lib/${APP_NAME}/"
cp -a mini_screenshot "${PKG_DIR}/usr/lib/${APP_NAME}/"
# Drop bytecode if any slipped in
find "${PKG_DIR}/usr/lib/${APP_NAME}" -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true

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
Depends: python3 (>= 3.8), python3-pyqt5, python3-pil, tesseract-ocr, tesseract-ocr-vie, gnome-screenshot, wl-clipboard, wmctrl, python3-gi, gir1.2-appindicator3-0.1
Recommends: grim, slurp, gnome-shell-extension-appindicator, gir1.2-keybinder-3.0
Maintainer: Ban <you@example.com>
Description: Mini Screenshot Tool - chup va chinh sua anh man hinh
 Cong cu chup man hinh mini cho Ubuntu/GNOME Wayland, ho tro chon vung,
 chon cua so can chup tu danh sach (wmctrl), ve/annotate (but, mui ten,
 chu nhat, hinh tron, highlight, text, danh so buoc), blur/pixelate che
 thong tin nhay cam, crop, color picker, undo/redo, luu file hoac copy
 thang vao clipboard.
EOF

echo ">> Tao script khoi chay usr/bin/${APP_NAME}..."
cat > "${PKG_DIR}/usr/bin/${APP_NAME}" << EOF
#!/bin/bash
LIB="/usr/lib/${APP_NAME}"
export PYTHONPATH="\${LIB}/vendor:\${LIB}\${PYTHONPATH:+:\$PYTHONPATH}"
# No args -> tray (default). Still supports: ${APP_NAME} --full, --window, ...
if [ \$# -eq 0 ]; then
  exec python3 "\${LIB}/main.py" --tray
fi
exec python3 "\${LIB}/main.py" "\$@"
EOF
chmod +x "${PKG_DIR}/usr/bin/${APP_NAME}"

echo ">> Tao icon ung dung..."
cp packaging/app-icon.svg "${PKG_DIR}/usr/share/icons/hicolor/scalable/apps/${APP_NAME}.svg"

echo ">> Tao file .desktop (mac dinh: tray)..."
cat > "${PKG_DIR}/usr/share/applications/${APP_NAME}.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Mini Screenshot
Comment=Chup man hinh - icon tren topbar, phim tat Ctrl+Shift+3/4/5
Exec=${APP_NAME} --tray
Icon=${APP_NAME}
Terminal=false
Categories=Graphics;Utility;
Keywords=screenshot;tray;topbar;capture;chup man hinh;
EOF

echo ">> Tao file autostart tray (bat mac dinh)..."
mkdir -p "${PKG_DIR}/etc/xdg/autostart"
cat > "${PKG_DIR}/etc/xdg/autostart/${APP_NAME}-tray.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Mini Screenshot Tray
Comment=Tu khoi dong Mini Screenshot tren topbar
Exec=${APP_NAME} --tray
Icon=${APP_NAME}
Terminal=false
X-GNOME-Autostart-enabled=true
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
