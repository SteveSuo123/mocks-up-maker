"""Dependency-free minimal mug mockup generator (PPM output).

Usage:
  python minimal_mockup_poc_stdlib.py --out output/mockup_preview.ppm
"""
from __future__ import annotations
import argparse
from pathlib import Path
import math

W, H = 1200, 800


def clamp(v, lo=0, hi=255):
    return lo if v < lo else hi if v > hi else int(v)


def make_canvas():
    return [[(242, 244, 248) for _ in range(W)] for _ in range(H)]


def blend_px(old, new, alpha):
    r, g, b = old
    return (
        clamp(r * (1 - alpha) + new[0] * alpha),
        clamp(g * (1 - alpha) + new[1] * alpha),
        clamp(b * (1 - alpha) + new[2] * alpha),
    )


def draw_rect(img, x0, y0, x1, y1, color):
    for y in range(max(0, y0), min(H, y1)):
        row = img[y]
        for x in range(max(0, x0), min(W, x1)):
            row[x] = color


def draw_ellipse_soft(img, cx, cy, rx, ry, color, alpha=1.0, feather=0.1):
    for y in range(max(0, cy - ry - 2), min(H, cy + ry + 3)):
        dy = (y - cy) / ry
        for x in range(max(0, cx - rx - 2), min(W, cx + rx + 3)):
            dx = (x - cx) / rx
            d = dx * dx + dy * dy
            if d <= 1.0 + feather:
                if d <= 1.0:
                    a = alpha
                else:
                    t = (d - 1.0) / feather
                    a = alpha * max(0.0, 1.0 - t)
                img[y][x] = blend_px(img[y][x], color, a)


def make_artwork(size=700):
    art = [[(255, 255, 255) for _ in range(size)] for _ in range(size)]
    for y in range(size):
        for x in range(size):
            art[y][x] = (35 + x // 9, 85 + y // 12, 205)
    cx = cy = size // 2
    r = size // 3
    for y in range(size):
        for x in range(size):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                art[y][x] = (245, 158, 11)
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
            # slight cylindrical squeeze for mug realism
            centered = (u - 0.5) * 2.0
            u2 = 0.5 + math.sin(centered * math.pi / 2) * 0.5
            ax = min(a_size - 1, int(u2 * (a_size - 1)))
            ay = min(a_size - 1, int(v * (a_size - 1)))
            img[y][x] = art[ay][ax]


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
    draw_rect(img, 0, 0, W, H, (241, 244, 249))
    draw_rect(img, 0, int(H * 0.72), W, H, (227, 232, 238))

    # ground shadow
    draw_ellipse_soft(img, 620, 700, 270, 62, (66, 74, 88), alpha=0.28, feather=0.25)

    # mug body (more realistic: rounded rectangle look using layered ellipses)
    draw_ellipse_soft(img, 600, 420, 230, 285, (247, 247, 248), alpha=1.0, feather=0.08)
    draw_ellipse_soft(img, 602, 412, 208, 250, (252, 252, 252), alpha=0.98, feather=0.08)

    # rim and lip
    draw_ellipse_soft(img, 600, 177, 224, 42, (232, 234, 238), alpha=0.65, feather=0.15)
    draw_ellipse_soft(img, 600, 182, 200, 30, (249, 249, 250), alpha=0.95, feather=0.12)
    draw_ellipse_soft(img, 600, 188, 170, 20, (240, 242, 246), alpha=0.9, feather=0.12)

    # handle with depth
    draw_ellipse_soft(img, 838, 430, 102, 150, (246, 247, 248), alpha=1.0, feather=0.1)
    draw_ellipse_soft(img, 846, 430, 66, 104, (238, 241, 246), alpha=1.0, feather=0.12)
    draw_ellipse_soft(img, 803, 430, 24, 86, (230, 233, 238), alpha=0.45, feather=0.18)

    artwork = make_artwork(700)
    quad = [(430, 290), (740, 278), (756, 588), (438, 602)]
    map_art_to_quad(img, artwork, quad)

    # mug shading and specular
    draw_ellipse_soft(img, 520, 430, 68, 228, (255, 255, 255), alpha=0.23, feather=0.28)
    draw_ellipse_soft(img, 665, 438, 220, 286, (98, 108, 126), alpha=0.11, feather=0.22)
    draw_ellipse_soft(img, 580, 405, 250, 290, (255, 255, 255), alpha=0.04, feather=0.24)

    write_ppm(args.out, img)
    print(f'Generated mockup: {args.out}')


if __name__ == '__main__':
    main()
