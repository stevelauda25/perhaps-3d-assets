"""Zoom sheets for designer review (host-side, OpenCV): the same crops of the reference photo and the render at 3x.

    python3 -B -m pipeline.zoom_check [baseline_dir ...]     # default: every references/*/baseline with baseline_vs_reference.png

Reads `baseline_vs_reference.png` (reference left, render right, same pixel frame), finds the watch head in the render (non-white pixels),
and cuts three crops at the native pixel size, upscaled 3x: upper dial (logo / 12 o'clock print), hands and hub, lower dial (small text / 6).
Writes `zoom_check.jpg` next to it: one row per crop, reference | render. It only prepares material for a human to look at small details
(sharpness, readable print, edge artifacts); it makes no pass/fail decision and computes no score.
"""
import glob
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SCALE = 3


def sheet(base):
    im = cv2.imread(str(base / "baseline_vs_reference.png"))
    h, w = im.shape[:2]
    ref, ren = im[:, : w // 2], im[:, w // 2:]
    ys, xs = np.nonzero((255 - ren).max(axis=2) > 24)
    if len(xs) == 0:
        return False
    x0, x1 = np.percentile(xs, [1, 99])
    y0, y1 = np.percentile(ys, [1, 99])
    cx, cy, W = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0)
    half = int(0.19 * W)
    rows = []
    for dy in (-0.16, 0.0, 0.2):
        py = int(cy + dy * W)
        ys_, xs_ = max(0, py - half), max(0, int(cx) - half)
        crop = lambda a: a[ys_: ys_ + 2 * half, xs_: xs_ + 2 * half]
        pair = [cv2.resize(crop(a), None, fx=SCALE, fy=SCALE, interpolation=cv2.INTER_CUBIC) for a in (ref, ren)]
        rows.append(np.hstack(pair))
    out = np.vstack(rows)
    cv2.putText(out, "reference", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.putText(out, "render (3x crops)", (out.shape[1] // 2 + 10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    cv2.imwrite(str(base / "zoom_check.jpg"), out, [cv2.IMWRITE_JPEG_QUALITY, 78])
    return True


if __name__ == "__main__":
    dirs = [Path(a) for a in sys.argv[1:]] or [Path(p).parent for p in sorted(glob.glob(str(ROOT / "references/*/baseline/baseline_vs_reference.png")))]
    ok = [d for d in dirs if sheet(d)]
    print("%d zoom sheets written" % len(ok))
