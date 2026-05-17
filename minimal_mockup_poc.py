from __future__ import annotations

"""Minimal mockup proof-of-concept using OpenCV + Pillow.

Generates a mug-like product background, warps user artwork into a print area,
blends shadows/highlights, and exports preview image.
"""

from pathlib import Path
import argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import cv2


def create_default_artwork(path: Path, size=(900, 900)) -> None:
    img = Image.new("RGBA", size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((80, 80, size[0]-80, size[1]-80), radius=100, fill=(37, 99, 235, 235))
    draw.ellipse((180, 180, size[0]-180, size[1]-180), fill=(245, 158, 11, 230))
    draw.text((size[0]//2 - 120, size[1]//2 - 15), "MOCKUP", fill=(15, 23, 42, 255))
    img.save(path)


def create_mug_template(size=(1400, 1000)):
    w, h = size
    bg = Image.new("RGBA", size, (242, 244, 248, 255))
    draw = ImageDraw.Draw(bg)

    # table and subtle gradient backdrop
    draw.rectangle((0, int(h*0.72), w, h), fill=(226, 229, 235, 255))

    mug_rect = (380, 230, 1030, 820)
    draw.rounded_rectangle(mug_rect, radius=140, fill=(247, 247, 247, 255), outline=(210, 212, 218, 255), width=4)

    # handle
    draw.rounded_rectangle((980, 340, 1190, 700), radius=110, fill=(250, 250, 250, 255), outline=(210, 212, 218, 255), width=4)
    draw.rounded_rectangle((1035, 395, 1140, 645), radius=70, fill=(242, 244, 248, 255))

    # print area as quadrilateral (slightly perspective)
    src_quad = np.float32([[0, 0], [900, 0], [900, 900], [0, 900]])
    dst_quad = np.float32([[480, 340], [940, 320], [920, 730], [500, 740]])

    # mask for printable area
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon([tuple(p) for p in dst_quad], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(0.6))

    # shadow / highlight layers
    shadow = Image.new("L", size, 0)
    sdraw = ImageDraw.Draw(shadow)
    sdraw.ellipse((350, 240, 1070, 820), fill=75)
    shadow = shadow.filter(ImageFilter.GaussianBlur(45))

    highlight = Image.new("L", size, 0)
    hdraw = ImageDraw.Draw(highlight)
    hdraw.ellipse((470, 280, 620, 760), fill=130)
    highlight = highlight.filter(ImageFilter.GaussianBlur(50))

    return bg, src_quad, dst_quad, mask, shadow, highlight


def warp_artwork(artwork: Image.Image, src_quad: np.ndarray, dst_quad: np.ndarray, out_size: tuple[int, int]) -> Image.Image:
    arr = np.array(artwork.convert("RGBA"))
    matrix = cv2.getPerspectiveTransform(src_quad, dst_quad)
    warped = cv2.warpPerspective(arr, matrix, out_size, flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_TRANSPARENT)
    return Image.fromarray(warped, "RGBA")


def blend(base: Image.Image, warped: Image.Image, mask: Image.Image, shadow: Image.Image, highlight: Image.Image) -> Image.Image:
    canvas = base.copy()
    canvas.paste(warped, (0, 0), mask)

    # multiply-style shadow
    shadow_rgba = Image.merge("RGBA", (shadow, shadow, shadow, shadow.point(lambda v: int(v * 0.58))))
    canvas = Image.alpha_composite(canvas, shadow_rgba)

    # screen-style highlight
    hi = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
    hi.putalpha(highlight.point(lambda v: int(v * 0.35)))
    canvas = Image.alpha_composite(canvas, hi)

    # ground shadow
    ground = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(ground)
    gdraw.ellipse((450, 760, 1030, 890), fill=(45, 52, 62, 65))
    ground = ground.filter(ImageFilter.GaussianBlur(25))
    return Image.alpha_composite(canvas, ground)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a minimal mockup preview.")
    parser.add_argument("--artwork", type=Path, default=Path("samples/artwork.png"))
    parser.add_argument("--out", type=Path, default=Path("output/mockup_preview.png"))
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.artwork.parent.mkdir(parents=True, exist_ok=True)

    if not args.artwork.exists():
        create_default_artwork(args.artwork)

    artwork = Image.open(args.artwork).convert("RGBA")
    base, src_quad, dst_quad, mask, shadow, highlight = create_mug_template()
    warped = warp_artwork(artwork, src_quad, dst_quad, base.size)
    result = blend(base, warped, mask, shadow, highlight)
    result.save(args.out)
    print(f"Generated mockup: {args.out}")


if __name__ == "__main__":
    main()
