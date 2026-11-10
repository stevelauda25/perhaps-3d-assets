"""Straighten the Zeppelin Z86621 front photo (taken slightly off axis) into a front view of the dial plane.

    python3 -B -m pipeline.zeppelin_z86621_rectify [out.png]     # default outputs/watches/zeppelin-z86621/front_rectified.png

The inner ends of the black hour bars on the minute track go to one circle at 30 deg steps with a homography. The 3 and 9
bars are cut by crystal glare and left out. The radius keeps the photo's own scale (longest semi axis of their ellipse).
The whole photo is warped, strap included.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "references/zeppelin-z86621/front_2000x3208.png"
OUT = ROOT / "outputs/watches/zeppelin-z86621/front_rectified.png"
SIZE = (2000, 3208)
CENTRE_PX = (900, 1580)
# inner ends of the black hour bars (px in the source photo), by hour
BARS_PX = {0: (881.3, 879.0), 1: (1232.5, 959.5), 2: (1500.4, 1209.3), 4: (1510.3, 1925.3), 5: (1251.4, 2187.3),
           6: (899.3, 2277.6), 7: (552.8, 2183.8), 8: (297.6, 1932.4), 10: (289.7, 1237.7), 11: (537.9, 979.1)}


def build(out=OUT):
    im = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
    src = np.float32(list(BARS_PX.values()))
    _, axes, _ = cv2.fitEllipse(src)
    R = max(axes) / 2
    dst = np.float32([(CENTRE_PX[0] + R * math.sin(math.radians(30 * k)), CENTRE_PX[1] - R * math.cos(math.radians(30 * k))) for k in BARS_PX])
    H, _ = cv2.findHomography(src, dst, 0)
    res = np.hypot(*(cv2.perspectiveTransform(src[None], H)[0] - dst).T)
    assert res.max() < 3.5, "bar residual %.2f px" % res.max()
    warped = cv2.warpPerspective(im, H, SIZE, flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255, 0))
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), warped)
    meta = {"source": str(SRC.relative_to(ROOT)), "homography": H.tolist(), "bars_used": len(BARS_PX),
            "residual_px": {"median": round(float(np.median(res)), 2), "max": round(float(res.max()), 2)},
            "dial_centre_px": list(CENTRE_PX), "bar_inner_radius_px": round(float(R), 1)}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    m = build(dest)
    print({k: m[k] for k in ("bars_used", "residual_px", "bar_inner_radius_px")}, "->", dest)
