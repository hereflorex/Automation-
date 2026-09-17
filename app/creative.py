from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent

BOLD_FONT_CANDIDATES = [
    ROOT / "assets" / "DejaVuSans-Bold.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"),
    Path("/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
]

REGULAR_FONT_CANDIDATES = [
    ROOT / "assets" / "DejaVuSans.ttf",
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/dejavu/DejaVuSans.ttf"),
    Path("/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"),
    Path("/usr/share/fonts/truetype/freefont/FreeSans.ttf"),
]


def find_font(candidates):
    for candidate in candidates:
        try:
            if candidate.is_file():
                return str(candidate)
        except OSError:
            continue
    return None


BOLD_FONT = find_font(BOLD_FONT_CANDIDATES)
REGULAR_FONT = find_font(REGULAR_FONT_CANDIDATES)


def ft(size, bold=True):
    font_path = BOLD_FONT if bold else REGULAR_FONT
    if font_path:
        try:
            return ImageFont.truetype(font_path, int(size))
        except OSError:
            pass
    return ImageFont.load_default()


def wrap(text, max_chars):
    words = str(text or "").split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > max_chars:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def make_thumbnail(title, topic, outpath):
    image = Image.new("RGB", (1280, 720), (7, 8, 12))
    draw = ImageDraw.Draw(image)

    for x in range(0, 1280, 80):
        draw.line((x, 0, x, 720), fill=(22, 25, 32), width=1)
    for y in range(0, 720, 80):
        draw.line((0, y, 1280, y), fill=(22, 25, 32), width=1)

    variation = sum(map(ord, str(topic or ""))) % 3
    center_x = 1030 if variation != 1 else 250
    draw.ellipse(
        (center_x - 190, 170, center_x + 190, 550),
        outline=(0, 180, 215),
        width=5,
    )

    draw.text((55, 42), "NOIR//NULL", font=ft(30), fill=(0, 220, 245))

    text_x = 65 if variation != 1 else 500
    text_y = 150 if variation != 2 else 95
    for line in wrap(str(title or "Untitled").upper(), 21)[:4]:
        draw.text(
            (text_x, text_y),
            line,
            font=ft(62),
            fill=(245, 245, 245),
            stroke_width=2,
            stroke_fill=(0, 0, 0),
        )
        text_y += 72

    draw.text(
        (65, 650),
        "FLORΞXIA  •  EXPLAINED",
        font=ft(22, False),
        fill=(150, 150, 160),
    )

    output = Path(outpath)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True)
    return output


def make_banner(outpath, channel="NOIR//NULL"):
    image = Image.new("RGB", (2560, 1440), (5, 6, 9))
    draw = ImageDraw.Draw(image)

    for x in range(0, 2560, 128):
        draw.line((x, 0, x, 1440), fill=(18, 21, 28), width=2)
    for y in range(0, 1440, 128):
        draw.line((0, y, 2560, y), fill=(18, 21, 28), width=2)

    draw.ellipse(
        (1830, 360, 2370, 900),
        outline=(0, 190, 220),
        width=8,
    )
    draw.text((180, 520), str(channel or "NOIR//NULL"), font=ft(125), fill=(245, 245, 245))
    draw.text(
        (188, 675),
        "THE INTERNET, EXPLAINED DIFFERENTLY",
        font=ft(42, False),
        fill=(130, 220, 235),
    )

    output = Path(outpath)
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, format="PNG", optimize=True)
    return output
