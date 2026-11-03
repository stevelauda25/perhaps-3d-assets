"""Trace the three hands (outline + lume inlay) from Omega's straight-on front render into hand-local vector shapes. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.watch_hands [out.json]     # default config/watches/speedmaster-hands.json

Hands are traced inside analytic zones around their axes (angles from config/watches/speedmaster-trace.json), excluding the hub. Shapes are stored
in hand-local mm (x across the hand, y along it from the pivot, rotation clockwise from +y as in the build step), so the build can pose the hands at
any time. Where hands cross, the upper hand (chrono > minute > hour) keeps the pixels.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/omega-speedmaster-310-30-42-50-01-001/hires/official_main_2000.png"
OUT = ROOT / "config/watches/speedmaster-hands.json"
UP = 4
# name: (angle deg, length mm, tail mm, search half-width mm, hub exclusion mm)
HANDS = {"hour": (304.5, 10.6, 0.0, 1.25, 1.55), "minute": (49.0, 16.2, 0.0, 1.05, 1.55), "chrono": (222.0, 17.2, 5.6, 0.95, 0.0)}


def trace():
    t = json.loads((ROOT / "config/watches/speedmaster-trace.json").read_text())
    S, (cx, cy) = t["scale_px_per_mm"], t["centre_px"]
    im = cv2.imread(str(FRONT), cv2.IMREAD_UNCHANGED)
    bgr = im[..., :3].astype(int)
    gray = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    yy, xx = np.mgrid[0:h, 0:w]
    px, py = (xx - cx) / S, -(yy - cy) / S
    bright = gray > 150
    lume_px = (bgr[..., 1] > bgr[..., 2] + 5) & (bgr[..., 1] > bgr[..., 0] + 8) & (gray > 120)
    zones, claimed = {}, np.zeros_like(bright)
    for name in ("chrono", "minute", "hour"):  # upper hand first
        deg, length, tail, half, hub = HANDS[name]
        ux, uy = math.sin(math.radians(deg)), math.cos(math.radians(deg))
        along, x_loc = px * ux + py * uy, px * math.cos(math.radians(deg)) - py * math.sin(math.radians(deg))
        zone = (along > -tail) & (along < length) & (np.abs(x_loc) < half) & (np.hypot(px, py) > hub) & ~claimed
        m = (bright | lume_px) & zone
        m8 = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        k = 5 if name == "chrono" else 9  # opening removes thin print strokes touching the hand (numerals, ticks); the hands are thicker
        m8 = cv2.morphologyEx(m8, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        n, lab, st, _ = cv2.connectedComponentsWithStats(m8)
        keep = np.zeros_like(m8, dtype=bool)
        for i in range(1, n):
            if st[i, 4] > 300:  # the hand body, not stray specks
                keep |= lab == i
        if name == "chrono":  # thin stem + short counterweight; only the lume arrow near the tip is wider
            keep &= (np.abs(x_loc) < 0.55) | (along > 13.0)
        claimed |= cv2.dilate(keep.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        zones[name] = (keep, deg, along, x_loc)
    out = {"source": str(FRONT.relative_to(ROOT)), "scale_px_per_mm": S, "hands": {}}
    for name, (keep, deg, along, x_loc) in zones.items():
        res = {}
        for part, mask in (("body", keep), ("lume", keep & cv2.dilate(lume_px.astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & lume_px)):
            up = cv2.resize(mask.astype(np.uint8) * 255, None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR)
            up = cv2.GaussianBlur(up, (0, 0), UP * 0.5)
            cnts, hier = cv2.findContours((up > 128).astype(np.uint8) * 255, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
            shapes = []
            if hier is not None:
                for i, c in enumerate(cnts):
                    if hier[0][i][3] != -1 or cv2.contourArea(c) < 40 * UP * UP:
                        continue
                    def loc(p):
                        X, Y = p[0] / UP, p[1] / UP
                        mx, my = (X - cx) / S, -(Y - cy) / S
                        th = math.radians(deg)
                        return [round(mx * math.cos(th) - my * math.sin(th), 3), round(mx * math.sin(th) + my * math.cos(th), 3)]
                    holes, j = [], hier[0][i][2]
                    while j != -1:
                        if cv2.contourArea(cnts[j]) > 6 * UP * UP:
                            holes.append([loc(p) for p in cv2.approxPolyDP(cnts[j], 0.6, True)[:, 0, :]])
                        j = hier[0][j][0]
                    shapes.append({"outer": [loc(p) for p in cv2.approxPolyDP(c, 0.6, True)[:, 0, :]], "holes": holes})
            res[part] = shapes
        out["hands"][name] = res
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace()
    dest.write_text(json.dumps(data, separators=(",", ":")) + "\n")
    print({n: {k: (len(v), sum(len(s["outer"]) for s in v)) for k, v in h.items()} for n, h in data["hands"].items()}, dest.stat().st_size, "bytes")
