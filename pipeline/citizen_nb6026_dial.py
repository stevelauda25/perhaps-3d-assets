"""Cut the Citizen NB6026-56L (Promaster Fujitsubo) dial map from the official front render, hands and applied indices
removed.

    python3 -B -m pipeline.citizen_nb6026_dial [review.png]   # -> outputs/watches/citizen-nb6026-56l/dial_photo.jpg (+ .json)

Same method as pipeline/citizen_bj7150_dial.py: hands and index footprints rasterised from the trace, each masked pixel copied
from the same radius some degrees away (the blue dial's lighting and the minute track are radial), never from a print, a hand
or an index; what no rotation can fill (the hub) is inpainted under the 3D hub. Light unsharp mask, JPEG 93.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.tissot_t120607_dial import fill

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/citizen-nb6026-56l-trace.json"
OUT = ROOT / "outputs/watches/citizen-nb6026-56l"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_PX = 5
SHADOW_PX = (3, 3)  # the render's hands throw a faint shadow right and down
TRACK_PX = 380  # inner edge of the printed minute track about the pivot


def hand_mask(t, shape, only=None):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    for name, h in t["hands"].items():
        if only and name != only:
            continue
        a = math.radians(h["angle_deg"])
        loc = lambda x, y, dx, dy: (px0 + dx + (x * math.cos(a) + y * math.sin(a)) * S, py0 + dy + (x * math.sin(a) - y * math.cos(a)) * S)
        for dx, dy in ((0, 0), SHADOW_PX):
            for lp in h["body_mm"]:
                cv2.fillPoly(m, [np.array([loc(x, y, dx, dy) for x, y in lp], np.int32)], 1)
            for al_, rad in h["circles_mm"]:
                cv2.circle(m, tuple(int(v) for v in loc(0, al_, dx, dy)), int(rad * S), 1, -1)
    m = cv2.dilate(m, np.ones((2 * MARGIN_PX + 1,) * 2, np.uint8))
    if not only:
        cv2.circle(m, (px0, py0), int(t["hub_mm"]["disc"] * S) + MARGIN_PX + 2, 1, -1)
    return m.astype(bool)


def index_mask(t, shape, pad_px=15):  # the frames cast a lit edge and a shadow past their outline
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    ix = t["indices"]
    cx, cy = ix["centre_mm"]
    k = ix["frame_mm"] * S + pad_px
    m = np.zeros(shape, np.uint8)
    for v in ix["kinds"].values():
        (r0, r1), hw = [r * S for r in v["r_mm"]], v["half_mm"] * S
        for hr in v["hours"]:
            a = math.radians(hr * 30)
            pts = [(px0 + cx * S + x * math.cos(a) + y * math.sin(a), py0 - cy * S + x * math.sin(a) - y * math.cos(a))
                   for x, y in ((-hw - k, r0 - k), (hw + k, r0 - k), (hw + k, r1 + k), (-hw - k, r1 + k))]
            cv2.fillPoly(m, [np.array(pts, np.int32)], 1)
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
    mask = hand_mask(t, img.shape[:2])[sl] | index_mask(t, img.shape[:2])[sl]
    hsv = cv2.cvtColor(win, cv2.COLOR_BGR2HSV).astype(int)
    prints = (hsv[..., 1] < 90) & (hsv[..., 2] > 140)
    # where the seconds needle crosses a white print (DIVER'S 200m), keep the photo: the 3D needle lies on it, and a wider fill
    # would cut the numeral on both sides of the needle
    sec = hand_mask(t, img.shape[:2], "seconds")[sl]
    near = cv2.morphologyEx((prints & ~sec).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8)).astype(bool)
    keep = sec & near
    keep &= ~hand_mask(t, img.shape[:2], "hour")[sl] & ~hand_mask(t, img.shape[:2], "minute")[sl] & ~index_mask(t, img.shape[:2])[sl]
    mask &= ~keep
    prints = cv2.dilate(prints.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool) & ~mask
    # inside the minute track the blue gradient is lit from the upper left (not radial): a smooth inpaint, all of it under
    # 3D hands and indices; the minute track and the rim are copied from the same radius 6, 12 ... deg away
    yy, xx = np.mgrid[-R:R, -R:R]
    track = np.hypot(xx, yy) >= TRACK_PX
    todo = mask & track
    used = fill(win, todo, mask | prints, [sg * k * 6 for k in range(1, 40) for sg in (1, -1)], (R, R), np.zeros(win.shape, np.float32))
    todo |= mask & ~track
    # normalised blur of the clean dial (no hand, index, print or index edge as a source): the gradient without any grey
    valid = (~cv2.dilate((mask | prints).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool) & ~track).astype(np.float32)
    num = cv2.GaussianBlur(win.astype(np.float32) * valid[..., None], (0, 0), 28)
    den = cv2.GaussianBlur(valid, (0, 0), 28)[..., None]
    smooth = num / np.maximum(den, 1e-3)
    win[todo] = np.clip(smooth[todo], 0, 255).astype(np.uint8)
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
