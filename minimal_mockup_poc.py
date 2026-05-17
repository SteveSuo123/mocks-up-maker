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
    mask = mask.filter(ImageFilter.GaussianBlur(1.2))

    shadow = Image.new("L", size, 0)
    sdraw = ImageDraw.Draw(shadow)
    qx = [p[0] for p in dst_quad]
    qy = [p[1] for p in dst_quad]
    sdraw.ellipse((min(qx) - 90, min(qy) - 70, max(qx) + 90, max(qy) + 100), fill=58)
    shadow = shadow.filter(ImageFilter.GaussianBlur(42))

    highlight = Image.new("L", size, 0)
    hdraw = ImageDraw.Draw(highlight)
    hdraw.ellipse((int(w * 0.30), int(h * 0.24), int(w * 0.44), int(h * 0.78)), fill=85)
    highlight = highlight.filter(ImageFilter.GaussianBlur(42))
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




def cylindrical_prewarp_artwork(artwork: Image.Image, curve: float) -> Image.Image:
    src = np.array(artwork.convert("RGBA"))
    h, w = src.shape[:2]
    map_x = np.zeros((h, w), dtype=np.float32)
    map_y = np.zeros((h, w), dtype=np.float32)

    for x in range(w):
        u = x / max(1, (w - 1))
        centered = (u - 0.5) * 2.0
        warped_u = 0.5 + math.sin(centered * math.pi / 2.0) * (curve * 0.9)
        src_x = np.clip(warped_u * (w - 1), 0, w - 1)
        map_x[:, x] = src_x

    for y in range(h):
        map_y[y, :] = y

    warped = cv2.remap(src, map_x, map_y, interpolation=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    return Image.fromarray(warped, "RGBA")

def mesh_warp_artwork(artwork: Image.Image, dst_quad: np.ndarray, out_size: tuple[int, int], mesh_cols=20, mesh_rows=16, curve=0.55) -> Image.Image:
    src_w, src_h = artwork.size
    src = np.array(artwork.convert("RGBA"))
    out_rgb = np.zeros((out_size[1], out_size[0], 3), dtype=np.float32)
    out_a = np.zeros((out_size[1], out_size[0]), dtype=np.float32)

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
            wa = (warped[:, :, 3].astype(np.float32) / 255.0)

            # soft accumulation avoids cell-boundary seams/striping
            wa = cv2.GaussianBlur(wa, (3, 3), 0.0)
            wrgb = warped[:, :, :3].astype(np.float32)

            comp = wa * (1.0 - out_a)
            out_rgb += wrgb * comp[:, :, None]
            out_a += comp

    out_a_safe = np.clip(out_a, 1e-6, 1.0)
    final_rgb = np.clip(out_rgb / out_a_safe[:, :, None], 0, 255).astype(np.uint8)
    final_a = np.clip(out_a * 255.0, 0, 255).astype(np.uint8)
    out = np.dstack([final_rgb, final_a])
    return Image.fromarray(out, "RGBA")


def warp_artwork_perspective(artwork: Image.Image, dst_quad: np.ndarray, out_size: tuple[int, int]) -> Image.Image:
    src_w, src_h = artwork.size
    src_quad = np.float32([[0, 0], [src_w - 1, 0], [src_w - 1, src_h - 1], [0, src_h - 1]])
    arr = np.array(artwork.convert("RGBA"))
    matrix = cv2.getPerspectiveTransform(src_quad, dst_quad)
    warped = cv2.warpPerspective(arr, matrix, out_size, flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_TRANSPARENT)
    return Image.fromarray(warped, "RGBA")


def apply_cylindrical_shading(warped: Image.Image, dst_quad: np.ndarray, strength: float, edge_fade: float = 0.22) -> Image.Image:
    arr = np.array(warped, dtype=np.float32)
    h, w = arr.shape[:2]
    min_x, max_x = int(np.min(dst_quad[:, 0])), int(np.max(dst_quad[:, 0]))
    min_y, max_y = int(np.min(dst_quad[:, 1])), int(np.max(dst_quad[:, 1]))
    min_x = max(0, min_x); max_x = min(w - 1, max_x)
    min_y = max(0, min_y); max_y = min(h - 1, max_y)

    # smooth cylindrical matte: right side stronger wrap to avoid floating edge
    for x in range(min_x, max_x + 1):
        u = (x - min_x) / max(1, (max_x - min_x))
        shade = (1 - strength) + strength * math.exp(-((u - 0.5) ** 2) / 0.08)

        left_f = np.clip(u / max(1e-6, edge_fade), 0.0, 1.0)
        right_f = np.clip((1.0 - u) / max(1e-6, edge_fade * 0.65), 0.0, 1.0)
        side_alpha = min(left_f, right_f)

        for y in range(min_y, max_y + 1):
            v = (y - min_y) / max(1, (max_y - min_y))
            top = np.clip(v / 0.08, 0.0, 1.0)
            bottom = np.clip((1.0 - v) / 0.08, 0.0, 1.0)
            vertical_alpha = min(top, bottom)
            alpha_mul = side_alpha * vertical_alpha

            arr[y, x, :3] *= shade
            arr[y, x, 3] *= alpha_mul

    # slight blur on alpha to remove hard matte transitions
    arr[:, :, 3] = cv2.GaussianBlur(arr[:, :, 3], (5, 5), 0.0)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")




def apply_canvas_cylindrical_projection(warped: Image.Image, dst_quad: np.ndarray, strength: float = 0.22) -> Image.Image:
    """Project already-warped print onto canvas-space cylinder to avoid right-side floating."""
    arr = np.array(warped.convert("RGBA"))
    h, w = arr.shape[:2]
    min_x, max_x = int(np.min(dst_quad[:, 0])), int(np.max(dst_quad[:, 0]))
    min_y, max_y = int(np.min(dst_quad[:, 1])), int(np.max(dst_quad[:, 1]))
    min_x = max(0, min_x); max_x = min(w - 1, max_x)
    min_y = max(0, min_y); max_y = min(h - 1, max_y)

    roi = arr[min_y:max_y+1, min_x:max_x+1].copy()
    rh, rw = roi.shape[:2]
    map_x = np.zeros((rh, rw), dtype=np.float32)
    map_y = np.zeros((rh, rw), dtype=np.float32)

    for y in range(rh):
        map_y[y, :] = y
    for x in range(rw):
        u = x / max(1, rw - 1)
        c = (u - 0.5) * 2.0
        # compress both sides in canvas space, stronger on right to sink into mug
        bend = math.sin(c * math.pi / 2.0) * (strength * (1.0 + 0.35 * max(0.0, c)))
        src_u = 0.5 + bend * 0.5
        map_x[:, x] = np.clip(src_u * (rw - 1), 0, rw - 1)

    warped_roi = cv2.remap(roi, map_x, map_y, interpolation=cv2.INTER_CUBIC, borderMode=cv2.BORDER_TRANSPARENT)
    arr[min_y:max_y+1, min_x:max_x+1] = warped_roi
    return Image.fromarray(arr, "RGBA")


def apply_base_occlusion_alpha(warped: Image.Image, base: Image.Image, dst_quad: np.ndarray, occlusion_strength: float = 0.35) -> Image.Image:
    """Use base mug luminance to push print behind darker curvature areas (esp. right side)."""
    w_arr = np.array(warped.convert("RGBA"), dtype=np.float32)
    b_arr = np.array(base.convert("RGB"), dtype=np.float32)
    lum = (0.2126 * b_arr[:, :, 0] + 0.7152 * b_arr[:, :, 1] + 0.0722 * b_arr[:, :, 2]) / 255.0

    min_x, max_x = int(np.min(dst_quad[:, 0])), int(np.max(dst_quad[:, 0]))
    min_y, max_y = int(np.min(dst_quad[:, 1])), int(np.max(dst_quad[:, 1]))
    min_x = max(0, min_x); max_x = min(w_arr.shape[1] - 1, max_x)
    min_y = max(0, min_y); max_y = min(w_arr.shape[0] - 1, max_y)

    roi_l = lum[min_y:max_y+1, min_x:max_x+1]
    # darker = more occlusion
    occ = 1.0 - occlusion_strength * np.clip((0.58 - roi_l) / 0.58, 0.0, 1.0)
    w_arr[min_y:max_y+1, min_x:max_x+1, 3] *= occ
    w_arr[:, :, 3] = cv2.GaussianBlur(w_arr[:, :, 3], (3, 3), 0)
    return Image.fromarray(np.clip(w_arr, 0, 255).astype(np.uint8), "RGBA")

def blend(base: Image.Image, warped: Image.Image, mask: Image.Image, shadow: Image.Image, highlight: Image.Image) -> Image.Image:
    base_arr = np.array(base.convert("RGBA"), dtype=np.float32)
    w_arr = np.array(warped.convert("RGBA"), dtype=np.float32)
    m = np.array(mask, dtype=np.float32) / 255.0
    wa = (w_arr[:, :, 3] / 255.0) * m

    # preserve cup lighting: modulate print by base luminance
    lum = (0.2126 * base_arr[:, :, 0] + 0.7152 * base_arr[:, :, 1] + 0.0722 * base_arr[:, :, 2]) / 255.0
    light = 0.82 + 0.22 * lum
    pr = w_arr[:, :, :3] * light[:, :, None]

    out_rgb = base_arr[:, :, :3] * (1.0 - wa[:, :, None]) + pr * wa[:, :, None]
    out = np.dstack([np.clip(out_rgb, 0, 255), base_arr[:, :, 3]])
    canvas = Image.fromarray(out.astype(np.uint8), "RGBA")

    shadow_rgba = Image.merge("RGBA", (shadow, shadow, shadow, shadow.point(lambda v: int(v * 0.34))))
    canvas = Image.alpha_composite(canvas, shadow_rgba)
    hi = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
    hi.putalpha(highlight.point(lambda v: int(v * 0.22)))
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
    parser.add_argument("--warp-mode", choices=["perspective", "mesh", "cylindrical"], default="cylindrical")
    parser.add_argument("--mesh-cols", type=int, default=20)
    parser.add_argument("--mesh-rows", type=int, default=16)
    parser.add_argument("--curve-strength", type=float, default=0.55)
    parser.add_argument("--shading-strength", type=float, default=0.18)
    parser.add_argument("--edge-fade", type=float, default=0.22)
    parser.add_argument("--projection-strength", type=float, default=0.22)
    parser.add_argument("--occlusion-strength", type=float, default=0.35)
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
    elif args.warp_mode == "cylindrical":
        pre = cylindrical_prewarp_artwork(artwork, args.curve_strength)
        warped = warp_artwork_perspective(pre, dst_quad, base.size)
    else:
        warped = warp_artwork_perspective(artwork, dst_quad, base.size)

    warped = apply_canvas_cylindrical_projection(warped, dst_quad, args.projection_strength)
    warped = apply_cylindrical_shading(warped, dst_quad, args.shading_strength, args.edge_fade)
    warped = apply_base_occlusion_alpha(warped, base, dst_quad, args.occlusion_strength)
    mask, shadow, highlight = create_layers(base.size, dst_quad)
    result = blend(base, warped, mask, shadow, highlight)
    result.save(args.out)
    print(f"Generated mockup: {args.out}")


if __name__ == "__main__":
    main()
