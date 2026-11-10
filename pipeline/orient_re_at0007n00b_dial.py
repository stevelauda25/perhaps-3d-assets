"""Cut the Orient Star RE-AT0007N00B photo map: the whole front photo, projected from the front on every part of the model.

    python3 -B -m pipeline.orient_re_at0007n00b_dial [out.jpg]   # default outputs/watches/orient-re-at0007n00b/photo.jpg

The hands stay in the map (as the Rolex Daytona builds): the raised hand plates show the same pixels from the front.
Strap rows past the lug tips are stretched to the model's strap edges (the photo's strap widens and shifts where it curls
away); rows with under half the width are past the photo's strap end. Long side capped at 2048 px, light unsharp mask, JPEG.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/orient-re-at0007n00b-trace.json"
OUT = ROOT / "outputs/watches/orient-re-at0007n00b/photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MAX_PX = 2048
DARK = 110  # black leather; the steel clasp and the white background are brighter
REACH_PX = 60  # strap search band outside the model's strap edges (keeps the clasp out)


def build(out=OUT):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    clean = img.copy()
    grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ends = {}
    for side, sy in (("top", 1), ("bottom", -1)):
        st = t["strap_mm"][side]
        x0, x1 = (int(round(px0 + x * S)) for x in st["x"])
        a, b = x0 - REACH_PX, x1 + REACH_PX
        start = int(round(py0 - sy * (st["tip_y"] + 0.3) * S))
        for row in (range(start, -1, -1) if sy > 0 else range(start, img.shape[0])):
            dark = np.nonzero(grey[row, a:b] < DARK)[0]
            if len(dark) < (x1 - x0) / 2:
                break
            seg = img[row:row + 1, a + dark.min():a + dark.max() + 1]
            clean[row, x0:x1] = cv2.resize(seg, (x1 - x0, 1), interpolation=cv2.INTER_LINEAR)[0]
            ends[side] = round(abs(py0 - row) / S - 0.2, 2)
    k = min(1.0, MAX_PX / max(clean.shape[:2]))
    if k < 1:
        clean = cv2.resize(clean, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    blur = cv2.GaussianBlur(clean, (0, 0), SHARPEN[0])
    clean = cv2.addWeighted(clean, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), clean, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    # the build maps model mm to this image: u = (px0 + x S) k / w, v = 1 - (py0 - y S) k / h
    meta = {"source": t["source"], "scale": round(k, 6), "size_px": list(clean.shape[1::-1]), "strap_end_mm": ends}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest), "->", dest)
