"""Measure the Seiko 5 SNK381K1 front photo (white background, 4698 x 9372) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.seiko_snk381_trace [out.json] [overlay.png]     # default config/watches/seiko-snk381k1-trace.json

Same method and output keys as pipeline/seiko_trace.py (SNK607K1), so the build reads both alike. Anchor: case outline = 37.0 mm
(listings), cross-check bracelet next to the case vs 20 mm. mm, x right, y toward 12, origin = hand pivot. Hands, day-date,
logo, crown and hour dots are read from gridded crops (MANUAL_PX, +-8 px = +-0.07 mm); hour dots are then snapped to the
centroid of the bright blob. The applied numerals stay in the dial map (pipeline/seiko_snk381_dial.py).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_print import UP, shapes_from_mask
from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-snk381k1/front_4698x9372.png"
OUT = ROOT / "config/watches/seiko-snk381k1-trace.json"
CASE_MM = 37.0
BRACELET_MM = 20.0

MANUAL_PX = {
    "hand_pivot": [2292, 4677],
    "hour_hand_tip": [1653, 4239],
    "hour_hand_lume": [[1724, 4284], [2089, 4586]],
    "minute_hand_tip": [3356, 3847],
    "minute_hand_lume": [[2449, 4569], [3207, 3959]],
    "seconds_hand_tip": [1206, 3864],
    "seconds_hand_tail_end": [2830, 5094],  # centre of the lume disc on the tail
    "seconds_tail_disc_radius_px": [77, 97],  # lume disc, polished rim
    "hub_radius_px": [89, 125],  # black cap, polished ring
    "lume_dots": {"12": [2281, 3262], "1": [3000, 3457], "2": [3514, 3984], "4": [3527, 5392], "5": [3012, 5922],
                  "6": [2300, 6116], "7": [1584, 5926], "8": [1061, 5404], "9": [867, 4693], "10": [1057, 3984], "11": [1579, 3457]},
    "daydate_frame": [2810, 4533, 3680, 4840],
    "logo_seiko": [1960, 3899, 2628, 4008],
    "logo_5_shield": [2105, 4075, 2432, 4286],
    "print_automatic_21_jewels": [1990, 5240, 2600, 5420],
    "numeral_10": [1086, 3959, 1547, 4324],
    "crown_box": [4050, 5230, 4390, 5720],  # knurled crown at about 4 o'clock
}
ARTEFACTS = ["bright arcs on the polished bezel and case: reflections, not shape",
             "the seconds hand crosses the top of the 0 of 10; the dial map repairs it by mirroring the 0"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]

    # case outline on the flanks (no lugs, crown or bracelet there)
    edge = []
    for a in list(np.arange(52, 95, 1.0)) + list(np.arange(250, 309, 1.0)):
        t = math.radians(a)
        rs = np.arange(1700, 2300, 0.5)
        xs, ys = px0 + rs * math.sin(t), py0 - rs * math.cos(t)
        ok = (xs >= 0) & (xs < w) & (ys >= 0) & (ys < h)
        hit = np.nonzero(fg[ys[ok].astype(int), xs[ok].astype(int)])[0]
        edge.append((xs[ok][hit[-1]], ys[ok][hit[-1]]))
    edge = np.array(edge)
    # crystal ring: first dark pixel moving inward (the gasket), skipping the day-date sector
    g = cv2.GaussianBlur(gray, (0, 0), 2)
    ring = []
    for a in np.arange(0, 360, 1.0):
        if 75 < a < 105:
            continue
        t = math.radians(a)
        for r in np.arange(1850, 1400, -0.5):
            x, y = px0 + r * math.sin(t), py0 - r * math.cos(t)
            if g[int(y), int(x)] < 50:
                ring.append((x, y))
                break
    rcx, rcy, rr = fit_circle(np.array(ring))
    case_r = float(np.median(np.hypot(edge[:, 0] - rcx, edge[:, 1] - rcy)))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case outline = {CASE_MM} mm (listings); cross-check bracelet next to the case vs {BRACELET_MM} mm",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((rcx, rcy))},
           "crystal_ring": {"radius_mm": round(rr / S, 3), "centre_mm": mm((rcx, rcy)),
                            "basis": "outer edge of the dark gasket, first pixel darker than 50 moving inward"}}

    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    out["bracelet_width_mm"] = {f"{y:+.0f}": round(width[y], 2) for y in (23, 25, 28, 32, 36, 40, -23, -25, -28, -32, -36, -40) if y in width}
    near = [width[y] for y in width if 22 <= abs(y) <= 24]
    out["checks"] = {"bracelet_next_to_case_mm": round(float(np.median(near)), 2), "expected_mm": BRACELET_MM}

    col = gray[int(py0 + 25 * S):int(py0 + 40 * S), px0 - int(4 * S)]  # outer-mid column below the case
    col = col - col.mean()
    ac = np.correlate(col, col, "full")[len(col) - 1:]
    ac /= ac[0]
    pk = [i / S for i in range(20, len(ac) - 1) if ac[i] > ac[i - 1] and ac[i] >= ac[i + 1] and ac[i] > 0.15]
    out["bracelet_row_autocorr_peaks_mm"] = [round(v, 2) for v in pk[:4]]

    hands = {}
    for name in ("hour", "minute", "seconds"):
        r, a = polar(M[f"{name}_hand_tip"])
        hands[name] = {"angle_deg": a, "length_mm": r}
    hands["seconds"]["tail_mm"], hands["seconds"]["tail_angle_deg"] = polar(M["seconds_hand_tail_end"])
    hands["seconds"]["tail_disc_radius_mm"] = [round(v / S, 3) for v in M["seconds_tail_disc_radius_px"]]
    hands["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    for name in ("hour", "minute"):
        a, b = M[f"{name}_hand_lume"]
        hands[name]["lume_from_to_mm"] = sorted([polar(a)[0], polar(b)[0]])
    out["hands"] = hands
    out["time_shown"] = "about 10:08:50 (from the hand angles)"

    dots = {}
    for k, (x, y) in M["lume_dots"].items():  # snap to the bright blob's centroid
        win = gray[y - 60:y + 61, x - 60:x + 61] > 160
        n, lab, st, cen = cv2.connectedComponentsWithStats(win.astype(np.uint8))
        i = 1 + int(np.argmax(st[1:, 4])) if n > 1 else None
        p = (x - 60 + cen[i][0], y - 60 + cen[i][1]) if i else (x, y)
        dots[k] = dict(zip(("radius_mm", "angle_deg"), polar(p)))
        dots[k]["blob_radius_mm"] = round(math.sqrt(st[i, 4] / math.pi) / S, 3) if i else None
    out["lume_dots"] = dots
    out["lume_dot_radius_mm_median"] = round(float(np.median([d["radius_mm"] for d in dots.values()])), 3)
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k in ("daydate_frame", "logo_seiko", "logo_5_shield", "print_automatic_21_jewels", "crown_box"):
        out[k] = box(M[k])
    # applied "5" shield: bright plate with the 5 as a hole
    x0, y0, x1, y1 = M["logo_5_shield"]
    pad = 12
    crop = (gray[y0 - pad:y1 + pad, x0 - pad:x1 + pad] > 150).astype(np.uint8) * 255
    crop = cv2.morphologyEx(crop, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(crop)
    crop = (lab == 1 + int(np.argmax(st[1:, 4]))).astype(np.uint8) * 255
    up = cv2.GaussianBlur(cv2.resize(crop, None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR), (0, 0), UP * 0.45)
    to_mm = lambda p: [round((p[0] / UP + x0 - pad - px0) / S, 3), round(-(p[1] / UP + y0 - pad - py0) / S, 3)]
    out["logo_5_shield_shapes"] = shapes_from_mask((up > 128).astype(np.uint8) * 255, to_mm, 300)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(rcx), int(rcy)), int(case_r), (0, 0, 255), 6)
        cv2.circle(ov, (int(rcx), int(rcy)), int(rr), (255, 128, 0), 6)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 5, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 5, (0, 255, 0), -1)
        for name in ("hour", "minute", "seconds"):
            hd = hands[name]
            t = math.radians(hd["angle_deg"])
            cv2.line(ov, (px0, py0), P((hd["length_mm"] * math.sin(t), hd["length_mm"] * math.cos(t))), (0, 255, 255), 6)
        for d in dots.values():
            t = math.radians(d["angle_deg"])
            cv2.circle(ov, P((d["radius_mm"] * math.sin(t), d["radius_mm"] * math.cos(t))), 25, (255, 0, 255), 5)
        for k in ("daydate_frame", "logo_seiko", "logo_5_shield", "print_automatic_21_jewels", "crown_box", "numeral_10"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 6)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "crystal_ring", "checks", "bracelet_row_autocorr_peaks_mm")}), "->", dest)
