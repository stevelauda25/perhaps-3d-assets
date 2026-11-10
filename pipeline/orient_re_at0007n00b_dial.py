"""Cut the Orient Star RE-AT0007N00B photo map: the front photo, projected from the front on every part of the model.

    python3 -B -m pipeline.orient_re_at0007n00b_dial [out.jpg]   # default outputs/watches/orient-re-at0007n00b/photo.jpg

The hands stay in the map (as the Rolex Daytona builds): the raised hand plates show the same pixels from the front.
Strap: inside each side's strap box (lug inner edges, from the case to the tips) white background is filled from the
leather around it (the photo's strap runs at a slant); past the tips each row's leather is stretched to the box width; rows
with under half the width are past the photo's strap end. Crop: the watch width, rows to the strap's front-visible end plus a
margin; long side capped at 2048 px, light unsharp mask, JPEG.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/orient-re-at0007n00b-trace.json"
SPEC = ROOT / "config/watches/orient-re-at0007n00b.json"
OUT = ROOT / "outputs/watches/orient-re-at0007n00b/photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MAX_PX = 2048
DARK = 110  # black leather; the steel buckle and the white background are brighter
REACH_PX = 80  # strap search band outside the box edges (keeps the buckle out)
MARGIN_MM = 2.0  # rows kept past the strap's front-visible end (tip + bend radius)


def build(out=OUT):
    t = json.loads(TRACE.read_text())
    st = json.loads(SPEC.read_text())["strap"]
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    img = cv2.imread(str(ROOT / t["source"]))
    clean = img.copy()
    grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ends, rows_kept = {}, {}
    for side, sy in (("top", 1), ("bottom", -1)):
        s = t["strap_mm"][side]
        x0, x1 = (int(round(px0 + x * S)) for x in s["x"])
        tip = int(round(py0 - sy * s["tip_y"] * S))
        # between the case and the tips: white background inside the box -> leather
        y_case = int(round(py0 - sy * 12.0 * S))
        ya, yb = sorted((y_case, tip))
        box = clean[ya:yb, x0:x1]
        hole = (box.min(2) > 235).astype(np.uint8)
        if hole.any():
            clean[ya:yb, x0:x1] = cv2.inpaint(box, cv2.dilate(hole, np.ones((5, 5), np.uint8)), 7, cv2.INPAINT_TELEA)
        a, b = x0 - REACH_PX, x1 + REACH_PX
        for row in (range(tip, -1, -1) if sy > 0 else range(tip, img.shape[0])):
            dark = np.nonzero(grey[row, a:b] < DARK)[0]
            if len(dark) < (x1 - x0) / 2:
                break
            seg = img[row:row + 1, a + dark.min():a + dark.max() + 1]
            clean[row, x0:x1] = cv2.resize(seg, (x1 - x0, 1), interpolation=cv2.INTER_LINEAR)[0]
            ends[side] = round(abs(py0 - row) / S - 0.2, 2)
        rows_kept[side] = s["tip_y"] + st["bend_radius"] + MARGIN_MM
    y0 = max(0, int(py0 - rows_kept["top"] * S))
    y1 = min(img.shape[0], int(py0 + rows_kept["bottom"] * S))
    fg = np.nonzero((img[y0:y1].min(2) < 238).any(0))[0]
    x0c, x1c = max(0, fg.min() - 8), min(img.shape[1], fg.max() + 9)
    crop = clean[y0:y1, x0c:x1c]
    ends = {k: min(v, (py0 - y0) / S - 0.1 if k == "top" else (y1 - py0) / S - 0.1) for k, v in ends.items()}
    k = min(1.0, MAX_PX / max(crop.shape[:2]))
    if k < 1:
        crop = cv2.resize(crop, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
    blur = cv2.GaussianBlur(crop, (0, 0), SHARPEN[0])
    crop = cv2.addWeighted(crop, 1 + SHARPEN[1], blur, -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    # the build maps model mm to this image: u = (px0 + x S - crop_x) k / w, v = 1 - (py0 - y S - crop_y) k / h
    meta = {"source": t["source"], "crop_px": [int(x0c), int(y0)], "scale": round(k, 6), "size_px": list(crop.shape[1::-1]),
            "strap_end_mm": {kk: round(v, 2) for kk, v in ends.items()}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    print(build(dest), "->", dest)
