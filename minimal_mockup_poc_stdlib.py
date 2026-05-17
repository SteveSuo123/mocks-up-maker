"""Dependency-free minimal mug mockup generator (PPM output).

Usage:
  python minimal_mockup_poc_stdlib.py --out output/mockup_preview.ppm
"""
from __future__ import annotations
import argparse
from pathlib import Path
import math
import random

W, H = 1400, 900
RNG = random.Random(7)


def clamp(v, lo=0, hi=255):
    return lo if v < lo else hi if v > hi else int(v)


def blend_px(old, new, alpha):
    r, g, b = old
    return (
        clamp(r * (1 - alpha) + new[0] * alpha),
        clamp(g * (1 - alpha) + new[1] * alpha),
        clamp(b * (1 - alpha) + new[2] * alpha),
    )


def make_canvas():
    img = [[(0, 0, 0) for _ in range(W)] for _ in range(H)]
    for y in range(H):
        t = y / (H - 1)
        bg = (clamp(248 - 12 * t), clamp(250 - 14 * t), clamp(254 - 18 * t))
        for x in range(W):
            img[y][x] = bg
    return img


def draw_soft_ellipse(img, cx, cy, rx, ry, color, alpha=1.0, feather=0.2):
    for y in range(max(0, cy - ry - 3), min(H, cy + ry + 4)):
        dy = (y - cy) / ry
        for x in range(max(0, cx - rx - 3), min(W, cx + rx + 4)):
            dx = (x - cx) / rx
            d = dx * dx + dy * dy
            if d <= 1.0 + feather:
                a = alpha if d <= 1.0 else alpha * (1.0 - (d - 1.0) / feather)
                if a > 0:
                    img[y][x] = blend_px(img[y][x], color, a)


def add_noise(img, amount=2):
    for y in range(H):
        for x in range(W):
            r, g, b = img[y][x]
            n = RNG.randint(-amount, amount)
            img[y][x] = (clamp(r + n), clamp(g + n), clamp(b + n))


def make_artwork(size=720):
    art = [[(255, 255, 255) for _ in range(size)] for _ in range(size)]
    for y in range(size):
        for x in range(size):
            t = x / (size - 1)
            art[y][x] = (clamp(38 + 40 * t), clamp(92 + 58 * (y / size)), clamp(210 - 28 * t))

    # simple badge + stripes
    cx = cy = size // 2
    r = size // 3
    for y in range(size):
        for x in range(size):
            d2 = (x - cx) ** 2 + (y - cy) ** 2
            if d2 <= r * r:
                art[y][x] = (245, 158, 11)
            elif abs((y - cy) - 0.5 * (x - cx)) < 6:
                art[y][x] = (252, 229, 171)
    return art


def point_in_quad(px, py, quad):
    def cross(ax, ay, bx, by, cx, cy):
        return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)

    sign = None
    for i in range(4):
        x1, y1 = quad[i]
        x2, y2 = quad[(i + 1) % 4]
        c = cross(x1, y1, x2, y2, px, py)
        if sign is None:
            sign = c >= 0
        elif (c >= 0) != sign:
            return False
    return True


def map_art_to_quad(img, art, quad):
    minx = max(0, min(p[0] for p in quad)); maxx = min(W - 1, max(p[0] for p in quad))
    miny = max(0, min(p[1] for p in quad)); maxy = min(H - 1, max(p[1] for p in quad))
    a_size = len(art)

    for y in range(miny, maxy + 1):
        for x in range(minx, maxx + 1):
            if not point_in_quad(x, y, quad):
                continue
            u = (x - minx) / max(1, (maxx - minx))
            v = (y - miny) / max(1, (maxy - miny))
            curve = math.sin((u - 0.5) * math.pi)
            u2 = 0.5 + curve * 0.52
            ax = min(a_size - 1, max(0, int(u2 * (a_size - 1))))
            ay = min(a_size - 1, int(v * (a_size - 1)))
            img[y][x] = art[ay][ax]


def apply_print_shading(img, quad):
    minx = max(0, min(p[0] for p in quad)); maxx = min(W - 1, max(p[0] for p in quad))
    miny = max(0, min(p[1] for p in quad)); maxy = min(H - 1, max(p[1] for p in quad))
    for y in range(miny, maxy + 1):
        for x in range(minx, maxx + 1):
            if not point_in_quad(x, y, quad):
                continue
            u = (x - minx) / max(1, (maxx - minx))
            # center brighter, edges darker like cylinder
            shade = 0.82 + 0.22 * math.exp(-((u - 0.5) ** 2) / 0.05)
            r, g, b = img[y][x]
            img[y][x] = (clamp(r * shade), clamp(g * shade), clamp(b * shade))


def write_ppm(path: Path, img):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w') as f:
        f.write(f"P3\n{W} {H}\n255\n")
        for row in img:
            f.write(' '.join(f"{r} {g} {b}" for r, g, b in row) + '\n')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, default=Path('output/mockup_preview.ppm'))
    args = p.parse_args()

    img = make_canvas()

    # desk plane
    for y in range(int(H * 0.72), H):
        t = (y - H * 0.72) / (H * 0.28)
        row_col = (clamp(230 - 8 * t), clamp(234 - 10 * t), clamp(240 - 12 * t))
        for x in range(W):
            img[y][x] = row_col

    # ground shadow
    draw_soft_ellipse(img, 680, 745, 290, 66, (60, 68, 82), alpha=0.26, feather=0.3)

    # mug silhouette
    draw_soft_ellipse(img, 660, 440, 255, 315, (246, 247, 248), alpha=1.0, feather=0.12)
    draw_soft_ellipse(img, 662, 430, 226, 270, (252, 252, 252), alpha=0.98, feather=0.1)

    # mug rim and cavity
    draw_soft_ellipse(img, 660, 188, 248, 46, (225, 229, 236), alpha=0.65, feather=0.2)
    draw_soft_ellipse(img, 660, 194, 216, 31, (250, 250, 251), alpha=0.95, feather=0.15)
    draw_soft_ellipse(img, 660, 198, 184, 21, (236, 239, 244), alpha=0.9, feather=0.14)

    # handle with depth/ambient occlusion
    draw_soft_ellipse(img, 930, 450, 118, 168, (245, 246, 247), alpha=1.0, feather=0.12)
    draw_soft_ellipse(img, 942, 450, 75, 117, (237, 240, 245), alpha=1.0, feather=0.15)
    draw_soft_ellipse(img, 890, 450, 30, 94, (224, 228, 235), alpha=0.5, feather=0.2)

    artwork = make_artwork(720)
    quad = [(470, 302), (820, 288), (842, 635), (476, 652)]
    map_art_to_quad(img, artwork, quad)
    apply_print_shading(img, quad)

    # specular + cylindrical shading on mug
    draw_soft_ellipse(img, 550, 450, 78, 250, (255, 255, 255), alpha=0.24, feather=0.35)
    draw_soft_ellipse(img, 735, 462, 248, 312, (90, 102, 120), alpha=0.11, feather=0.28)
    draw_soft_ellipse(img, 658, 428, 280, 330, (255, 255, 255), alpha=0.035, feather=0.3)

    add_noise(img, amount=2)
    write_ppm(args.out, img)
    print(f'Generated mockup: {args.out}')


if __name__ == '__main__':
    main()
