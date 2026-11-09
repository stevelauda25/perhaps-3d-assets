"""Straighten the Zeppelin Z8680M4 front photo (taken from the left, about 3/4) into a front view of the dial plane in mm.

    python3 -B -m pipeline.zeppelin_z8680m4_rectify [out.png]     # default outputs/watches/zeppelin-z8680m4/front_rectified.png

Same dial as Z7680MB2 (100 Jahre chronograph, 42 mm). A homography maps photo px on the dial plane to mm: the six visible
lume dots (1, 5, 7, 8, 10, 11 o'clock; 2 sits under the minute hand, 4 is the date) on their circle, the hand pivot and the
three sub-dial hubs at their Z7680MB2 trace positions. The output keeps about the photo's own resolution (SCALE px/mm) with
the pivot at PIVOT_OUT (residual up to 0.28 mm, at the pivot: the MB2 dot circle sits slightly off its pivot). The case, lugs and bracelet sit off the dial plane and stay skewed; only the dial and the mesh are used.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "references/zeppelin-z8680m4/front_3430x5390.png"
OUT = ROOT / "outputs/watches/zeppelin-z8680m4/front_rectified.png"
SIZE = (3600, 5800)
PIVOT_OUT = (1800, 2900)
SCALE = 75.0  # px/mm, about the photo's scale along its long axis
DOT_R_MM = 11.76  # lume dot circle on the Z7680MB2 photo (612.5 px at 52.09 px/mm)
DOTS_PX = {1: (1938.0, 1883.4), 5: (1949.4, 3382.7), 7: (1098.2, 3392.1), 8: (786.5, 3080.7), 10: (781.5, 2223.1), 11: (1088.4, 1902.5)}
# pivot and sub-dial hubs (px, gridded crops) -> mm from the Z7680MB2 trace
HUBS = [((1488, 2628), (0.0, 0.0)), ((1037, 2535), (-6.527, 1.325)), ((1983, 2520), (6.661, 1.516)), ((1512, 3131), (0.096, -6.834))]


def homography():
    src = [p for p in DOTS_PX.values()] + [h[0] for h in HUBS]
    mm = [(DOT_R_MM * math.sin(math.radians(30 * k)), DOT_R_MM * math.cos(math.radians(30 * k))) for k in DOTS_PX] + [h[1] for h in HUBS]
    dst = np.float32([(PIVOT_OUT[0] + x * SCALE, PIVOT_OUT[1] - y * SCALE) for x, y in mm])
    src = np.float32(src)
    H, _ = cv2.findHomography(src, dst, 0)
    res = np.hypot(*(cv2.perspectiveTransform(src[None], H)[0] - dst).T) / SCALE
    return H, res


def build(out=OUT):
    H, res = homography()
    assert res.max() < 0.35, "residual %.3f mm" % res.max()
    im = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
    warped = cv2.warpPerspective(im, H, SIZE, flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255, 0))
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), warped)
    meta = {"source": str(SRC.relative_to(ROOT)), "homography": H.tolist(), "points_used": len(res),
            "residual_mm": {"median": round(float(np.median(res)), 3), "max": round(float(res.max()), 3)},
            "pivot_px": list(PIVOT_OUT), "scale_px_per_mm": SCALE}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    m = build(dest)
    print({k: m[k] for k in ("points_used", "residual_mm")}, "->", dest)
