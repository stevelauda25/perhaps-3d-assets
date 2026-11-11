"""Cut the Citizen BJ7150-50W (Promaster Land GMT) dial map from the official front render, hands removed.

    python3 -B -m pipeline.citizen_bj7150_dial [review.png]   # -> outputs/watches/citizen-bj7150-50w/dial_photo.jpg (+ .json)

Square crop centred on the hand pivot out to the bezel's inner edge, native resolution. The hands are rasterised from the
trace's polygons (plus a margin and the faint render shadow). The textured red dial does not repeat but has no direction, so
each hand pixel is copied from the same radius a few degrees away (the lighting is radial; the flange's marks repeat every
6 deg); the printed numerals, triangle, bars, logo and the date are never a copy source. Light unsharp mask, JPEG 93.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.tissot_t120607_dial import fill

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/citizen-bj7150-50w-trace.json"
OUT = ROOT / "outputs/watches/citizen-bj7150-50w"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_PX = 5
SHADOW_PX = (3, 3)  # the render's hands throw a faint shadow right and down


def hand_mask(t, shape, only=None):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    for name, h in t["hands"].items():
        if only and name != only:
            continue
        for key, turn in (("body_mm", 0.0), ("counterweight_mm", 180.0)):
            if key not in h:
                continue
            a = math.radians(h["angle_deg"] + turn)
            for dx, dy in ((0, 0), SHADOW_PX):
                pts = [(px0 + dx + (x * math.cos(a) + y * math.sin(a)) * S, py0 + dy + (x * math.sin(a) - y * math.cos(a)) * S) for x, y in h[key]]
                cv2.fillPoly(m, [np.array(pts, np.int32)], 1)
    m = cv2.dilate(m, np.ones((2 * MARGIN_PX + 1,) * 2, np.uint8))
    if not only:
        cv2.circle(m, (px0, py0), int(t["hub_mm"]["black"] * S) + MARGIN_PX + 2, 1, -1)
    return m.astype(bool)


def build(review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    raw = cv2.imread(str(ROOT / t["source"]), cv2.IMREAD_UNCHANGED)
    al = raw[..., 3:].astype(np.float32) / 255
    img = (raw[..., :3] * al + 255 * (1 - al)).astype(np.uint8)
    R = int(math.ceil(t["rings_mm"]["dial_map"] * S))
    sl = np.s_[py0 - R:py0 + R, px0 - R:px0 + R]
    win = img[sl].copy()
    mask = hand_mask(t, img.shape[:2])[sl]
    hsv = cv2.cvtColor(win, cv2.COLOR_BGR2HSV).astype(int)
    prints = ((hsv[..., 1] < 90) & (hsv[..., 2] > 140)) | ((hsv[..., 0] > 10) & (hsv[..., 0] < 35) & (hsv[..., 1] > 120))
    # where the white seconds needle crosses a white numeral, keep the photo: the 3D needle lies on it, and a wider fill
    # would cut the numeral on both sides of the needle
    sec = hand_mask(t, img.shape[:2], "seconds")[sl]
    near = cv2.morphologyEx((prints & ~sec).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8)).astype(bool)
    keep = sec & near
    keep &= ~hand_mask(t, img.shape[:2], "hour")[sl] & ~hand_mask(t, img.shape[:2], "minute")[sl]
    mask &= ~keep
    prints = cv2.dilate(prints.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool) & ~mask
    todo = mask.copy()
    used = fill(win, todo, mask | prints, [sg * k * 6 for k in range(1, 40) for sg in (1, -1)], (R, R), np.zeros(win.shape, np.float32))
    win[todo] = cv2.inpaint(win, todo.astype(np.uint8), 7, cv2.INPAINT_TELEA)[todo]  # the hub: every source is a hand too
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.0)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], cv2.GaussianBlur(win, (0, 0), SHARPEN[0]), -SHARPEN[1], 0)
    OUT.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUT / "dial_photo.jpg"), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": crop.shape[0],
            "masked_px": int(mask.sum()), "inpainted_px": int(todo.sum()), "filled_from": {k: v for k, v in used.items() if v}}
    (OUT / "dial_photo.json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    print(build(Path(sys.argv[1]) if len(sys.argv) > 1 else None))
