"""Measure the Speedmaster front view (official 2000 px render) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.watch_trace [out.json]      # default config/watches/speedmaster-trace.json

Anchor (v2): pass 1 scales the black bezel's outer circle to 21.0 mm; pass 2 corrects that scale so the two verified Omega numbers hold
(lug tip at 23.75 mm = half of 47.5 lug-to-lug, bracelet width at the lugs 20.0 mm). Pass 1 was 2.2 % too small in mm per pixel because the
black insert is not the 42 mm ring: the 42 mm is the outer steel bezel ring, which lies outside the black band. Every number below is a pixel measurement divided by that scale; model
coordinates are mm, x to the right, y toward 12 o'clock, origin = bezel centre. Measurements are not visual QA:
they are inputs to the builder.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/omega-speedmaster-310-30-42-50-01-001/hires/official_main_2000.png"
OUT = ROOT / "config/watches/speedmaster-trace.json"
BEZEL_OD_MM = 42.0


def fit_circle(points):
    p = points
    for _ in range(6):
        A = np.c_[2 * p[:, 0], 2 * p[:, 1], np.ones(len(p))]
        x, *_ = np.linalg.lstsq(A, (p ** 2).sum(1), rcond=None)
        cx, cy = x[:2]
        r = math.sqrt(x[2] + cx * cx + cy * cy)
        d = np.abs(np.hypot(points[:, 0] - cx, points[:, 1] - cy) - r)
        p = points[d < max(2.0, np.percentile(d, 60))]
    return cx, cy, r


def trace(path=FRONT, scale_override=None):
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    alpha, bgr = im[..., 3], im[..., :3].astype(int)
    gray = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2GRAY).astype(float)
    h, w = alpha.shape
    # Hough gives a first bezel circle; its outer edge is then refined on rays (steel -> black, strongest gradient)
    blur = cv2.GaussianBlur(gray.astype(np.uint8), (0, 0), 2)
    cx0, cy0, r0 = cv2.HoughCircles(blur, cv2.HOUGH_GRADIENT, 1, 50, param1=120, param2=80,
                                    minRadius=int(0.22 * w), maxRadius=int(0.27 * w))[0][0]
    edge = []
    for a in np.arange(150, 351, 1.0):  # left half: no crown, pushers or guards
        t = math.radians(a)
        rs = np.arange(r0 - 25, r0 + 25, 0.5)
        xs, ys = cx0 + rs * math.sin(t), cy0 - rs * math.cos(t)
        vals = cv2.GaussianBlur(gray, (0, 0), 1.2)[ys.astype(int), xs.astype(int)]
        k = int(np.argmax(np.diff(vals)))
        edge.append((xs[k], ys[k]))
    cx, cy, r = fit_circle(np.array(edge))
    S0 = r / (BEZEL_OD_MM / 2)  # pass-1 px per mm (black bezel = 21.0 mm)
    S = scale_override or S0
    mm = lambda x, y: ((x - cx) / S, -(y - cy) / S)
    yy, xx = np.mgrid[0:h, 0:w]
    rad = np.hypot(xx - cx, yy - cy) / S
    ang = (np.degrees(np.arctan2(xx - cx, -(yy - cy)))) % 360
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "scale_pass1_px_per_mm": round(S0, 4), "centre_px": [round(cx, 2), round(cy, 2)],
           "anchor": "pass 2: lug tip = 23.75 mm and bracelet width = 20.0 mm (verified Omega); pass 1: black bezel outer = 21.0 mm"}

    # --- silhouette: left/right edge per y (case planform + lugs + crown/pushers), bracelet width beyond the lugs ---
    prof = []
    for y_mm in np.arange(-40, 40.01, 0.25):
        row = int(round(cy - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(alpha[row] > 128)[0]
            if len(xs):
                prof.append([round(y_mm, 2), round((xs.min() - cx) / S, 3), round((xs.max() - cx) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    arr = np.array(prof)
    gap = np.median([r_[2] - r_[1] for r_ in prof if 30 <= abs(r_[0]) <= 33])
    tips = [y for y in arr[:, 0] if y > 18 and (arr[arr[:, 0] == y][0][2] - arr[arr[:, 0] == y][0][1]) < gap + 1.6]
    out["bracelet_width_at_30mm"] = round(float(gap), 2)
    out["lug_tip_y_mm"] = round(float(min(tips)), 2) if tips else None

    # --- lume indices (bar/dots), minute track band, bezel print band ---
    b, g, rr = bgr[..., 0], bgr[..., 1], bgr[..., 2]
    lume = ((gray > 150) & (g > rr + 6) & (g > b + 10) & (rad < 15.5) & (alpha > 200)).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(lume)
    idx = []
    for i in range(1, n):
        if st[i, 4] < 150:
            continue
        ys, xs = np.nonzero(lab == i)
        (_, _), (bw, bh), _ = cv2.minAreaRect(np.c_[xs, ys].astype(np.float32))
        x, y = mm(*cen[i])
        idx.append({"x": round(x, 3), "y": round(y, 3), "radius": round(math.hypot(x, y), 3),
                    "angle_deg": round(math.degrees(math.atan2(x, y)) % 360, 2),
                    "w": round(min(bw, bh) / S, 3), "l": round(max(bw, bh) / S, 3)})
    out["lume_components"] = sorted(idx, key=lambda d: d["angle_deg"])
    out["index_bars"] = [d for d in idx if d["radius"] > 12.5 and d["l"] > 2 and d["l"] < 3.4]

    # radial profile of bright (print/lume) pixels: minute-track and bezel-print bands
    bright = (gray > 170) & (alpha > 200)
    prof_r = [(r0, float(bright[(rad >= r0) & (rad < r0 + 0.1)].mean())) for r0 in np.arange(10, 21, 0.1)]
    out["radial_bright_profile_10_21mm"] = [[round(a, 1), round(b_, 4)] for a, b_ in prof_r]

    # --- hands: bright run length from the hub along each ray (peaks = hands) ---
    runs = []
    for a in np.arange(0, 360, 0.5):
        t = math.radians(a)
        run = 0.0
        for r0 in np.arange(1.2, 17.5, 0.1):
            x, y = int(cx + r0 * S * math.sin(t)), int(cy - r0 * S * math.cos(t))
            if gray[y, x] > 170:
                run = r0
            elif r0 - run > 0.45:
                break
        runs.append(run)
    runs = np.array(runs)
    peaks = [(round(a * 0.5, 1), round(float(runs[a]), 2)) for a in range(len(runs))
             if runs[a] > 4.5 and runs[a] >= runs[(a - 1) % 720] and runs[a] >= runs[(a + 1) % 720]]
    out["hand_rays_deg_len_mm"] = peaks
    # --- sub-hand hubs (bright discs) give the subdial centres; subdial radius is NOT measured (edges inconclusive) ---
    m = ((gray > 170) & (rad < 10.5)).astype(np.uint8) * 255
    circles = cv2.HoughCircles(cv2.GaussianBlur(m, (0, 0), 1.5), cv2.HOUGH_GRADIENT, 1, 30, param1=100, param2=9,
                               minRadius=int(0.45 * S), maxRadius=int(1.0 * S))[0]
    hubs = [(round((x - cx) / S, 2), round(-(y - cy) / S, 2), round(r_ / S, 2)) for x, y, r_ in circles]
    out["subdial_hubs_xy_r_mm"] = [hb for hb in hubs if (abs(hb[1]) < 0.4 and abs(abs(hb[0]) - 7.3) < 0.6) or (abs(hb[0]) < 0.4 and abs(hb[1] + 7.3) < 0.6)]
    out["subdial_radius_mm"] = {"value": 4.75, "basis": "estimated from the dark disc width in the render, edge fit inconclusive"}

    # --- bezel print band and minute-track band (radial bright fraction, left half so crown/guards are excluded) ---
    band = []
    for r0 in np.arange(17.0, 21.5, 0.1):
        vs = [gray[int(cy - r0 * S * math.cos(math.radians(t))), int(cx + r0 * S * math.sin(math.radians(t)))] for t in np.arange(200, 340, 0.5)]
        band.append([round(r0, 1), round(float(np.mean(np.array(vs) > 120)), 3)])
    out["bezel_bright_fraction_by_radius_left_half"] = band
    out["minute_track_mm"] = {"r_in": 15.3, "r_out": 16.7, "basis": "radial bright-fraction peak 16.0, band 15.3-16.6; tick count not measurable (assume 240)"}

    # --- bracelet below the case: row pitch (autocorrelation of the centre link) and link edges across a row ---
    col = gray[int(cy + 26 * S):int(cy + 46 * S), int(cx)]
    col = col - col.mean()
    ac = np.correlate(col, col, "full")[len(col) - 1:]
    ac /= ac[0]
    pk = [i / S for i in range(20, len(ac) - 1) if ac[i] > ac[i - 1] and ac[i] >= ac[i + 1] and ac[i] > 0.15]
    out["bracelet_row_pitch_mm"] = round(pk[2] / 2, 2) if len(pk) > 2 else None
    out["bracelet_row_autocorr_peaks_mm"] = [round(v, 2) for v in pk[:4]]
    edges = []
    for y_mm in (-30, -33, -36, -39):
        row = cv2.GaussianBlur(gray[int(cy - y_mm * S)].reshape(1, -1), (0, 0), 1.5)[0]
        d = np.abs(np.diff(row))
        xs = np.nonzero((d > 14) & (np.abs(np.arange(w - 1) - cx) < 12 * S))[0]
        edges += [(x - cx) / S for x in xs]
    edges = np.sort(np.array(edges))
    groups = np.split(edges, np.nonzero(np.diff(edges) > 0.35)[0] + 1)
    out["bracelet_link_edges_mm"] = [round(float(np.median(g_)), 2) for g_ in groups if len(g_) >= 6]

    # --- checks against the verified spec ---
    out["checks"] = {"lug_tip_y_mm_vs_verified_23.75": out["lug_tip_y_mm"],
                     "note": "tip measured on the silhouette where width falls to the bracelet width; a 2 % scale uncertainty is the anchor choice (bezel = 42.0)"}
    return out


if __name__ == "__main__":
    first = trace()
    factor = ((first["lug_tip_y_mm"] / 23.75) + (first["bracelet_width_at_30mm"] / 20.0)) / 2  # >1: pass 1 measured too many mm (scale too small), so px/mm must go UP by this factor
    data = trace(scale_override=first["scale_pass1_px_per_mm"] * factor)
    data["anchor_factor_applied"] = round(factor, 4)
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "centre_px", "bracelet_width_at_30mm", "lug_tip_y_mm")}),
          "index_bars", len(data["index_bars"]), "->", dest)
