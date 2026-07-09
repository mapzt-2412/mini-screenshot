"""
mac_window_style.py

Hau xu ly anh chup cua so de gia lap style macOS:
- Bo goc cua so (rounded corners)
- Drop shadow mo (blur) phia duoi cua so
- Nen trong suot (RGBA PNG), khong bi vien trang du

LY DO CAN MODULE NAY:
gnome-screenshot / grim+slurp chi tra ve anh raster hinh chu nhat thuan
tuy - khong co shadow, khong co alpha o goc, vi Mutter/wlroots khong
expose thong tin do qua cac API chup man hinh nay (khac voi macOS,
noi WindowServer da render san shadow/alpha truoc khi chup). Module
nay "ve them" hieu ung do bang Pillow sau khi da chup xong anh cua so.

Cach dung:
    from mac_window_style import apply_mac_style
    out_path = apply_mac_style("/tmp/screenshot_capture_123.png")
    # out_path la file PNG moi, nen trong suot, co shadow + bo goc
"""

from PIL import Image, ImageDraw, ImageFilter
import os


def _rounded_mask(size, radius):
    """Tao mask trang-den bo goc, dung antialias bang cach ve o kich thuoc
    lon hon roi resize xuong (giup net bo goc muot hon, gia lap HiDPI)."""
    scale = 4  # supersampling factor -> net hon, gia lap Retina
    w, h = size
    big = Image.new("L", (w * scale, h * scale), 0)
    draw = ImageDraw.Draw(big)
    draw.rounded_rectangle(
        [0, 0, w * scale - 1, h * scale - 1],
        radius=radius * scale,
        fill=255,
    )
    return big.resize((w, h), Image.LANCZOS)


def apply_mac_style(
    input_path,
    output_path=None,
    corner_radius=14,
    shadow_blur=28,
    shadow_offset=(0, 14),
    shadow_opacity=110,
    padding=60,
):
    """
    Bien anh chup cua so (hinh chu nhat, nen dac) thanh anh PNG kieu macOS:
    bo goc + drop shadow + nen trong suot.

    Tham so:
        input_path:      duong dan anh goc (vd tu capture_window())
        output_path:      duong dan file xuat, mac dinh them hau to _mac.png
        corner_radius:    ban kinh bo goc, tinh theo px cua anh goc
        shadow_blur:      do mo cua shadow (Gaussian blur radius)
        shadow_offset:    (dx, dy) shadow lech xuong duoi bao nhieu px
        shadow_opacity:   do dam shadow (0-255)
        padding:          khoang trong suot them quanh anh de chua shadow

    Tra ve: duong dan file da xu ly.
    """
    img = Image.open(input_path).convert("RGBA")
    w, h = img.size

    # 1. Bo goc anh cua so bang mask
    mask = _rounded_mask((w, h), corner_radius)
    rounded = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    rounded.paste(img, (0, 0), mask)

    # 2. Canvas moi lon hon, nen trong suot hoan toan, du cho shadow toa ra
    canvas_w = w + padding * 2
    canvas_h = h + padding * 2
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

    # 3. Ve shadow: dung chinh mask bo goc lam hinh dang shadow, to den mo
    shadow_layer = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    shadow_shape = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shadow_shape.paste((0, 0, 0, shadow_opacity), (0, 0), mask)
    sx = padding + shadow_offset[0]
    sy = padding + shadow_offset[1]
    shadow_layer.paste(shadow_shape, (sx, sy), shadow_shape)
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(shadow_blur))

    # 4. Ghep: shadow truoc, cua so bo goc de len tren
    canvas = Image.alpha_composite(canvas, shadow_layer)
    canvas.alpha_composite(rounded, (padding, padding))

    if output_path is None:
        base, _ = os.path.splitext(input_path)
        output_path = f"{base}_mac.png"

    canvas.save(output_path, "PNG")
    return output_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Dung: python3 mac_window_style.py <input.png> [output.png]")
        sys.exit(1)
    inp = sys.argv[1]
    outp = sys.argv[2] if len(sys.argv) > 2 else None
    result = apply_mac_style(inp, outp)
    print(f"Da luu: {result}")
