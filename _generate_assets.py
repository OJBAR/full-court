from PIL import Image, ImageDraw, ImageFont


def quad_bezier_points(p0, p1, p2, n=60):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((x, y))
    return pts


def render_ball(diameter, fill_color, seam_color, seam_width):
    """
    Returns a standalone RGBA image of the ball icon, hard-clipped to its own
    circle so the seam lines can never poke out past the edge (the seam
    curves' control points fall slightly outside the circle by construction,
    so drawing + clipping is used instead of trusting the raw coordinates).
    """
    size = diameter
    r = size / 2
    cx = cy = r

    content = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(content)
    d.ellipse([0, 0, size, size], fill=fill_color)
    d.line([(cx, 0), (cx, size)], fill=seam_color, width=seam_width)
    d.line([(0, cy), (size, cy)], fill=seam_color, width=seam_width)

    s = r / 15  # original design used a radius-15 circle in a 32-unit box

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


def crop_to_content(img):
    bbox = img.getbbox()
    return img.crop(bbox) if bbox else img


SS = 4  # supersampling factor for smooth anti-aliased curves

# --- Favicon ---
size = 512
ball_big = render_ball(size * SS, "#A67C1E", "#EFEAD8", int(size * SS * 0.055))
favicon = ball_big.resize((size, size), Image.LANCZOS)
favicon.save("favicon.png")

# --- Logo (light + dark) ---
FONT_PATH = "_bebas_neue.ttf"
W, H = 1500, 320
ball_r = 130
ball_cx = ball_r + 10
ball_cy = H / 2
font_big = ImageFont.truetype(FONT_PATH, 190 * SS)
text = "FULL COURT"


def make_logo(text_color, ball_fill, seam_color):
    img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    ball_img = render_ball(int(ball_r * 2 * SS), ball_fill, seam_color, int(ball_r * SS * 0.11))
    img.paste(ball_img, (int((ball_cx - ball_r) * SS), int((ball_cy - ball_r) * SS)), ball_img)

    d = ImageDraw.Draw(img)
    bbox = d.textbbox((0, 0), text, font=font_big)
    text_h = bbox[3] - bbox[1]
    text_x = (ball_cx + ball_r + 36) * SS
    text_y = H * SS / 2 - text_h / 2 - bbox[1]
    d.text((text_x, text_y), text, font=font_big, fill=text_color)

    small = img.resize((W, H), Image.LANCZOS)
    return crop_to_content(small)


make_logo("#2E2A1E", "#A67C1E", "#EFEAD8").save("logo_light.png")
make_logo("#F0E6D6", "#E08A3E", "#2A2118").save("logo_dark.png")

print("Saved favicon.png, logo_light.png, logo_dark.png")
