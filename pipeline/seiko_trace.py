"""Measure the Seiko 5 SNK607K1 front photo (white background, 3224 x 6212) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.seiko_trace [out.json] [overlay.png]     # default config/watches/seiko-snk607k1-trace.json

Anchor: the case outline (fitted on its left and right flanks, away from lugs and crown) is 37.0 mm, chosen by the owner;
the bracelet width next to the case is the cross-check (listings say 20 mm). Model coordinates are mm, x to the right,
y toward 12 o'clock, origin = hand pivot. The woven dial texture defeats threshold tracing of indices and hands, so those
are read from gridded crops and kept below as pixel coordinates with their basis (MANUAL_PX). Measurements are inputs to the
builder, not visual QA.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-snk607k1/front_3224x6212.png"
OUT = ROOT / "config/watches/seiko-snk607k1-trace.json"
CASE_MM = 37.0
BRACELET_MM = 20.0

# Read from gridded crops of FRONT (pixel coordinates in the full image); +-5 px.
MANUAL_PX = {
    "hand_pivot": [1620, 3100],
    "hour_hand_tip": [1145, 2800],
    "hour_hand_lume": [[1400, 2950], [1540, 3040]],
    "minute_hand_tip": [2170, 2460],
    "minute_hand_lume": [[1700, 3020], [1910, 2780]],
    "seconds_hand_tip": [2391, 3486],
    "seconds_hand_tail_end": [1305, 2975],
    "lume_dots": {"12": [1616, 2228], "1": [2060, 2341], "2": [2383, 2655], "4": [2391, 3534], "5": [2076, 3865],
                  "6": [1637, 3986], "7": [1197, 3873], "8": [866, 3558], "9": [745, 3123], "10": [850, 2671], "11": [1173, 2349]},
    "index_9_inner_outer_x": [995, 802],
    "index_12_inner_outer_y": [2478, 2276],
    "index_6_inner_outer_y": [3728, 3865],
    "daydate_frame": [1955, 3010, 2495, 3187],
    "logo_seiko": [1405, 2605, 1825, 2680],
    "logo_5_shield": [1515, 2725, 1740, 2825],
    "print_automatic_21_jewels": [1399, 3470, 1834, 3583],
    "minute_track_radius_px_at_9": [907, 947],
    "dial_texture_edge_px_at_9": 963,
    "crown_box": [2800, 3490, 2967, 3775],  # knurled crown, axis radial at about 114 deg (4 o'clock)
}
ARTEFACTS = ["thin white wedge from the pivot toward 7 o'clock (about 2.5 mm): crystal reflection, not a hand",
             "bright specks of the woven dial texture: lighting on raised bumps, not print"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    px0, py0 = MANUAL_PX["hand_pivot"]

    # case outline: last foreground pixel along rays on the flanks (no lugs, crown or bracelet there)
    edge = []
    for a in list(np.arange(52, 101, 1.0)) + list(np.arange(250, 309, 1.0)):
        t = math.radians(a)
        rs = np.arange(1100, 1450, 0.5)
        xs, ys = px0 + rs * math.sin(t), py0 - rs * math.cos(t)
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    edge = np.array(edge)
    # crystal ring: first dark pixel moving inward (the gasket); full circle except the crown sector
    g = cv2.GaussianBlur(gray, (0, 0), 2)
    ring = []
    for a in np.arange(0, 360, 1.0):
        if 100 < a < 130:
            continue
        t = math.radians(a)
        for r in np.arange(1250, 1000, -0.5):
            x, y = px0 + r * math.sin(t), py0 - r * math.cos(t)
            if g[int(y), int(x)] < 50:
                ring.append((x, y))
                break
    rcx, rcy, rr = fit_circle(np.array(ring))
    # case radius about the ring centre (sides alone cannot fix the vertical centre)
    case_r = float(np.median(np.hypot(edge[:, 0] - rcx, edge[:, 1] - rcy)))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case outline = {CASE_MM} mm (owner's choice); cross-check bracelet next to the case vs {BRACELET_MM} mm",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((rcx, rcy))},
           "crystal_ring": {"radius_mm": round(rr / S, 3), "centre_mm": mm((rcx, rcy)),
                            "basis": "outer edge of the dark gasket, first pixel darker than 50 moving inward"}}

    # silhouette per y: left/right edge of the white-background mask
    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    case_w = 2 * case_r / S
    lug_top = max(y for y, wd in width.items() if y > 0 and wd > 0.5 * (case_w + 20) and wd < case_w and all(width.get(round(y + k * 0.25, 2), 0) < wd + 0.6 for k in range(1, 3)))
    out["bracelet_width_mm"] = {f"{y:+.0f}": round(width[y], 2) for y in (23, 25, 28, 32, 36, 40, -23, -25, -28, -32, -36, -40) if y in width}
    near = [width[y] for y in width if 22 <= abs(y) <= 24]
    out["checks"] = {"bracelet_next_to_case_mm": round(float(np.median(near)), 2), "expected_mm": BRACELET_MM}

    # bracelet row pitch: autocorrelation of the centre column below the case
    col = gray[int(py0 + 25 * S):int(py0 + 43 * S), px0]
    col = col - col.mean()
    ac = np.correlate(col, col, "full")[len(col) - 1:]
    ac /= ac[0]
    pk = [i / S for i in range(20, len(ac) - 1) if ac[i] > ac[i - 1] and ac[i] >= ac[i + 1] and ac[i] > 0.15]
    out["bracelet_row_autocorr_peaks_mm"] = [round(v, 2) for v in pk[:4]]

    # manual parts
    M = MANUAL_PX
    hands = {}
    for name, tip in (("hour", M["hour_hand_tip"]), ("minute", M["minute_hand_tip"]), ("seconds", M["seconds_hand_tip"])):
        r, a = polar(tip)
        hands[name] = {"angle_deg": a, "length_mm": r}
    hands["seconds"]["tail_mm"] = polar(M["seconds_hand_tail_end"])[0]
    for name in ("hour", "minute"):
        a, b = M[f"{name}_hand_lume"]
        hands[name]["lume_from_to_mm"] = sorted([polar(a)[0], polar(b)[0]])
    out["hands"] = hands
    out["time_shown"] = "about 10:07:19 (from the hand angles)"
    dots = {k: dict(zip(("radius_mm", "angle_deg"), polar(v))) for k, v in M["lume_dots"].items()}
    out["lume_dots"] = dots
    out["lume_dot_radius_mm_median"] = round(float(np.median([d["radius_mm"] for d in dots.values()])), 3)
    out["indices"] = {"inner_outer_radius_mm": {"9": sorted(abs(mm((x, py0))[0]) for x in M["index_9_inner_outer_x"]),
                                                "12": sorted(abs(mm((px0, y))[1]) for y in M["index_12_inner_outer_y"]),
                                                "6": sorted(abs(mm((px0, y))[1]) for y in M["index_6_inner_outer_y"])},
                      "layout": "applied batons at every hour except 3 (day-date); double baton at 12; polished with a dark centre line"}
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k in ("daydate_frame", "logo_seiko", "logo_5_shield", "print_automatic_21_jewels", "crown_box"):
        out[k] = box(M[k])
    out["minute_track_radius_mm"] = sorted(v / S for v in M["minute_track_radius_px_at_9"])
    out["dial_texture_edge_radius_mm"] = round(M["dial_texture_edge_px_at_9"] / S, 3)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(rcx), int(rcy)), int(case_r), (0, 0, 255), 4)
        cv2.circle(ov, (int(rcx), int(rcy)), int(rr), (255, 128, 0), 4)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 3, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 3, (0, 255, 0), -1)
        for name, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            cv2.line(ov, (px0, py0), P((hd["length_mm"] * math.sin(t), hd["length_mm"] * math.cos(t))), (0, 255, 255), 4)
        for d in dots.values():
            t = math.radians(d["angle_deg"])
            cv2.circle(ov, P((d["radius_mm"] * math.sin(t), d["radius_mm"] * math.cos(t))), 18, (255, 0, 255), 4)
        for k in ("daydate_frame", "logo_seiko", "logo_5_shield", "print_automatic_21_jewels", "crown_box"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 4)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "crystal_ring", "checks")}), "->", dest)
