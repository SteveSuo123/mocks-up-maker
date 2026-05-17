from __future__ import annotations

"""Minimal mockup proof-of-concept using OpenCV + Pillow.

Supports:
- User-provided mug image (`--mug`)
- User-provided artwork (`--artwork`)
- Custom print area quad (`--quad x1,y1 x2,y2 x3,y3 x4,y4`)
- Pixel/relative quad mode and debug preview
- Warp mode: perspective or mesh
"""

from pathlib import Path
import argparse
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import cv2


def create_default_artwork(path: Path, size=(900, 900)) -> None:
    img = Image.new("RGBA", size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((80, 80, size[0] - 80, size[1] - 80), radius=100, fill=(37, 99, 235, 235))
    draw.ellipse((180, 180, size[0] - 180, size[1] - 180), fill=(245, 158, 11, 230))
    draw.text((size[0] // 2 - 120, size[1] // 2 - 15), "MOCKUP", fill=(15, 23, 42, 255))
    img.save(path)


def create_default_mug_template(size=(1400, 1000)):
    w, h = size
    bg = Image.new("RGBA", size, (242, 244, 248, 255))
    draw = ImageDraw.Draw(bg)
    draw.rectangle((0, int(h * 0.72), w, h), fill=(226, 229, 235, 255))
    mug_rect = (380, 230, 1030, 820)
    draw.rounded_rectangle(mug_rect, radius=140, fill=(247, 247, 247, 255), outline=(210, 212, 218, 255), width=4)
    draw.rounded_rectangle((980, 340, 1190, 700), radius=110, fill=(250, 250, 250, 255), outline=(210, 212, 218, 255), width=4)
    draw.rounded_rectangle((1035, 395, 1140, 645), radius=70, fill=(242, 244, 248, 255))
    dst_quad = np.float32([[480, 340], [940, 320], [920, 730], [500, 740]])
    return bg, dst_quad


def create_layers(size: tuple[int, int], dst_quad: np.ndarray):
    w, h = size
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon([tuple(p) for p in dst_quad], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(0.8))

    shadow = Image.new("L", size, 0)
    sdraw = ImageDraw.Draw(shadow)
    qx = [p[0] for p in dst_quad]
    qy = [p[1] for p in dst_quad]
    sdraw.ellipse((min(qx) - 80, min(qy) - 60, max(qx) + 80, max(qy) + 90), fill=64)
    shadow = shadow.filter(ImageFilter.GaussianBlur(36))

    highlight = Image.new("L", size, 0)
    hdraw = ImageDraw.Draw(highlight)
    hdraw.ellipse((int(w * 0.3), int(h * 0.25), int(w * 0.43), int(h * 0.76)), fill=95)
    highlight = highlight.filter(ImageFilter.GaussianBlur(38))
    return mask, shadow, highlight


def parse_quad(quad_args: list[str] | None, default_dst_quad: np.ndarray, width: int, height: int, quad_mode: str) -> np.ndarray:
    if not quad_args:
        return default_dst_quad
    points = []
    for token in quad_args:
        x_str, y_str = token.split(",")
        x, y = float(x_str), float(y_str)
        if quad_mode == "relative":
            x, y = x * width, y * height
        points.append([x, y])
    return np.float32(points)


def bilinear_point(quad: np.ndarray, u: float, v: float) -> np.ndarray:
    p00, p10, p11, p01 = quad
    return (1-u)*(1-v)*p00 + u*(1-v)*p10 + u*v*p11 + (1-u)*v*p01


def mesh_warp_artwork(artwork: Image.Image, dst_quad: np.ndarray, out_size: tuple[int, int], mesh_cols=20, mesh_rows=16, curve=0.55) -> Image.Image:
    src_w, src_h = artwork.size
    src = np.array(artwork.convert("RGBA"))
    out = np.zeros((out_size[1], out_size[0], 4), dtype=np.uint8)

    for j in range(mesh_rows):
        v0, v1 = j / mesh_rows, (j + 1) / mesh_rows
        sy0, sy1 = int(v0 * (src_h - 1)), int(v1 * (src_h - 1))
        for i in range(mesh_cols):
            u0, u1 = i / mesh_cols, (i + 1) / mesh_cols

            def cu(u: float) -> float:
                c = math.sin((u - 0.5) * math.pi)
                return 0.5 + c * curve * 0.5

            uu0, uu1 = cu(u0), cu(u1)
            p00 = bilinear_point(dst_quad, uu0, v0)
            p10 = bilinear_point(dst_quad, uu1, v0)
            p11 = bilinear_point(dst_quad, uu1, v1)
            p01 = bilinear_point(dst_quad, uu0, v1)
            dst_cell = np.float32([p00, p10, p11, p01])

            sx0, sx1 = int(u0 * (src_w - 1)), int(u1 * (src_w - 1))
            src_cell = np.float32([[sx0, sy0], [sx1, sy0], [sx1, sy1], [sx0, sy1]])

            m = cv2.getPerspectiveTransform(src_cell, dst_cell)
            warped = cv2.warpPerspective(src, m, out_size, flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_TRANSPARENT)
            alpha = warped[:, :, 3] > 0
            out[alpha] = warped[alpha]

    return Image.fromarray(out, "RGBA")


def warp_artwork_perspective(artwork: Image.Image, dst_quad: np.ndarray, out_size: tuple[int, int]) -> Image.Image:
    src_w, src_h = artwork.size
    src_quad = np.float32([[0, 0], [src_w - 1, 0], [src_w - 1, src_h - 1], [0, src_h - 1]])
    arr = np.array(artwork.convert("RGBA"))
    matrix = cv2.getPerspectiveTransform(src_quad, dst_quad)
    warped = cv2.warpPerspective(arr, matrix, out_size, flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_TRANSPARENT)
    return Image.fromarray(warped, "RGBA")


def apply_cylindrical_shading(warped: Image.Image, dst_quad: np.ndarray, strength: float) -> Image.Image:
    arr = np.array(warped, dtype=np.float32)
    h, w = arr.shape[:2]
    min_x, max_x = int(np.min(dst_quad[:, 0])), int(np.max(dst_quad[:, 0]))
    min_x = max(0, min_x); max_x = min(w - 1, max_x)
    for x in range(min_x, max_x + 1):
        u = (x - min_x) / max(1, (max_x - min_x))
        shade = (1 - strength) + strength * math.exp(-((u - 0.5) ** 2) / 0.08)
        arr[:, x, :3] *= shade
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def blend(base: Image.Image, warped: Image.Image, mask: Image.Image, shadow: Image.Image, highlight: Image.Image) -> Image.Image:
    canvas = base.copy()
    canvas.paste(warped, (0, 0), mask)
    shadow_rgba = Image.merge("RGBA", (shadow, shadow, shadow, shadow.point(lambda v: int(v * 0.38))))
    canvas = Image.alpha_composite(canvas, shadow_rgba)
    hi = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
    hi.putalpha(highlight.point(lambda v: int(v * 0.24)))
    return Image.alpha_composite(canvas, hi)


def draw_debug_quad(base: Image.Image, quad: np.ndarray) -> Image.Image:
    img = base.copy(); d = ImageDraw.Draw(img)
    pts = [tuple(map(float, p)) for p in quad]
    d.polygon(pts, outline=(255, 32, 32, 255), width=5)
    return img


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a mockup preview with custom mug/artwork.")
    parser.add_argument("--mug", type=Path, default=None)
    parser.add_argument("--artwork", type=Path, default=Path("samples/artwork.png"))
    parser.add_argument("--out", type=Path, default=Path("output/mockup_preview.png"))
    parser.add_argument("--quad", nargs=4, default=None)
    parser.add_argument("--quad-mode", "--quad_mode", dest="quad_mode", choices=["pixels", "relative"], default="pixels")
    parser.add_argument("--warp-mode", choices=["perspective", "mesh"], default="mesh")
    parser.add_argument("--mesh-cols", type=int, default=20)
    parser.add_argument("--mesh-rows", type=int, default=16)
    parser.add_argument("--curve-strength", type=float, default=0.55)
    parser.add_argument("--shading-strength", type=float, default=0.18)
    parser.add_argument("--debug-quad-out", type=Path, default=None)
    args = parser.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.artwork.parent.mkdir(parents=True, exist_ok=True)
    if not args.artwork.exists():
        create_default_artwork(args.artwork)

    if args.mug is not None:
        base = Image.open(args.mug).convert("RGBA")
        default_quad = np.float32([[base.width * 0.34, base.height * 0.34], [base.width * 0.68, base.height * 0.33], [base.width * 0.67, base.height * 0.74], [base.width * 0.35, base.height * 0.75]])
    else:
        base, default_quad = create_default_mug_template()

    dst_quad = parse_quad(args.quad, default_quad, base.width, base.height, args.quad_mode)
    if args.debug_quad_out is not None:
        args.debug_quad_out.parent.mkdir(parents=True, exist_ok=True)
        draw_debug_quad(base, dst_quad).save(args.debug_quad_out)

    artwork = Image.open(args.artwork).convert("RGBA")
    if args.warp_mode == "mesh":
        warped = mesh_warp_artwork(artwork, dst_quad, base.size, mesh_cols=args.mesh_cols, mesh_rows=args.mesh_rows, curve=args.curve_strength)
    else:
        warped = warp_artwork_perspective(artwork, dst_quad, base.size)

    warped = apply_cylindrical_shading(warped, dst_quad, args.shading_strength)
    mask, shadow, highlight = create_layers(base.size, dst_quad)
    result = blend(base, warped, mask, shadow, highlight)
    result.save(args.out)
    print(f"Generated mockup: {args.out}")


if __name__ == "__main__":
    main()
