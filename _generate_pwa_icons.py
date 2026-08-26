"""
Generates the PWA icon set (maskable-safe, opaque background) from the same
ball-icon drawing code as favicon.png/_generate_assets.py - reused here
instead of just resizing favicon.png, since favicon.png has a transparent
background (fine for a browser tab, but iOS/Android fill transparent PWA
icons with black by default, which looks broken on the home screen).
"""
from PIL import Image, ImageDraw

# render_ball() copied from _generate_assets.py rather than imported - that
# module has generation code at import time (including loading a font file
# for the wordmark logo), which isn't needed here and isn't safely importable.


def quad_bezier_points(p0, p1, p2, n=60):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((x, y))
    return pts


def render_ball(diameter, fill_color, seam_color, seam_width):
    size = diameter
    r = size / 2
    cx = cy = r

    content = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(content)
    d.ellipse([0, 0, size, size], fill=fill_color)
    d.line([(cx, 0), (cx, size)], fill=seam_color, width=seam_width)
    d.line([(0, cy), (size, cy)], fill=seam_color, width=seam_width)

    s = r / 15

    def pt(x, y):
        return (cx + (x - 16) * s, cy + (y - 16) * s)

    left = quad_bezier_points(pt(4.5, 4.5), pt(16, 16), pt(4.5, 27.5))
    right = quad_bezier_points(pt(27.5, 4.5), pt(16, 16), pt(27.5, 27.5))
    seam_w2 = max(1, int(seam_width * 0.85))
    d.line(left, fill=seam_color, width=seam_w2, joint="curve")
    d.line(right, fill=seam_color, width=seam_w2, joint="curve")

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)

    clipped = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    clipped.paste(content, (0, 0), mask)
    return clipped


OUT_DIR = "output/assets"
BG = "#EFEAD8"       # matches --bg (light theme)
BALL = "#A67C1E"     # matches --accent (light theme)
SEAM = "#EFEAD8"
SS = 4


def make_icon(size: int, padding_ratio: float = 0.14) -> Image.Image:
    """A ball icon centered on an opaque square background, with padding so
    it isn't cropped by OS icon masks (circular/squircle) on Android."""
    canvas = Image.new("RGBA", (size * SS, size * SS), BG)
    ball_diameter = int(size * SS * (1 - 2 * padding_ratio))
    ball = render_ball(ball_diameter, BALL, SEAM, int(ball_diameter * 0.055))
    offset = ((size * SS - ball_diameter) // 2, (size * SS - ball_diameter) // 2)
    canvas.paste(ball, offset, ball)
    return canvas.resize((size, size), Image.LANCZOS)


for size, name in [(192, "icon-192.png"), (512, "icon-512.png"), (180, "icon-180.png")]:
    make_icon(size).convert("RGB").save(f"{OUT_DIR}/{name}")

print("Saved icon-192.png, icon-512.png, icon-180.png to", OUT_DIR)
