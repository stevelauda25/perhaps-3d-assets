"""Cut the dial map for the Citizen AT8300-58L (Promaster Navihawk A-T) from the official front render: the hour, minute and
chronograph hands, the counterweight and the hub removed, the applied indices blanked (they are modelled).

    python3 -B -m pipeline.citizen_at8300_dial [out.jpg] [review.png]   # default outputs/watches/citizen-at8300-58l/dial_photo.jpg

Same method as pipeline/bulova_96b258_dial.py without the print redraw (the render is sharp at 28.7 px/mm). Square map centred
on the dial centre out to the bezel's inner edge (dial, city ring and both slide rules). Each hidden pixel gets a local
lighting estimate (masked normalised blur) plus detail copied from the same radius a few degrees away: about the subdial
centre inside a subdial (concentric grooves), about the dial centre elsewhere (radial sunray). Prints, indices and the date
are never a copy source. The subdial needles stay in the map under the modelled ones. Light unsharp mask, JPEG.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.hamilton_h77616533_trace import load
from pipeline.hamilton_h82405130_dial import fill

ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "config/watches/citizen-at8300-58l-trace.json"
OUT = ROOT / "outputs/watches/citizen-at8300-58l/dial_photo.jpg"
SHARPEN = (1.2, 0.6)
JPEG_QUALITY = 93
MARGIN_PX = 8
SHADOW_PX = ((3, 3), (6, 6), (9, 9), (12, 11), (15, 13))  # the render's hands throw a soft shadow down to the right
LIGHT_SIGMA_PX = 14
SUB_RADII_PX = (132, 96, 132)  # 12, 9 and 6 o'clock subdials with their rims


def hand_mask(t, shape):
    S, (cx, cy) = t["scale_px_per_mm"], t["origin_px"]
    hx, hy = t["hand_pivot_px"]
    P = lambda q: (cx + q[0] * S, cy - q[1] * S)
    m = np.zeros(shape, np.uint8)
    for dx, dy in ((0, 0),) + SHADOW_PX:
        for name in ("hour", "minute"):
            poly = np.array([(x + dx, y + dy) for x, y in map(P, t["hands"][name]["outline_mm"])], np.int32)
            cv2.fillPoly(m, [poly], 1)
            cv2.polylines(m, [poly], True, 1, 2 * MARGIN_PX)
        for key, length, (h0, h1), tail in (("chrono", t["hands"]["chrono"]["tip_mm"], t["hands"]["chrono"]["half_mm"], t["hands"]["chrono"]["tail_mm"]),
                                             ("counter", t["counter"]["length_mm"], t["counter"]["half_mm"], 0.0)):
            a = math.radians(t["hands"]["chrono"]["angle_deg"] if key == "chrono" else t["counter"]["angle_deg"])
            u, v = (math.sin(a), -math.cos(a)), (math.cos(a), math.sin(a))
            q = lambda s, w: (hx + dx + (s * u[0] + w * v[0]) * S, hy + dy + (s * u[1] + w * v[1]) * S)
            mg = MARGIN_PX / S
            pts = [q(-tail - mg, h0 + mg), q(length + mg, h1 + mg), q(length + mg, -h1 - mg), q(-tail - mg, -h0 - mg)]
            cv2.fillPoly(m, [np.array(pts, np.int32)], 1)
        for hk in t["counter"]["hooks"]:
            a = math.radians(hk["angle_deg"])
            cv2.circle(m, (int(hx + dx + hk["r_mm"] * S * math.sin(a)), int(hy + dy - hk["r_mm"] * S * math.cos(a))), int((hk["radius_mm"] + 0.2) * S), 1, -1)
        cv2.circle(m, (int(hx + dx), int(hy + dy)), int(t["hub_radius_mm"][0] * S + MARGIN_PX), 1, -1)
    return m.astype(bool)


def index_mask(t, shape, pad_mm):
    S, (cx, cy) = t["scale_px_per_mm"], t["origin_px"]
    ix = t["indices"]
    bars = [{"centre_mm": [ix["baton"]["r_mm"] * math.sin(math.radians(30 * hr)), ix["baton"]["r_mm"] * math.cos(math.radians(30 * hr))],
             "angle_deg": 30 * hr, "half_len_mm": ix["baton"]["half_len_mm"], "half_w_mm": ix["baton"]["half_w_mm"]} for hr in ix["baton"]["hours"]]
    m = np.zeros(shape, np.uint8)
    for b in bars + ix["small"]:
        a = math.radians(b["angle_deg"])
        u, v = (math.sin(a), math.cos(a)), (math.cos(a), -math.sin(a))
        L, W = b["half_len_mm"] + pad_mm, b["half_w_mm"] + pad_mm
        x0, y0 = b["centre_mm"]
        pts = [(cx + (x0 + su * L * u[0] + sv * W * v[0]) * S, cy - (y0 + su * L * u[1] + sv * W * v[1]) * S) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        cv2.fillPoly(m, [np.array(pts, np.int32)], 1)
    return m.astype(bool)


def build(out=OUT, review=None):
    t = json.loads(TRACE.read_text())
    S, (cx, cy) = t["scale_px_per_mm"], t["origin_px"]
    img = load(ROOT / t["source"])
    shape = img.shape[:2]
    R = int(math.ceil(t["rings_mm"]["bezel_in"] * S))
    x0, y0 = int(round(cx)) - R, int(round(cy)) - R
    sl = np.s_[y0:y0 + 2 * R, x0:x0 + 2 * R]
    c = (cx - x0, cy - y0)
    win = img[sl].copy()
    mask = hand_mask(t, shape)[sl]
    idx = index_mask(t, shape, 0.15)[sl]
    todo_all = mask | idx
    g = cv2.cvtColor(win, cv2.COLOR_BGR2GRAY).astype(np.float32)
    hsv = cv2.cvtColor(win, cv2.COLOR_BGR2HSV)
    prints = cv2.dilate(((g > 150) | ((hsv[..., 1] > 120) & (hsv[..., 2] > 150) & (hsv[..., 0] < 10))).astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    d = t["date_mm"]
    date = np.zeros(win.shape[:2], bool)
    date[int(cy - d[1] * S) - y0 - 4:int(cy - d[3] * S) - y0 + 4, int(cx + d[0] * S) - x0 - 4:int(cx + d[2] * S) - x0 + 4] = True
    feats = (prints & ~todo_all) | date | index_mask(t, shape, 0.3)[sl]
    yy, xx = np.mgrid[0:win.shape[0], 0:win.shape[1]]
    clean = (~todo_all & ~feats).astype(np.float32)
    low = cv2.GaussianBlur(win.astype(np.float32) * clean[..., None], (0, 0), LIGHT_SIGMA_PX) / \
        np.maximum(cv2.GaussianBlur(clean, (0, 0), LIGHT_SIGMA_PX)[..., None], 1e-3)
    in_sub = np.zeros(win.shape[:2], bool)
    used = {}
    for k, ((sx, sy), rad) in enumerate(zip(t["subs"]["centres_mm"], SUB_RADII_PX)):
        scx, scy = c[0] + sx * S, c[1] - sy * S
        disc = np.hypot(xx - scx, yy - scy) < rad
        in_sub |= disc
        todo = todo_all & disc
        moves = [(sg * j * 6, 1.0) for j in range(1, 30) for sg in (1, -1)]
        used.update({"sub%d %s" % (k, a): b for a, b in fill(win, todo, todo_all | feats | ~disc, low, moves, (scx, scy)).items()})
        win[todo] = np.clip(low[todo], 0, 255).astype(np.uint8)
    todo = todo_all & ~in_sub
    moves = [(sg * j * 3, 1.0) for j in range(1, 60) for sg in (1, -1)]
    used.update(fill(win, todo, todo_all | feats | in_sub, low, moves, c))
    left = int(todo.sum())
    win[todo] = np.clip(low[todo], 0, 255).astype(np.uint8)
    # match the filled zones to the dial right next to them
    ring = (cv2.dilate(todo_all.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool) & ~todo_all & ~feats).astype(np.float32)
    # (wide hands: a sigma of 30 px reaches their middle; where the ring is still too far the shift fades out)
    mloc = lambda a, w: cv2.GaussianBlur(a * w[..., None], (0, 0), 30) / np.maximum(cv2.GaussianBlur(w, (0, 0), 30)[..., None], 1e-3)
    reach = np.clip(cv2.GaussianBlur(ring, (0, 0), 30) / 0.05, 0, 1)[..., None]
    shift = reach * (mloc(img[sl].astype(np.float32), ring) - mloc(win.astype(np.float32), todo_all.astype(np.float32)))
    win[todo_all] = np.clip(win[todo_all] + shift[todo_all], 0, 255).astype(np.uint8)
    soft = cv2.GaussianBlur(todo_all.astype(np.float32), (0, 0), 1.2)[..., None]
    win = (soft * win + (1 - soft) * img[sl]).astype(np.uint8)
    crop = cv2.addWeighted(win, 1 + SHARPEN[1], cv2.GaussianBlur(win, (0, 0), SHARPEN[0]), -SHARPEN[1], 0)
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), crop, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
    meta = {"source": t["source"], "centre_px": [x0 + R, y0 + R], "centre_offset_px": [round(cx - x0 - R, 2), round(cy - y0 - R, 2)],
            "half_size_mm": round(R / S, 3), "size_px": crop.shape[0], "masked_px": int(todo_all.sum()), "lighting_only_px": left,
            "filled_from": {k: v for k, v in used.items() if v}}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    if review:
        shown = img[sl].copy()
        shown[todo_all] = (0.5 * shown[todo_all] + [0, 0, 127]).astype(np.uint8)
        cv2.imwrite(str(review), cv2.resize(np.hstack([shown, crop]), (2000, 1000), interpolation=cv2.INTER_AREA))
    return meta


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    m = build(dest, Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    print({k: m[k] for k in ("size_px", "masked_px", "lighting_only_px", "centre_offset_px")}, "->", dest)
