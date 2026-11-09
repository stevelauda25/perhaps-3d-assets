"""Straighten the SNXG47K1 photo (turned about 15 deg) into a front view of the dial plane.

    python3 -B -m pipeline.seiko_snxg47_rectify [out.png]     # default outputs/watches/seiko-snxg47k1/front_rectified.png

Same method as pipeline/seiko_sna411_rectify.py: a homography maps the outer ends of the eleven batons (no baton at 3) to one
radius at their hour angles, read from gridded crops (+-3 px). The only straight-on photo found (front_straight_2000x2000.jpg)
is about 20 px/mm; this one is about 57 px/mm. Parts above or below the dial plane (case, bracelet) keep some parallax; the
trace fits them on their own. Output: dial centre at CENTRE_PX, about the photo's own scale, Lanczos resampling, white background.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "references/seiko-snxg47k1/front_3000x4851.png"
OUT = ROOT / "outputs/watches/seiko-snxg47k1/front_rectified.png"
SIZE = (3000, 4600)  # w, h
CENTRE_PX = (1500, 2200)
TIP_R_PX = 900.0  # baton outer ends in the output (about the photo's own scale)
TIPS_PX = {12: (1494, 1122), 1: (1956, 1247), 2: (2300, 1602), 4: (2278, 2555), 5: (1899, 2916), 6: (1424, 3045),
           7: (948, 2896), 8: (607, 2542), 9: (517, 2065), 10: (658, 1597), 11: (1012, 1259)}
HAND_PIVOT_PX = (1433, 2041)


def homography():
    src, dst = [], []
    for h, p in TIPS_PX.items():
        a = math.radians(30 * h)
        src.append(p)
        dst.append((CENTRE_PX[0] + TIP_R_PX * math.sin(a), CENTRE_PX[1] - TIP_R_PX * math.cos(a)))
    H, _ = cv2.findHomography(np.float32(src), np.float32(dst), 0)
    res = np.hypot(*(cv2.perspectiveTransform(np.float32(src)[None], H)[0] - np.float32(dst)).T)
    return H, res


def build(out=OUT):
    im = cv2.imread(str(SRC))
    H, res = homography()
    warped = cv2.warpPerspective(im, H, SIZE, flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), warped)
    pivot = cv2.perspectiveTransform(np.float32([[HAND_PIVOT_PX]]), H)[0, 0]
    meta = {"source": str(SRC.relative_to(ROOT)), "homography": H.tolist(), "residual_px": [round(float(r), 1) for r in res],
            "dial_centre_px": list(CENTRE_PX), "tip_radius_px": TIP_R_PX, "hand_pivot_px": [round(float(v), 1) for v in pivot]}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    m = build(dest)
    print({k: m[k] for k in ("residual_px", "hand_pivot_px")}, "->", dest)
