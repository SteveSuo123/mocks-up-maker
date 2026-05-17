"""Dependency-free minimal mug mockup generator (PPM output).

Usage:
  python minimal_mockup_poc_stdlib.py --out output/mockup_preview.ppm
"""
from __future__ import annotations
import argparse
from pathlib import Path

W, H = 1200, 800


def clamp(v, lo=0, hi=255):
    return lo if v < lo else hi if v > hi else int(v)


def make_canvas():
    return [[(242, 244, 248) for _ in range(W)] for _ in range(H)]


def draw_rect(img, x0, y0, x1, y1, color):
    for y in range(max(0, y0), min(H, y1)):
        row = img[y]
        for x in range(max(0, x0), min(W, x1)):
            row[x] = color


def draw_ellipse(img, cx, cy, rx, ry, color, alpha=1.0):
    for y in range(max(0, cy - ry), min(H, cy + ry + 1)):
        dy = (y - cy) / ry
        for x in range(max(0, cx - rx), min(W, cx + rx + 1)):
            dx = (x - cx) / rx
            if dx * dx + dy * dy <= 1.0:
                r, g, b = img[y][x]
                nr = clamp(r * (1 - alpha) + color[0] * alpha)
                ng = clamp(g * (1 - alpha) + color[1] * alpha)
                nb = clamp(b * (1 - alpha) + color[2] * alpha)
                img[y][x] = (nr, ng, nb)


def make_artwork(size=600):
    art = [[(255, 255, 255) for _ in range(size)] for _ in range(size)]
    for y in range(size):
        for x in range(size):
            # blue gradient base
            art[y][x] = (40 + x // 10, 90 + y // 14, 200)
    # orange circle
    cx = cy = size // 2
    r = size // 3
    for y in range(size):
        for x in range(size):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                art[y][x] = (245, 158, 11)
    return art


def map_art_to_quad(img, art, quad):
    # simple bilinear map onto convex quad split into two triangles
    (x0, y0), (x1, y1), (x2, y2), (x3, y3) = quad
    minx = max(0, min(p[0] for p in quad)); maxx = min(W - 1, max(p[0] for p in quad))
    miny = max(0, min(p[1] for p in quad)); maxy = min(H - 1, max(p[1] for p in quad))

    def inside(px, py):
        def s(a, b, c):
            return (a[0]-c[0])*(b[1]-c[1]) - (b[0]-c[0])*(a[1]-c[1])
        p=(px,py)
        b1 = s(p, (x0,y0), (x1,y1)) < 0
        b2 = s(p, (x1,y1), (x2,y2)) < 0
        b3 = s(p, (x2,y2), (x3,y3)) < 0
        b4 = s(p, (x3,y3), (x0,y0)) < 0
        return (b1==b2==b3==b4)

    a_size = len(art)
    for y in range(miny, maxy + 1):
        for x in range(minx, maxx + 1):
            if not inside(x, y):
                continue
            # normalize with rough bilinear coordinates
            u = (x - minx) / max(1, (maxx - minx))
            v = (y - miny) / max(1, (maxy - miny))
            ax = min(a_size - 1, int(u * (a_size - 1)))
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
    draw_rect(img, 0, int(H*0.7), W, H, (228, 232, 238))

    # mug body
    draw_ellipse(img, 620, 410, 250, 290, (247, 247, 247), 1.0)
    draw_ellipse(img, 620, 395, 220, 250, (252, 252, 252), 1.0)
    # handle
    draw_ellipse(img, 865, 430, 95, 145, (249, 249, 249), 1.0)
    draw_ellipse(img, 865, 430, 52, 92, (242, 244, 248), 1.0)

    artwork = make_artwork(600)
    quad = [(470, 280), (770, 270), (790, 590), (485, 600)]
    map_art_to_quad(img, artwork, quad)

    # highlights and shadows
    draw_ellipse(img, 530, 430, 65, 210, (255, 255, 255), 0.25)
    draw_ellipse(img, 640, 450, 260, 300, (90, 100, 120), 0.07)
    draw_ellipse(img, 625, 705, 230, 55, (70, 80, 95), 0.22)

    write_ppm(args.out, img)
    print(f'Generated mockup: {args.out}')


if __name__ == '__main__':
    main()
