"""Measure the Seiko 5 SNK623K1 front photo, straightened by pipeline/seiko_snk623_rectify.py, into mm. Host-side, numpy +
OpenCV, no Blender.

    python3 -B -m pipeline.seiko_snk623_rectify          # first: outputs/watches/seiko-snk623k1/front_rectified.png
    python3 -B -m pipeline.seiko_snk623_trace [out.json] [overlay.png]     # default config/watches/seiko-snk623k1-trace.json

Same method as pipeline/seiko_snkl41_trace.py. Anchor: case width on the left flank = 38 mm (owner's spec sheet); the case is
taken as concentric with the crystal ring (the right flank shows the case side and crown). The spec sheet's 10 mm "lug width"
is the centre link between the lugs and is reported as a check. mm, x right, y toward 12, origin = hand pivot. Hands, windows,
logo, numerals, crown and bracelet come from gridded crops (MANUAL_PX, +-3 px = +-0.08 mm); rings and index radii from
radial profiles.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "outputs/watches/seiko-snk623k1/front_rectified.png"
OUT = ROOT / "config/watches/seiko-snk623k1-trace.json"
CASE_MM = 38.0  # owner's spec sheet, 2026-11-09 (most listings say 37)
CENTRE_LINK_MM = 10.0  # spec sheet "lug width": the centre column between the lugs

MANUAL_PX = {
    "hand_pivot": [1443, 1438],  # hole in the hub cap
    # hour and minute: faceted steel dauphine, widest at the root, pointed tails; seconds: needle with a counterweight bar
    "hour_hand_tip": [1182, 1268],
    "hour_hand_tail_end": [1525, 1495],
    "hour_hand_half_width_px": 32,
    "minute_hand_tip": [1826, 1150],
    "minute_hand_tail_end": [1365, 1497],
    "minute_hand_half_width_px": 25,
    "seconds_hand_tip": [952, 1607],
    "seconds_hand_tail_end": [1630, 1385],
    "seconds_hand_half_width_px": [4, 17],  # needle, counterweight bar
    "hub_radius_px": [22, 6],
    "date_window": [1808, 1403, 1942, 1497],  # white window with a grey frame at 3: stays in the dial map
    "day_window": [1335, 1684, 1577, 1750],  # white pill with red SUNDAY above the 6: stays in the dial map
    "logo_seiko": [1327, 1133, 1567, 1180],
    "logo_5_shield": [1379, 1200, 1521, 1276],
    "print_automatic_21_jewels": [1346, 1576, 1558, 1640],
    "numeral_12": [1378, 990, 1516, 1094],  # applied polished steel numerals
    "numeral_9": [974, 1394, 1082, 1502],
    "numeral_6": [1392, 1808, 1506, 1912],
    "crown_box": [2090, 1680, 2190, 1810],  # steel fluted crown at about 4 o'clock
    "index_width_px": 33,  # applied steel batons at 1, 2, 4, 5, 7, 8, 10, 11
    "index_inner_outer_px": [361, 482],  # median of the radial runs (raised: the lower right ones sit about 12 px further out)
    "ring_radii_px": {"dial_edge": 556, "gasket": 590},  # black dial ends; silver rehaut 560-584; dark gasket; grey bezel slope
    # bracelet: the centre column runs into a notch in the case between the lugs; outer columns start at the lug tips
    "bracelet_centre_x": 1466,  # middle of the two column gaps (the raised bracelet sits about 23 px right of the pivot)
    "bracelet_column_gaps_x": [1270, 1662],
    "bracelet_outer_edge_x": 1078,  # left edge of the outer links, top and bottom rows
    "centre_start_y": [728, 2190],  # dark gap of the notch, top and bottom
    "lug_tip_y": [599, 2345],  # dark gap where the outer links start, top and bottom
    "bracelet_joints_y": {"top_centre": [250, 503], "bottom_centre": [2190, 2451]},  # rows further out lean away from the camera
}
ARTEFACTS = ["bright arcs on the polished bezel, case and bracelet: reflections, not shape",
             "straightened from a photo turned toward the crown: bezel, case and bracelet stand off the dial plane and keep some parallax; the bracelet centre sits about 23 px right of the pivot and the bottom half reads about 50 px longer than the top",
             "bracelet rows past the second joint lean away from the camera: pitch from the first rows only"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    g = cv2.GaussianBlur(gray, (0, 0), 1)
    fg = (765 - im.astype(int).sum(2)) > 45
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a: (px0 + r * math.sin(math.radians(a)), py0 - r * math.cos(math.radians(a)))

    # case outline on the left flank (the right one shows the case side and crown)
    edge = []
    for a in np.arange(250, 290.1, 1.0):
        rs = np.arange(650, 950, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    # crystal ring: the dark gasket line between the silver rehaut and the bezel slope, skipping the crown side
    ring = []
    for a in np.arange(0, 360, 2.0):
        if 80 <= a <= 130:
            continue
        r0 = M["ring_radii_px"]["gasket"] - 14
        prof = [g[int(at(r, a)[1]), int(at(r, a)[0])] for r in np.arange(r0, r0 + 28, 0.5)]
        ring.append(at(r0 + 0.5 * int(np.argmin(prof)), a))
    rcx, rcy, rr = fit_circle(np.array(ring))
    ccx, ccy = rcx, rcy
    case_r = float(np.median(np.hypot(*(np.array(edge) - (ccx, ccy)).T)))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width on the left flank = {CASE_MM} mm (spec sheet); centre link {CENTRE_LINK_MM} mm (spec sheet 'lug width') as a check",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "crystal_ring": {"radius_mm": round(rr / S, 3), "centre_mm": mm((rcx, rcy)), "basis": "dark gasket line outside the silver rehaut"},
           "dial_edge_mm": round(M["ring_radii_px"]["dial_edge"] / S, 3)}

    # silhouette per y: left side mirrored, measured from the case centre on the case and from the bracelet centre past it
    bx = M["bracelet_centre_x"]
    tips = [(py0 - M["lug_tip_y"][0]) / S, (M["lug_tip_y"][1] - py0) / S]
    starts = [(py0 - M["centre_start_y"][0]) / S, (M["centre_start_y"][1] - py0) / S]
    R = case_r / S
    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                k = min(max((abs(y_mm) - 0.5 * R) / (0.5 * R), 0.0), 1.0)
                cx_ = ccx + k * (bx - ccx)  # case centre on the case, blending to the bracelet centre at the lugs (no step)
                l_ = round((xs.min() - cx_) / S, 3)
                prof.append([round(float(y_mm), 2), l_, -l_])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    circ = lambda y: 2 * math.sqrt(max(R * R - y * y, 0))
    lug_from = [next(y for y in np.arange(5, 20, 0.25) if width[round(sy * y, 2)] > circ(y) + 0.3) for sy in (1, -1)]
    out["lug_from_y_mm"] = round(sum(lug_from) / 2, 3)
    out["lug_tip_mm"] = {"top": round(tips[0], 3), "bottom": round(tips[1], 3), "mean": round(sum(tips) / 2, 3)}
    out["centre_start_mm"] = {"top": round(starts[0], 3), "bottom": round(starts[1], 3), "mean": round(sum(starts) / 2, 3)}
    gaps = M["bracelet_column_gaps_x"]
    half = (bx - M["bracelet_outer_edge_x"]) / S
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "bracelet_width_mm": round(2 * half, 2),
                     "centre_link_mm": round((gaps[1] - gaps[0]) / S, 2), "listed_centre_link_mm": CENTRE_LINK_MM}
    out["bracelet_half_width_mm"] = round(half, 3)

    r0, r1 = (v / S for v in M["index_inner_outer_px"])
    out["indices"] = {"inner_mm": round(r0, 3), "outer_mm": round(r1, 3), "width_mm": round(M["index_width_px"] / S, 3),
                      "hours": [1, 2, 4, 5, 7, 8, 10, 11],
                      "layout": "applied steel batons with a ridge at 1, 2, 4, 5, 7, 8, 10, 11; applied numerals 12, 9, 6; date at 3"}

    hands = {}
    for name in ("hour", "minute"):
        r, a = polar(M[f"{name}_hand_tip"])
        hands[name] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M[f"{name}_hand_tail_end"])[0],
                       "half_width_mm": round(M[f"{name}_hand_half_width_px"] / S, 3)}
    r, a = polar(M["seconds_hand_tip"])
    wn, wc = M["seconds_hand_half_width_px"]
    hands["seconds"] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M["seconds_hand_tail_end"])[0],
                        "half_width_mm": round(wn / S, 3), "tail_half_width_mm": round(wc / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    boxes = ("date_window", "day_window", "logo_seiko", "logo_5_shield", "print_automatic_21_jewels",
             "numeral_12", "numeral_9", "numeral_6", "crown_box")
    for k in boxes:
        out[k] = box(M[k])

    j = M["bracelet_joints_y"]
    out["bracelet_pitch_mm"] = round(float(np.mean([(b - a) / S for a, b in j.values()])), 3)
    out["bracelet_centre_half"] = round(((bx - gaps[0]) + (gaps[1] - bx)) / 2 / S / half, 3)
    out["bracelet_centre_phase"] = round((out["lug_tip_mm"]["mean"] - out["centre_start_mm"]["mean"]) / out["bracelet_pitch_mm"], 3)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(ccx), int(ccy)), int(case_r), (0, 0, 255), 3)
        cv2.circle(ov, (int(rcx), int(rcy)), int(rr), (255, 128, 0), 3)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 3, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 3, (0, 255, 0), -1)
        for name, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            cv2.line(ov, P((-hd["tail_mm"] * math.sin(t), -hd["tail_mm"] * math.cos(t))),
                     P((hd["length_mm"] * math.sin(t), hd["length_mm"] * math.cos(t))), (0, 255, 255), 2)
        for hr in out["indices"]["hours"]:
            t = math.radians(hr * 30)
            cv2.line(ov, P((r0 * math.sin(t), r0 * math.cos(t))), P((r1 * math.sin(t), r1 * math.cos(t))), (255, 0, 255), 2)
        for k in boxes:
            cv2.rectangle(ov, tuple(M[k][:2]), tuple(M[k][2:]), (0, 200, 255), 2)
        for y in (tips[0], -tips[1], starts[0], -starts[1], out["lug_from_y_mm"], -out["lug_from_y_mm"]):
            cv2.line(ov, P((-14, y)), P((14, y)), (255, 255, 0), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "crystal_ring", "dial_edge_mm", "lug_from_y_mm", "lug_tip_mm",
                                           "centre_start_mm", "checks", "indices", "hands", "bracelet_pitch_mm",
                                           "bracelet_centre_half", "bracelet_centre_phase")}, default=float), "->", dest)
