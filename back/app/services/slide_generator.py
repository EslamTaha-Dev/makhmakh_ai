from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


BASE_DIR = Path("generated/slides")


def _get_font(size: int):
    candidates = [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
    ]

    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


def _wrap_text(text: str, max_chars: int = 65):
    words = text.split()
    lines = []
    current = ""

    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current += (" " if current else "") + word
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def create_slides(script: dict, lesson_id: str) -> list[str]:
    output_dir = BASE_DIR / lesson_id
    output_dir.mkdir(parents=True, exist_ok=True)

    title_font = _get_font(54)
    heading_font = _get_font(42)
    body_font = _get_font(30)

    slide_paths = []
    image = Image.new("RGB", (1280, 720), "white")
    draw = ImageDraw.Draw(image)

    draw.text(
        (80, 100),
        script["title"],
        fill="black",
        font=title_font,
    )

    draw.text(
        (80, 220),
        "makhmakh Educational Lesson",
        fill="black",
        font=body_font,
    )

    path = output_dir / "slide_01.png"
    image.save(path)
    slide_paths.append(str(path))

    for index, section in enumerate(script["sections"], start=2):
        image = Image.new("RGB", (1280, 720), "white")
        draw = ImageDraw.Draw(image)

        draw.text(
            (80, 70),
            section["heading"],
            fill="black",
            font=heading_font,
        )

        lines = _wrap_text(section["explanation"])

        y = 180

        for line in lines:
            draw.text(
                (80, y),
                line,
                fill="black",
                font=body_font,
            )
            y += 48

        path = output_dir / f"slide_{index:02d}.png"
        image.save(path)

        slide_paths.append(str(path))
    image = Image.new("RGB", (1280, 720), "white")
    draw = ImageDraw.Draw(image)

    draw.text(
        (80, 80),
        "Summary",
        fill="black",
        font=heading_font,
    )

    lines = _wrap_text(script["summary"])

    y = 190

    for line in lines:
        draw.text(
            (80, y),
            line,
            fill="black",
            font=body_font,
        )
        y += 48

    path = output_dir / f"slide_{len(slide_paths) + 1:02d}.png"
    image.save(path)
    slide_paths.append(str(path))

    return slide_paths