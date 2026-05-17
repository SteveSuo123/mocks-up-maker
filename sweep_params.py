from __future__ import annotations

import itertools
import subprocess
from pathlib import Path

MUG = Path("samples/m.png")
ART = Path("samples/2.jpg")
OUT_DIR = Path("output/sweep")
OUT_DIR.mkdir(parents=True, exist_ok=True)

quad = ["0.33,0.34", "0.67,0.33", "0.67,0.74", "0.34,0.75"]

curve_strengths = [0.40, 0.45, 0.50]
shading_strengths = [0.10, 0.14, 0.18]
projection_strengths = [0.22, 0.28, 0.34]
occlusion_strengths = [0.30, 0.40, 0.50]
edge_fades = [0.18, 0.24]


def run_one(c: float, s: float, p: float, o: float, e: float) -> int:
    name = f"mug_c{c:.2f}_s{s:.2f}_p{p:.2f}_o{o:.2f}_e{e:.2f}.png"
    out = OUT_DIR / name
    cmd = [
        "python",
        "minimal_mockup_poc.py",
        "--mug", str(MUG),
        "--artwork", str(ART),
        "--quad-mode", "relative",
        "--quad", *quad,
        "--warp-mode", "cylindrical",
        "--curve-strength", str(c),
        "--shading-strength", str(s),
        "--projection-strength", str(p),
        "--occlusion-strength", str(o),
        "--edge-fade", str(e),
        "--out", str(out),
    ]
    print("RUN", " ".join(cmd))
    return subprocess.run(cmd).returncode


def main() -> None:
    combos = list(itertools.product(curve_strengths, shading_strengths, projection_strengths, occlusion_strengths, edge_fades))
    ok = 0
    fail = 0
    for c, s, p, o, e in combos:
        rc = run_one(c, s, p, o, e)
        if rc == 0:
            ok += 1
        else:
            fail += 1
    print(f"Done. total={len(combos)} ok={ok} fail={fail}")


if __name__ == "__main__":
    main()
