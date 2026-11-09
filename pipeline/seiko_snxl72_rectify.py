"""Straighten the SNXL72K1 front photo (turned slightly toward the crown: dial 4 % narrower than tall) into a front view of
the dial plane.

    python3 -B -m pipeline.seiko_snxl72_rectify [out.png]     # default outputs/watches/seiko-snxl72k1/front_rectified.png

Same method as pipeline/seiko_sna411_rectify.py: a homography maps the eleven lume dots on the dial edge (all hours but 3,
which sits under the day-date frame) to one circle at their hour angles. Dot centres from the low-saturation blobs (+-2 px);
8, 9 and 10 sit in shadow and come from gridded crops (+-3 px). The hand pivot stands above the dial and is left out.
Output keeps about the photo's vertical scale, Lanczos resampling, white background. Parts above or below the dial plane
(bezel, case, bracelet) keep some parallax; the trace fits them on their own.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "references/seiko-snxl72k1/front_watchnation_2000.jpg"
OUT = ROOT / "outputs/watches/seiko-snxl72k1/front_rectified.png"
SIZE = (2000, 2000)  # w, h
CENTRE_PX = (1000, 1000)
DOT_R_PX = 393.5  # lume dot radius in the output (half the photo's 12-6 dot distance)
DOTS_PX = {12: (969.8, 611.8), 1: (1162.2, 662.5), 2: (1305.6, 805.7), 4: (1299.3, 1204.1), 5: (1157.7, 1346.6),
           6: (962.5, 1395.4), 7: (774.7, 1339.4), 8: (638, 1197), 9: (588, 1000), 10: (639, 807), 11: (778.5, 666.8)}
HAND_PIVOT_PX = (962, 1002)


def homography():
    src, dst = [], []
    for h, p in DOTS_PX.items():
        a = math.radians(30 * h)
        src.append(p)
        dst.append((CENTRE_PX[0] + DOT_R_PX * math.sin(a), CENTRE_PX[1] - DOT_R_PX * math.cos(a)))
    H, _ = cv2.findHomography(np.float32(src), np.float32(dst), 0)
    res = np.hypot(*(cv2.perspectiveTransform(np.float32(src)[None], H)[0] - np.float32(dst)).T)
    return H, res


def build(out=OUT):
    im = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
    H, res = homography()
    warped = cv2.warpPerspective(im, H, SIZE, flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255, 0))
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), warped)
    pivot = cv2.perspectiveTransform(np.float32([[HAND_PIVOT_PX]]), H)[0, 0]
    meta = {"source": str(SRC.relative_to(ROOT)), "homography": H.tolist(), "residual_px": [round(float(r), 1) for r in res],
            "dial_centre_px": list(CENTRE_PX), "dot_radius_px": DOT_R_PX,
            "hand_pivot_px": [round(float(v), 1) for v in pivot]}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    m = build(dest)
    print({k: m[k] for k in ("residual_px", "hand_pivot_px")}, "->", dest)
