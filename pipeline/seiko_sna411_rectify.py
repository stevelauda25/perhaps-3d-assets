"""Straighten the turned SNA411P1 photo into a front view of the dial plane (no straight front photo exists).

    python3 -B -m pipeline.seiko_sna411_rectify [out.png]     # default outputs/watches/seiko-sna411p1-var-nato3/front_rectified.png

A homography maps the dial plane to a circle: the eight lume dots (hours 1 2 4 5 7 8 10 11) to one radius at their hour
angles and the hubs of the 9 and 6 subdials to a second radius, read from gridded crops (+-3 px). The hand pivot stands above
the dial and is left out (parallax). Output: dial centre at CENTRE_PX, about the photo's own scale, Lanczos resampling,
white background. Parts above or below the dial plane (bezel, case, strap) keep some parallax; the trace fits them on
their own.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "references/seiko-sna411p1-var-nato3/turned_2000x3070.png"
OUT = ROOT / "outputs/watches/seiko-sna411p1-var-nato3/front_rectified.png"
SIZE = (2300, 3200)  # w, h
CENTRE_PX = (1150, 1640)
DOT_R_PX = 455.0  # lume dot radius in the output (about the photo's own scale)
DOTS_PX = {1: (1136, 1111), 2: (1304, 1276), 4: (1314, 1735), 5: (1144, 1908),
           7: (694, 1913), 8: (532, 1747), 10: (528, 1291), 11: (688, 1124)}
SUBDIAL_HUBS_PX = {9: (590, 1515), 6: (911, 1840)}
HAND_PIVOT_PX = (898, 1513)


def homography():
    src, dst = [], []
    pts = [(p, h, 1.0) for h, p in DOTS_PX.items()] + [(p, h, None) for h, p in SUBDIAL_HUBS_PX.items()]
    # subdial radius in dot radii from a first affine pass would be circular; use the ratio the subdial hubs give
    piv = np.array(HAND_PIVOT_PX, float)
    dot_r = np.mean([np.hypot(*(np.array(p) - piv)) for p in DOTS_PX.values()])
    sub_r = np.mean([np.hypot(*(np.array(p) - piv)) for p in SUBDIAL_HUBS_PX.values()]) / dot_r
    for p, h, r in pts:
        r = DOT_R_PX * (r or sub_r)
        a = math.radians(30 * h)
        src.append(p)
        dst.append((CENTRE_PX[0] + r * math.sin(a), CENTRE_PX[1] - r * math.cos(a)))
    H, _ = cv2.findHomography(np.float32(src), np.float32(dst), 0)
    res = np.hypot(*(cv2.perspectiveTransform(np.float32(src)[None], H)[0] - np.float32(dst)).T)
    return H, res, sub_r


def build(out=OUT):
    im = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
    H, res, sub_r = homography()
    warped = cv2.warpPerspective(im, H, SIZE, flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255, 0))
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), warped)
    pivot = cv2.perspectiveTransform(np.float32([[HAND_PIVOT_PX]]), H)[0, 0]
    meta = {"source": str(SRC.relative_to(ROOT)), "homography": H.tolist(), "residual_px": [round(float(r), 1) for r in res],
            "dial_centre_px": list(CENTRE_PX), "dot_radius_px": DOT_R_PX, "subdial_radius_in_dot_radii": round(float(sub_r), 4),
            "hand_pivot_px": [round(float(v), 1) for v in pivot]}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    m = build(dest)
    print({k: m[k] for k in ("residual_px", "hand_pivot_px", "subdial_radius_in_dot_radii")}, "->", dest)
