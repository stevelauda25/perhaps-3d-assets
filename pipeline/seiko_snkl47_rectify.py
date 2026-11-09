"""Straighten the SNKL47K1 front photo (turned slightly toward the crown: dial 2.5 % narrower than tall) into a front view
of the dial plane.

    python3 -B -m pipeline.seiko_snkl47_rectify [out.png]     # default outputs/watches/seiko-snkl47k1/front_rectified.png

Same method as pipeline/seiko_snxl72_rectify.py: a homography maps the small rings at the inner end of the eleven batons
(all hours but 3, which is the day-date) to one circle at their hour angles. Ring centres from 5 px gridded crops and circle
fits (+-3 px). The hand pivot stands above the dial and is left out. Output keeps about the photo's vertical scale, Lanczos
resampling, white background. Parts above or below the dial plane (bezel, case, bracelet) keep some parallax; the trace fits
them on their own.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "references/seiko-snkl47k1/front_2772.png"
OUT = ROOT / "outputs/watches/seiko-snkl47k1/front_rectified.png"
SIZE = (2772, 2772)  # w, h
CENTRE_PX = (1386, 1386)
DOT_R_PX = 281.0  # ring radius in the output (half the photo's 12-6 ring distance)
DOTS_PX = {12: (1368, 911), 1: (1505, 947), 2: (1610, 1047), 4: (1613, 1329), 5: (1508, 1437), 6: (1372, 1473),
           7: (1232, 1437), 8: (1130, 1335), 9: (1096, 1196), 10: (1128, 1054), 11: (1228, 949)}
HAND_PIVOT_PX = (1365, 1190)


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
