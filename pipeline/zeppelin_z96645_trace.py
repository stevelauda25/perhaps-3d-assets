"""Measure the straightened Zeppelin Z96645 photo into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.zeppelin_z96645_rectify     # first: outputs/watches/zeppelin-z96645/front_rectified.png
    python3 -B -m pipeline.zeppelin_z96645_trace [out.json] [overlay.png]     # default config/watches/zeppelin-z96645-trace.json

Anchor: the case silhouette (left edge, and right edge above and below the crown) fits a circle; its diameter is 40 mm (listing).
The case top sits above the dial, so in the straightened photo it is seen about 0.5 mm left of the dial centre (parallax); the
lug outline is measured about the case circle's own centre. Check: the strap between the lugs reads about 20 mm.
mm, x right, y toward 12, origin = dial centre. The hands are black on the cream dial: at every pixel along each hand's axis the
dark run across it (largest channel below 95) gives the hand's width. Crown: same case as Z96643 (straight-on enough there).
Outlines are stored about the hand pivot seen in the photo; the build puts them on the dial centre.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "outputs/watches/zeppelin-z96645/front_rectified.png"
OUT = ROOT / "config/watches/zeppelin-z96645-trace.json"
CASE_MM = 40.0

MANUAL_PX = {
    "dial_centre": [1609, 2420],  # rectify target: hour bars on a circle of 961.7 px
    "hour_bar_radius_px": 961.7,
    "rehaut_inner_px": 1051,  # Z96643 ring radii scaled by the hour-bar radius (same dial layout)
    "bezel_inner_px": 1223,
    "case_rows": {"left": [1750, 3100], "right": [[1750, 2150], [2700, 3100]]},
    "pivot": [1599, 2412],  # hub pin as seen (raised: parallax up-left of the dial centre)
    "hub_radius_px": 88,  # black hub with gold rings
    "hour": {"tip": [1003, 2026], "half": 30, "metric": "dark"},
    "minute": {"tip": [2307, 1716], "half": 22, "metric": "dark"},
    "seconds": {"tip": [667, 2045], "half": 10, "metric": "dark"},
    "seconds_tail": {"tip": [1847, 2513], "half": 24, "metric": "dark"},
    "lug_px": {"inner_x": 950, "groove_x": 855, "rows_top": [800, 1408], "rows_bottom": [3458, 4066]},  # left lugs; x in px
}
SAME_CASE_MM = {"crown": {"angle_deg": 90.0, "radius_mm": 2.525, "collar_radius_mm": 1.6, "r_from_to_mm": [19.3, 20.011, 23.069], "teeth": 16}}
ARTEFACTS = ["day-date window, its gold frame and the dot at 3: kept in the dial map",
             "black hub and the seconds counterweight: removed from the dial map, built as parts",
             "applied gold numerals and the Zeppelin logo: kept in the dial map (flat)",
             "crystal glare at 9-10 o'clock on the minute ring: stays in the dial map"]


def metric(im, kind):
    f = im.astype(np.float32)
    if kind == "dark":
        return f.max(2), 95
    if kind == "white":
        return 255 - f.min(2), 255 - 175  # "dark" (< threshold) = bright hand
    return 255 - np.clip(f[..., 2] - f[..., 0], 0, 255) * 3, 255 - 90  # gold: red well above blue


def edge_profile(g, thr, pivot, tip, half, r0, max_gap=4):
    p, t = np.float32(pivot), np.float32(tip)
    L = float(np.hypot(*(t - p)))
    u = (t - p) / L
    n = np.float32([-u[1], u[0]])
    offs = np.arange(-half, half + 0.5, 0.5, dtype=np.float32)
    rows, gap = [], 0
    for s in np.arange(r0, L + 0.5, 1.0):
        pts = (p + u * s)[None] + offs[:, None] * n[None]
        v = cv2.remap(g, pts[:, 0][None].astype(np.float32), pts[:, 1][None].astype(np.float32), cv2.INTER_LINEAR)[0]
        dark = v < thr
        near = [k for k in range(len(offs)) if dark[k] and abs(offs[k]) <= 4]
        if not near:
            gap += 1
            if gap > max_gap and rows:
                break
            continue
        gap = 0
        k = min(near, key=lambda k: abs(offs[k]))
        a = b = k
        while a > 0 and dark[a - 1]:
            a -= 1
        while b < len(offs) - 1 and dark[b + 1]:
            b += 1
        rows.append((s, float(offs[b]) + 0.5, float(-offs[a]) + 0.5))
    s = np.array([r[0] for r in rows])
    w = np.array([(r[1] + r[2]) / 2 for r in rows])
    w = np.array([np.median(w[max(0, i - 4):i + 5]) for i in range(len(w))])
    return s, w, u, n


def hand_outline(g, thr, pivot, tip, half, r0, S, max_gap=4):
    s, w, u, n = edge_profile(g, thr, pivot, tip, half, r0, max_gap)
    L = float(s[-1]) + 0.5
    pts = [(si, wi) for si, wi in zip(s, w)]
    poly = pts + [(L + 0.5, 0.0)] + [(si, -wi) for si, wi in reversed(pts)]
    poly = cv2.approxPolyDP(np.float32(poly)[:, None], 0.35, True)[:, 0]
    out = []
    for si, wi in poly:
        x, y = u * si + n * wi
        out.append([round(float(x) / S, 3), round(float(-y) / S, 3)])
    return {"angle_deg": round(math.degrees(math.atan2(u[0], -u[1])) % 360, 2), "length_mm": round(L / S, 3), "outline_mm": out,
            "max_half_width_mm": round(float(w.max()) / S, 3)}


def circle(pts):
    p = np.float32(pts)
    A = np.c_[2 * p[:, 0], 2 * p[:, 1], np.ones(len(p))]
    fx, fy, c = np.linalg.lstsq(A, (p ** 2).sum(1), rcond=None)[0]
    return float(fx), float(fy), float(np.sqrt(c + fx ** 2 + fy ** 2))


def trace(overlay=None):
    im = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)[..., :3]
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    M = MANUAL_PX
    cx0, cy0 = M["dial_centre"]
    cr = M["case_rows"]
    left = circle([(np.nonzero(gray[y] < 235)[0].min(), y) for y in range(cr["left"][0], cr["left"][1], 25)])
    right = circle([(np.nonzero(gray[y] < 235)[0].max(), y) for a, b in cr["right"] for y in range(a, b, 25)])
    Rc = (left[2] + right[2]) / 2
    S = 2 * Rc / CASE_MM
    ccx, ccy = (left[0] + right[0]) / 2, (left[1] + right[1]) / 2
    assert abs(ccx - cx0) < 40 and abs(ccy - cy0) < 20, "case circle far from the dial centre: %.1f %.1f" % (ccx, ccy)
    out = {"source": str(SRC.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [cx0, cy0],
           "anchor": "case edge circles left r %.1f / right r %.1f px = %.0f mm diameter" % (left[2], right[2], CASE_MM),
           "case_seen_offset_mm": [round((ccx - cx0) / S, 3), round(-(ccy - cy0) / S, 3)]}
    out["rings_mm"] = {"hour_bars": round(M["hour_bar_radius_px"] / S, 3), "dial_edge": round(M["rehaut_inner_px"] / S, 3),
                       "bezel_inner": round(M["bezel_inner_px"] / S, 3), "case": CASE_MM / 2}

    # lugs: left silhouette about the case circle's centre, top and bottom rows; strap edge and groove from the crops
    lp = M["lug_px"]
    rows = {}
    for key, sgn in (("rows_top", 1), ("rows_bottom", -1)):
        for y in range(*lp[key], 4):
            xs = np.nonzero(gray[y, :int(ccx)] < 240)[0]
            if len(xs):
                rows.setdefault(round(sgn * (ccy - y) / S * 4) / 4 * sgn, []).append((ccx - xs.min()) / S)
    prof = sorted((abs(k), float(np.mean(v))) for k, v in rows.items())
    merged = {}
    for y, h in prof:
        merged.setdefault(y, []).append(h)
    prof = [(y, round(float(np.mean(h)), 3)) for y, h in sorted(merged.items())]
    tip = max(y for y, h in prof if h > (ccx - lp["inner_x"]) / S + 0.3)
    out["lug"] = {"inner_x_mm": round((ccx - lp["inner_x"]) / S, 3), "groove_x_mm": round((ccx - lp["groove_x"]) / S, 3),
                  "outer_x_mm": round(max(h for y, h in prof if 15 < y < tip), 3), "tip_mm": {"mean": tip},
                  "from_y_mm": 15.75, "outline_half_mm": [[y, h] for y, h in prof if 15.5 <= y <= tip]}
    brown = ((im[..., 2].astype(int) - im[..., 0]) > 60)
    row = int(ccy - (tip - 0.6) * S)
    xs = np.nonzero(brown[row - 3:row + 4].mean(0) > 0.5)[0]
    out["checks"] = {"strap_at_12_lug_tips_mm": round(float(xs.max() - xs.min()) / S, 2), "lug_inner_gap_mm": round(2 * out["lug"]["inner_x_mm"], 2)}

    pc = M["pivot"]
    hands = {}
    for name in ("hour", "minute", "seconds", "seconds_tail"):
        h = M[name]
        g, thr = metric(im, h["metric"])
        hands[name] = hand_outline(g, thr, pc, h["tip"], h["half"], M["hub_radius_px"] - 12, S, h.get("max_gap", 4))
    out["hands"] = {k: v for k, v in hands.items() if k != "seconds_tail"}
    out["hands"]["seconds"]["tail_mm"] = hands["seconds_tail"]["outline_mm"]
    out["central_pivot_seen_mm"] = [round((pc[0] - cx0) / S, 3), round(-(pc[1] - cy0) / S, 3)]
    out["hub_radius_mm"] = [round(M["hub_radius_px"] / S, 3), 0.3]
    out.update(SAME_CASE_MM)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = (im // 2).copy()
        P = lambda q, o: (int(round(o[0] + q[0] * S)), int(round(o[1] - q[1] * S)))
        for f in (left, right):
            cv2.circle(ov, (int(f[0]), int(f[1])), int(f[2]), (0, 255, 0), 1)
        for r in (M["hour_bar_radius_px"], M["rehaut_inner_px"], M["bezel_inner_px"]):
            cv2.circle(ov, (cx0, cy0), int(r), (255, 128, 0), 1)
        for hd in list(out["hands"].values()) + [{"outline_mm": out["hands"]["seconds"]["tail_mm"]}]:
            cv2.polylines(ov, [np.array([P(q, pc) for q in hd["outline_mm"]])], True, (0, 255, 255), 1)
        for sgn in (1, -1):
            cv2.polylines(ov, [np.array([P((-h, sgn * y), (ccx, ccy)) for y, h in out["lug"]["outline_half_mm"]])], False, (255, 0, 255), 1)
        cv2.line(ov, (0, row), (ov.shape[1], row), (255, 0, 255), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case_seen_offset_mm", "rings_mm", "checks", "crown")}, default=float),
          {k: (v["angle_deg"], v["length_mm"], v["max_half_width_mm"]) for k, v in data["hands"].items()},
          {k: v for k, v in data["lug"].items() if k != "outline_half_mm"}, "->", dest)
