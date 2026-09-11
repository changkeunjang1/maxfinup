"""One-off script: generate maxfinup favicon assets from the site's brand mark."""
from PIL import Image, ImageDraw, ImageFont

NAVY = (21, 43, 75, 255)      # --ink
BRASS = (40, 93, 219, 255)    # --brass
WHITE = (255, 255, 255, 255)

FONT_PATH = r"C:\Windows\Fonts\malgunbd.ttf"
GLYPH = "\u5e33"  # 帳

def render(size: int) -> Image.Image:
    scale = 4
    big = size * scale
    img = Image.new("RGBA", (big, big), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    radius = int(big * 0.22)
    draw.rounded_rectangle([0, 0, big - 1, big - 1], radius=radius, fill=NAVY)

    border_w = max(1, int(big * 0.035))
    draw.rounded_rectangle(
        [border_w // 2, border_w // 2, big - 1 - border_w // 2, big - 1 - border_w // 2],
        radius=radius,
        outline=BRASS,
        width=border_w,
    )

    font_size = int(big * 0.62)
    font = ImageFont.truetype(FONT_PATH, font_size)
    bbox = draw.textbbox((0, 0), GLYPH, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (big - w) / 2 - bbox[0]
    y = (big - h) / 2 - bbox[1]
    draw.text((x, y), GLYPH, font=font, fill=WHITE)

    return img.resize((size, size), Image.LANCZOS)


if __name__ == "__main__":
    import os
    out_dir = os.path.join(os.path.dirname(__file__), "..", "ledger", "static", "ledger", "favicon")
    os.makedirs(out_dir, exist_ok=True)

    sizes = {
        "favicon-16.png": 16,
        "favicon-32.png": 32,
        "favicon-48.png": 48,
        "apple-touch-icon.png": 180,
        "icon-512.png": 512,
    }
    imgs = {}
    for name, size in sizes.items():
        img = render(size)
        imgs[name] = img
        img.save(os.path.join(out_dir, name))

    ico_path = os.path.join(out_dir, "favicon.ico")
    imgs["favicon-48.png"].save(
        ico_path,
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48)],
    )
    print("done ->", out_dir)
