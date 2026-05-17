from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageOps, ImageDraw

IN_DIR = Path("output/sweep")
OUT = Path("output/sweep_contact_sheet.jpg")
THUMB = (360, 300)
COLUMNS = 5
PAD = 16
LABEL_H = 36


def main() -> None:
    files = sorted([p for p in IN_DIR.glob("*.png")])
    if not files:
        raise SystemExit("No png files in output/sweep")

    rows = (len(files) + COLUMNS - 1) // COLUMNS
    w = COLUMNS * THUMB[0] + (COLUMNS + 1) * PAD
    h = rows * (THUMB[1] + LABEL_H) + (rows + 1) * PAD
    canvas = Image.new("RGB", (w, h), (245, 246, 250))
    draw = ImageDraw.Draw(canvas)

    for i, p in enumerate(files):
        r = i // COLUMNS
        c = i % COLUMNS
        x = PAD + c * THUMB[0] + c * PAD
        y = PAD + r * (THUMB[1] + LABEL_H) + r * PAD

        img = Image.open(p).convert("RGB")
        thumb = ImageOps.fit(img, THUMB)
        canvas.paste(thumb, (x, y))
        draw.text((x, y + THUMB[1] + 8), p.stem, fill=(30, 34, 42))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT, quality=90)
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
