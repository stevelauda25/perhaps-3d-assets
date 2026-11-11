"""Cut the Bulova 96A225 (Lunar Pilot) photo maps from the official front render: the dial (hands and applied indices removed)
and the NATO strap.

    python3 -B -m pipeline.bulova_96a225_dial [review.png]
    # -> outputs/watches/bulova-96a225/dial_photo.jpg (+ .json) and strap.jpg (+ .json)

Dial map: square crop centred on the hand pivot out to the tachymeter ring's outer edge, native resolution. Masked pixels in a
subdial are copied from the same subdial radius 12, 24 ... deg away (concentric grooves); on the flange and tachymeter ring
from the same ring radius 6, 12 ... deg away; on the plain black dial a normalised blur of the clean dial around them (all of it
lies under 3D hands or indices). Prints and indices are never a copy source. Light unsharp mask, JPEG 93.
Strap map: as pipeline/tissot_t120407_dial.py. Each render row of the strap from the case edge outward, resampled to one width,
12 o'clock rows first, then 6 o'clock rows; the keepers come with it.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.tissot_t120607_dial import fill

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/bulova-96a225-trace.json"
OUT = ROOT / "outputs/watches/bulova-96a225"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_PX = 4
SHADOW_PX = (3, 3)  # the render's hands throw a faint shadow right and down
STRAP_W = 420


def hand_mask(t, shape):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    m = np.zeros(shape, np.uint8)
    for h in t["hands"].values():
        a = math.radians(h["angle_deg"])
        for dx, dy in ((0, 0), SHADOW_PX):
            for lp in h["body_mm"]:
                pts = [(px0 + dx + (x * math.cos(a) + y * math.sin(a)) * S, py0 + dy + (x * math.sin(a) - y * math.cos(a)) * S) for x, y in lp]
                cv2.fillPoly(m, [np.array(pts, np.int32)], 1)
    cv2.circle(m, (int(px0), int(py0)), int(t["hub_mm"]["disc"] * S) + 2, 1, -1)
    return cv2.dilate(m, np.ones((2 * MARGIN_PX + 1,) * 2, np.uint8)).astype(bool)


def sub_mask(t, shape, key):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    sd = t["subdials"][key]
    cx, cy = px0 + sd["centre_mm"][0] * S, py0 - sd["centre_mm"][1] * S
    a = math.radians(sd["angle_deg"])
    L, hw = sd["length_mm"] * S, sd["half_mm"] * S + MARGIN_PX
    m = np.zeros(shape, np.uint8)
    for dx, dy in ((0, 0), SHADOW_PX):
        pts = [(cx + dx + x * math.cos(a) + y * math.sin(a), cy + dy + x * math.sin(a) - y * math.cos(a)) for x, y in ((-hw, -8), (hw, -8), (hw, L + 4), (-hw, L + 4))]
        cv2.fillPoly(m, [np.array(pts, np.int32)], 1)
    cv2.circle(m, (int(cx), int(cy)), int(sd["hub_mm"] * S) + MARGIN_PX, 1, -1)
    return m.astype(bool), (cx, cy)


def index_mask(t, shape, pad_px=6):
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    ix = t["indices"]
    cx, cy = px0 + ix["centre_mm"][0] * S, py0 - ix["centre_mm"][1] * S
    m = np.zeros(shape, np.uint8)
    for v in ix["kinds"].values():
        (r0, r1), hw = [r * S for r in v["r_mm"]], v["half_mm"] * S
        for hr in v["hours"]:
            a = math.radians(hr * 30)
            pts = [(cx + x * math.cos(a) + y * math.sin(a), cy + x * math.sin(a) - y * math.cos(a))
                   for x, y in ((-hw - pad_px, r0 - pad_px), (hw + pad_px, r0 - pad_px), (hw + pad_px, r1 + pad_px), (-hw - pad_px, r1 + pad_px))]
            cv2.fillPoly(m, [np.array(pts, np.int32)], 1)
    return m.astype(bool)


def build(review=None):
    t = json.loads(TRACE.read_text())
    S, (px0, py0) = t["scale_px_per_mm"], t["origin_px"]
    px0i, py0i = int(round(px0)), int(round(py0))
    raw = cv2.imread(str(ROOT / t["source"]), cv2.IMREAD_UNCHANGED)
    al = raw[..., 3:].astype(np.float32) / 255
    img = (raw[..., :3] * al + 255 * (1 - al)).astype(np.uint8)
    rg = t["rings_mm"]
    R = int(math.ceil(rg["tach_out"] * S)) + 8
    sl = np.s_[py0i - R:py0i + R, px0i - R:px0i + R]
    shape = img.shape[:2]
    win = img[sl].copy()
    hands = hand_mask(t, shape)[sl]
    idx = index_mask(t, shape)[sl]
    hsv = cv2.cvtColor(win, cv2.COLOR_BGR2HSV).astype(int)
    prints = cv2.dilate(((hsv[..., 2] > 120) & ~hands & ~idx).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    used = {}
    subs = np.zeros(win.shape[:2], bool)
    sub_hands = np.zeros(win.shape[:2], bool)
    yy, xx = np.mgrid[0:2 * R, 0:2 * R]
    for key, sd in t["subdials"].items():
        sm, (cx, cy) = sub_mask(t, shape, key)
        sm = sm[sl]
        sub_hands |= sm
        cx, cy = cx - (px0i - R), cy - (py0i - R)
        disc = np.hypot(xx - cx, yy - cy) < 4.0 * S
        todo = (sm | hands) & disc
        used[key] = fill(win, todo, sm | hands | prints, [sg * k * 12 for k in range(1, 15) for sg in (1, -1)], (cx, cy), np.zeros(win.shape, np.float32))
        subs |= disc
    rcx, rcy = px0 + t["ring_centre_mm"][0] * S - (px0i - R), py0 - t["ring_centre_mm"][1] * S - (py0i - R)
    rr = np.hypot(xx - rcx, yy - rcy)
    ring = rr >= rg["dial_out"] * S - 2
    todo = (hands | idx) & ring
    used["rings"] = fill(win, todo, hands | idx | prints, [sg * k * 6 for k in range(1, 30) for sg in (1, -1)], (rcx, rcy), np.zeros(win.shape, np.float32))
    # where the white chrono needle crosses a white print (BULOVA, the 60 of the lower subdial), keep the photo: the 3D needle
    # lies on the same pixels, and a fill would cut the letters on both sides of it
    near = cv2.morphologyEx((prints & ~hands).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((21, 21), np.uint8)).astype(bool)
    keep = hands & near & ~idx
    plain = (hands | idx) & ~ring & ~subs & ~keep
    valid = (~cv2.dilate((hands | idx | prints).astype(np.uint8), np.ones((7, 7), np.uint8)).astype(bool) & ~ring & ~subs).astype(np.float32)
    num = cv2.GaussianBlur(win.astype(np.float32) * valid[..., None], (0, 0), 20)
    den = cv2.GaussianBlur(valid, (0, 0), 20)[..., None]
    win[plain] = np.clip((num / np.maximum(den, 1e-3))[plain], 0, 255).astype(np.uint8)
    mask = (hands | idx | sub_hands) & ~keep
    soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 1.0)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], cv2.GaussianBlur(win, (0, 0), SHARPEN[0]), -SHARPEN[1], 0)
    OUT.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(OUT / "dial_photo.jpg"), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [px0i, py0i], "centre_offset_mm": [round((px0i - px0) / S, 3), round(-(py0i - py0) / S, 3)],
            "half_size_mm": round(R / S, 3), "size_px": crop.shape[0], "masked_px": int(mask.sum()), "smooth_px": int(plain.sum()),
            "filled_from": {k: {a: b for a, b in v.items() if b} for k, v in used.items()}}
    (OUT / "dial_photo.json").write_text(json.dumps(meta, indent=1) + "\n")

    # ---- strap: rows from the case edge outward, each resampled to STRAP_W ----
    fg = raw[..., 3] > 250
    strips, rows_meta = [], []
    for sy, e_row in ((1, t["case_edge_rows"][0]), (-1, t["case_edge_rows"][1])):
        rows = range(e_row, -1, -1) if sy == 1 else range(e_row, img.shape[0])
        out = []
        for y in rows:
            xs = np.nonzero(fg[y])[0]
            if len(xs) < 10:
                break
            out.append(cv2.resize(img[y:y + 1, xs.min() + 1:xs.max()], (STRAP_W, 1), interpolation=cv2.INTER_AREA))
        strips.append(np.vstack(out))
        rows_meta.append({"first_s_mm": round(sy * (py0 - e_row) / S, 3), "rows": len(out)})
    strap = np.vstack(strips)
    cv2.imwrite(str(OUT / "strap.jpg"), strap, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    smeta = {"source": t["source"], "width_px": STRAP_W, "rows_per_mm": round(S, 4), "top": rows_meta[0], "bottom": rows_meta[1],
             "size_px": [STRAP_W, strap.shape[0]]}
    (OUT / "strap.json").write_text(json.dumps(smeta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[mask] = (0.5 * shown[mask] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2000, 1000), interpolation=cv2.INTER_AREA))
    return meta, smeta


if __name__ == "__main__":
    print(build(Path(sys.argv[1]) if len(sys.argv) > 1 else None))
