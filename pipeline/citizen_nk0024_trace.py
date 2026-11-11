"""Measure the Citizen NK0024-54X (Tsuyosa 60 automatic, 40 mm, green patterned dial, gold-tone bezel, two-tone Jubilee-style
bracelet) front photo (960 x 1769) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.citizen_nk0024_trace [out.json] [overlay.png]   # default config/watches/citizen-nk0024-54x-trace.json

Same method as pipeline/tissot_t120410_trace.py. Anchor: 40 mm case width (Citizen listing), the widest steel row at 3 and 9.
Origin = the dial centre (centre of the 3 deg dial pattern and of the index ring); the hand stack sits 0.25 mm above it in
the photo (the photo is taken slightly from below), so the hands are measured about their own pivot and placed at the
origin. mm, x right, y toward 12. Indices are found by threshold (white lume in a thin gold frame), one rectangle each;
the hands, date window, cyclops, crown and bracelet columns come from gridded crops and profiles (MANUAL_PX, about +-1 px =
+-0.05 mm). The dial pattern, its prints and the printed minute track stay in the dial map.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/citizen-nk0024-54x/front_960x1769.jpg"
OUT = ROOT / "config/watches/citizen-nk0024-54x-trace.json"
CASE_MM = 40.0  # Citizen listing: case width
LISTED = {"case_mm": 40.0, "thickness_mm": 10.9}

MANUAL_PX = {
    "dial_centre": [454.5, 861.0],  # best 3 and 6 deg rotation match of the dial pattern; matches the index ring
    "hand_pivot": [453.0, 856.0],
    # gold batons with lume, square ends; short stub tails
    "hour_hand": {"angle_deg": 302.4, "tip": 193, "half": 10.5, "lume": [92, 184, 6.5], "tail": [48, 11.5]},
    "minute_hand": {"angle_deg": 42.8, "tip": 280, "half": 10, "lume": [118, 272, 6], "tail": [45, 12]},
    # gold needle; thin counterweight tail
    "seconds_hand": {"angle_deg": 238.4, "tip": 300, "half": 1.5, "tail": [73, 2.5]},
    "hub_radius_px": [13.5, 6],  # gold boss, cap
    "frame_px": 3,  # thin gold frame round each index's lume
    "date_window": [597, 820, 700, 892],  # white date (17) seen through the cyclops, kept in the dial map
    "cyclops": [594, 805, 706, 902],
    "logo": [370, 690, 540, 728],  # CITIZEN (printed)
    "print_automatic": [370, 1000, 540, 1030],
    "crown": {"angle_deg": 125.0, "r": [392, 449], "radius": 51, "teeth": 22},
    "rings_px": {"dial_out": 318, "rehaut_out": 335, "bezel_in": 338},  # about the dial centre (radial profiles)
    # bracelet: steel outer links, gold semi and centre links (Jubilee style), joints from vertical brightness dips
    "bracelet_joints_y": {"outer": [389, 311, 230, 155], "semi": [373, 292, 211], "centre": [412, 330, 252]},
    "bracelet_gold_half_px": 90,
    "bracelet_centre_half_px": 28,
    "end_link_x_px": [240, 670],
}
ARTEFACTS = ["the photo is 960 x 1769 at about 19.9 px/mm: edges are +-1 px (+-0.05 mm)",
             "the hand stack shows 0.25 mm above the dial centre (parallax); the hands are placed at the origin",
             "the top bracelet end turns slightly right in the photo; joints are read on the top end where the links are flat",
             "the seconds tip disappears into the 8 o'clock index; its length is the minute-track radius"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(float)
    tot = im.astype(int).sum(2)
    fg = (765 - tot) > 15
    h, w = tot.shape
    M = MANUAL_PX
    px0, py0 = M["dial_centre"]
    hx, hy = M["hand_pivot"]

    # scale: widest steel row near the centre (the crown at 4 is below these rows)
    rows = range(int(py0) - 40, int(py0) + 20)
    widths = [(np.nonzero(fg[y])[0].max() - np.nonzero(fg[y])[0].min() + 1, y) for y in rows]
    case_w, case_row = max(widths)
    S = case_w / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    f = lambda v: round(v / S, 3)
    xs_row = np.nonzero(fg[case_row])[0]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0], "hand_pivot_px": [hx, hy],
           "anchor": f"case width = {CASE_MM} mm (listing), widest row y {case_row} px",
           "case_row_mm": {"y": mm((0, case_row))[1], "left": mm((xs_row.min(), 0))[0], "right": mm((xs_row.max() + 1, 0))[0]}}

    # gold bezel outer edge: gold (hue < 40, saturated) meets the brushed steel case
    gold = (hsv[..., 0] < 40) & (hsv[..., 1] > 35) & (hsv[..., 2] > 80)
    pts = []
    for a in np.arange(0, 360, 1.0):
        if 105 < a < 145:  # crown
            continue
        rs = np.arange(355, 395, 0.5)
        xs = (px0 + rs * np.sin(np.radians(a))).astype(int)
        ys = (py0 - rs * np.cos(np.radians(a))).astype(int)
        g = gold[ys, xs]
        k = next((i for i in range(1, len(rs)) if g[i - 1] and not g[i]), None)
        if k:
            pts.append((xs[k], ys[k]))
    pts = np.array(pts, float)
    keep = np.ones(len(pts), bool)
    for _ in range(6):
        bcx, bcy, br = fit_circle(pts[keep])
        d = np.abs(np.hypot(pts[:, 0] - bcx, pts[:, 1] - bcy) - br)
        keep = d < max(1.5, 2 * np.percentile(d[keep], 60))
    rg = dict(M["rings_px"], bezel_out=round(float(br), 1))
    out["bezel_offset_mm"] = mm((bcx, bcy))
    out["rings_mm"] = {k: f(v) for k, v in rg.items()}
    out["bezel_edge_fit"] = {"centre_px": [round(float(bcx), 1), round(float(bcy), 1)], "points": int(keep.sum()), "of": len(pts)}

    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() + 1 - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    # the case tapers into the bracelet: the tip is where the outline comes within 0.6 mm of the bracelet width past it
    tips = [next(y for y in np.arange(18, 26, 0.25) if width[round(sy * y, 2)] < width[round(sy * 24.0, 2)] + 0.6) for sy in (1, -1)]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    out["bracelet_width_mm"] = {f"{y:+.0f}": round(width[y], 2) for y in (24, 28, -24, -28) if y in width}
    out["checks"] = {"case_to_case_mm": round(sum(tips), 2), "end_link_width_mm": f(M["end_link_x_px"][1] - M["end_link_x_px"][0]),
                     "listed": LISTED}

    # applied indices: white lume (thin gold frame) by threshold, one rotated rectangle each
    lum = ((hsv[..., 1] < 55) & (hsv[..., 2] > 195)).astype(np.uint8)
    yy, xx = np.mgrid[0:h, 0:w]
    rp = np.hypot(xx - px0, yy - py0)
    lum[(rp < 195) | (rp > 288)] = 0
    n, lab, st, cen = cv2.connectedComponentsWithStats(lum)
    bars = []
    for i in range(1, n):
        if st[i, 4] < 150:
            continue
        ys_, xs_ = np.nonzero(lab == i)
        (cx, cy), (bw, bh), ang = cv2.minAreaRect(np.column_stack([xs_, ys_]).astype(np.float32))
        x_mm, y_mm = mm((cx, cy))
        radial = math.degrees(math.atan2(x_mm, y_mm)) % 360
        long_, short = max(bw, bh), min(bw, bh)
        bars.append({"centre_mm": [x_mm, y_mm], "angle_deg": round(radial, 2), "half_len_mm": f(long_ / 2), "half_w_mm": f(short / 2), "area_px": int(st[i, 4])})
    # keep the hour positions (pairs sit 4 deg either side of 12 and 6); drop the date at 3 and lume on the hands
    off = lambda b: abs((b["angle_deg"] + 15) % 30 - 15)
    bars = sorted((b for b in bars if (off(b) < 2 or 3 < off(b) < 6) and abs(b["angle_deg"] - 90) > 5), key=lambda b: b["angle_deg"])
    assert len(bars) == 13, [b["angle_deg"] for b in bars]  # 1 2 4 5 7 8 9 10 11 and the pairs at 12 and 6
    out["indices"] = {"bars": bars, "frame_mm": f(M["frame_px"]),
                      "layout": "applied gold-framed lume bars; pairs at 12 and 6, date with cyclops at 3"}

    hands = {}
    for name in ("hour_hand", "minute_hand", "seconds_hand"):
        hands[name.split("_")[0]] = {k: (v if k == "angle_deg" else ([f(x) for x in v] if isinstance(v, list) else f(v))) for k, v in M[name].items()}
    out["hands"] = hands
    out["hub_radius_mm"] = [f(v) for v in M["hub_radius_px"]]
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [f(b[2] - b[0]), f(b[3] - b[1])], "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k in ("date_window", "cyclops", "logo", "print_automatic"):
        out[k] = box(M[k])
    c = M["crown"]
    out["crown"] = {"angle_deg": c["angle_deg"], "r_mm": [f(v) for v in c["r"]], "radius_mm": f(c["radius"]), "teeth": c["teeth"]}

    j = M["bracelet_joints_y"]
    diffs = lambda v: [abs(a - b) for a, b in zip(v[1:], v[:-1])]
    pitch = f(float(np.mean(sum((diffs(v) for v in j.values()), []))))
    out["bracelet"] = {"pitch_mm": pitch, "first_joint_mm": {k: f(abs(v[0] - py0)) for k, v in j.items()},
                       "gold_half_mm": f(M["bracelet_gold_half_px"]), "centre_half_mm": f(M["bracelet_centre_half_px"]),
                       "end_link_half_mm": f((M["end_link_x_px"][1] - M["end_link_x_px"][0]) / 2)}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = im.copy() // 2 + 60
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for k_, rk in rg.items():
            cv2.circle(ov, (int(bcx), int(bcy)) if k_ == "bezel_out" else (int(px0), int(py0)), int(rk), (0, 0, 255), 1)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 1, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 1, (0, 255, 0), -1)
        for hd in (M["hour_hand"], M["minute_hand"], M["seconds_hand"]):
            t = math.radians(hd["angle_deg"])
            cv2.line(ov, (int(hx), int(hy)), (int(hx + hd["tip"] * math.sin(t)), int(hy - hd["tip"] * math.cos(t))), (0, 255, 255), 1)
        for b in bars:
            a = math.radians(b["angle_deg"])
            u, v = (math.sin(a), math.cos(a)), (math.cos(a), -math.sin(a))
            L, W = b["half_len_mm"], b["half_w_mm"]
            cx, cy = b["centre_mm"]
            poly = [(cx + su * L * u[0] + sv * W * v[0], cy + su * L * u[1] + sv * W * v[1]) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            cv2.polylines(ov, [np.array([P(p) for p in poly], np.int32)], True, (255, 0, 255), 1)
        for k in ("date_window", "cyclops", "logo", "print_automatic"):
            b = M[k]
            cv2.rectangle(ov, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), (0, 200, 255), 1)
        a = math.radians(c["angle_deg"])
        for r in c["r"]:
            q = (px0 + r * math.sin(a), py0 - r * math.cos(a))
            cv2.circle(ov, (int(q[0]), int(q[1])), 3, (0, 200, 255), -1)
        for v in j.values():
            for y in v:
                cv2.line(ov, (250, int(y)), (680, int(y)), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case_row_mm", "bezel_offset_mm", "rings_mm", "lug_tip_mm", "bracelet_width_mm",
                                           "checks", "bracelet", "crown")}, default=float), "->", dest)
    print([(b["angle_deg"], b["half_len_mm"], b["half_w_mm"]) for b in data["indices"]["bars"]])
