"""Measure the Seiko 5 SNKK65K1 straight-on front photo into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.seiko_snkk65_trace [out.json] [overlay.png]     # default config/watches/seiko-snkk65k1-trace.json

Same method as pipeline/seiko_snkl41_trace.py, on a photo that is already straight (no rectify step). Anchor: case width on
the left flank = 38 mm (spec sheet); the case is concentric with the crystal ring. The listed 18 mm lug width is reported as
a check. mm, x right, y toward 12, origin = hand pivot. Hands, day-date, logo, crown, ring radii and bracelet come from gridded
crops (MANUAL_PX, +-3 px = +-0.07 mm).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-snkk65k1/front_3198.png"
OUT = ROOT / "config/watches/seiko-snkk65k1-trace.json"
CASE_MM = 38.0  # owner's spec sheet, 2026-11-09
LUG_WIDTH_MM = 18.0  # spec sheet

MANUAL_PX = {
    "hand_pivot": [1600, 1512],  # dark hole in the hub cap
    # hour and minute: steel swords (widest just behind the point) with a lume insert, short tails under the hub collar
    "hour_hand_tip": [1308, 1306],
    "hour_hand_tail_end": [1640, 1540],
    "hour_hand_lume": [[1475, 1445], [1330, 1322]],
    "hour_hand_half_width_px": 25,  # outer edge of the steel frame (the dark outline is a halo)
    "minute_hand_tip": [1997, 1180],
    "minute_hand_tail_end": [1565, 1542],
    "minute_hand_lume": [[1790, 1365], [1975, 1200]],
    "minute_hand_half_width_px": 18,
    "seconds_hand_tip": [1080, 1662],  # thin needle; the long tapered steel tail runs over the day-date frame
    "seconds_hand_tail_end": [1885, 1447],
    "seconds_hand_half_width_px": [3, 15],  # needle, tail at the hub (it narrows to 0.7 of that)
    "hub_radius_px": [25, 6],
    "hub_collar_px": 46,  # hour-hand collar round the hub
    "daydate_frame": [1792, 1452, 2162, 1588],  # wide polished frame round both windows
    "daydate_wall_px": 20,
    "logo_seiko": [1458, 1180, 1737, 1240],
    "logo_5_shield": [1518, 1253, 1682, 1337],
    "print_automatic_21_jewels": [1478, 1742, 1722, 1802],
    "print_6": [1480, 2100, 1720, 2125],  # no calibre print legible here; kept as an empty box for the dial-map masks
    "crown_box": [2300, 1765, 2450, 1950],  # fluted crown at about 4 o'clock
    "index_width_px": [37, 75],  # single baton; the 12 is a double-width faceted block
    "index_ring_px": 13,  # rounded outer end with a dark outline (lume pip), radius
    "index_inner_outer_px": [420, 572],  # baton body from the pivot, read at 9 (12: 407-592 incl. the pip)
    "crystal_ring_px": 700,  # outer edge of the green-tinted crystal gasket, read at 9
    "gasket_inner_px": 660,  # inner edge of the green ring, start of the printed minute track
    # bracelet, first row above the case: top surface edges, centre piece, mid pieces (outer links half a row off)
    "bracelet_row_400": {"edges": [1205, 1995], "centre": [1530, 1680], "mid": [[1375, 1530], [1680, 1825]]},
    "end_link_top_px": {"outer": [605, 2437], "centre": [475, 2552]},  # top and bottom of the end link: outer pieces, centre tongue
    "bracelet_joints_y": {"outer_bottom": [2437, 2770], "centre_top": [475, 210], "centre_bottom": [2552, 2840]},
}
ARTEFACTS = ["bright arcs on the polished bezel and case: reflections, not shape",
             "the photo looks upscaled (about 1000 px source): dark outlines round every part are sharpening halos",
             "bracelet rows beyond the first lean away from the camera: pitch from the first rows next to the end links"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    g = cv2.GaussianBlur(gray, (0, 0), 2)
    fg = (765 - im.astype(int).sum(2)) > 45
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a: (px0 + r * math.sin(math.radians(a)), py0 - r * math.cos(math.radians(a)))

    # case outline on the flanks: lugs leave the case above 60 / below 120 deg, the crown sits at 100-125 deg
    edge = []
    for a in list(np.arange(250, 290.1, 1.0)):  # left flank only: the right one has the crown
        rs = np.arange(760, 900, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    rcx, rcy, rr = px0, py0, M["crystal_ring_px"]  # green gasket edge, no dark line to search for
    ccx, ccy = rcx, rcy  # the case is concentric with the crystal ring
    case_r = float(np.median(np.hypot(*(np.array(edge) - (ccx, ccy)).T)))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width on the left flank = {CASE_MM} mm (spec sheet); lug width {LUG_WIDTH_MM} mm (spec sheet) as a check",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "crystal_ring": {"radius_mm": round(rr / S, 3), "centre_mm": mm((rcx, rcy)), "basis": "outer edge of the green crystal gasket"},
           "gasket_inner_mm": round(M["gasket_inner_px"] / S, 3)}

    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                l_ = round((xs.min() - ccx) / S, 3)  # left side mirrored: the right side has the crown and the clasp
                prof.append([round(float(y_mm), 2), l_, -l_])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    tips = [next(y for y in np.arange(18, 30, 0.25) if width[round(sy * (y + 0.25), 2)] < width[round(sy * y, 2)] - 1.0) + 0.125
            for sy in (1, -1)]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    near = [width[y] for y in width if tips[0] + 0.5 <= y <= tips[0] + 3 or -tips[1] - 3 <= y <= -tips[1] - 0.5]
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "bracelet_past_lug_tips_mm": round(float(np.median(near)), 2),
                     "listed_lug_width_mm": LUG_WIDTH_MM}

    # indices: steel batons, no colour to threshold: radii read at 9 and 12 (MANUAL_PX)
    r0, r1 = (v / S for v in M["index_inner_outer_px"])
    idx = {str(hr): {"inner": round(r0, 3), "outer": round(r1, 3)} for hr in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12)}
    out["indices"] = {"per_hour_mm": idx,
                      "inner_mm": round(float(np.median([v["inner"] for k, v in idx.items() if k != "12"])), 3),
                      "outer_mm": round(float(np.median([v["outer"] for k, v in idx.items() if k != "12"])), 3),
                      "width_mm": round(M["index_width_px"][0] / S, 3), "width_12_mm": round(M["index_width_px"][1] / S, 3),
                      "ring_radius_mm": round(M["index_ring_px"] / S, 3),
                      "layout": "applied steel batons with a lengthwise ridge and a rounded, dark-outlined outer end (lume pip); a double-width block at 12; none at 3 (day-date)"}

    hands = {}
    for name in ("hour", "minute"):
        r, a = polar(M[f"{name}_hand_tip"])
        hands[name] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M[f"{name}_hand_tail_end"])[0],
                       "half_width_mm": round(M[f"{name}_hand_half_width_px"] / S, 3),
                       "lume_from_to_mm": sorted(polar(p)[0] for p in M[f"{name}_hand_lume"])}
    r, a = polar(M["seconds_hand_tip"])
    wn, wc = M["seconds_hand_half_width_px"]
    hands["seconds"] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M["seconds_hand_tail_end"])[0],
                        "half_width_mm": round(wn / S, 3), "tail_half_width_mm": round(wc / S, 3)}
    out["hub_collar_mm"] = round(M["hub_collar_px"] / S, 3)
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k in ("daydate_frame", "logo_seiko", "logo_5_shield", "print_automatic_21_jewels", "print_6", "crown_box"):
        out[k] = box(M[k])
    out["daydate_frame"]["wall_mm"] = round(M["daydate_wall_px"] / S, 3)

    row = M["bracelet_row_400"]
    c, hw = sum(row["edges"]) / 2, (row["edges"][1] - row["edges"][0]) / 2
    f = lambda x: round(abs(x - c) / hw, 3)
    out["bracelet_columns"] = {"centre_half": round((f(row["centre"][0]) + f(row["centre"][1])) / 2, 3),
                               "mid_outer": round((f(row["mid"][0][0]) + f(row["mid"][1][1])) / 2, 3),
                               "half_width_mm": round(hw / S, 3), "basis": "fractions of the bracelet half width, row at y = 400 px"}
    e = M["end_link_top_px"]
    yt = lambda v: [round((py0 - v[0]) / S, 3), round((v[1] - py0) / S, 3)]  # distance from the pivot, top and bottom
    out["end_link_top_mm"] = {k: yt(v) for k, v in e.items()}
    j = M["bracelet_joints_y"]
    out["bracelet_pitch_mm"] = round(float(np.mean([abs(b - a) / S for a, b in j.values()])), 3)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(ccx), int(ccy)), int(case_r), (0, 0, 255), 4)
        cv2.circle(ov, (int(rcx), int(rcy)), int(rr), (255, 128, 0), 4)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 3, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 3, (0, 255, 0), -1)
        for name, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            cv2.line(ov, P((-hd["tail_mm"] * math.sin(t), -hd["tail_mm"] * math.cos(t))),
                     P((hd["length_mm"] * math.sin(t), hd["length_mm"] * math.cos(t))), (0, 255, 255), 3)
        for hr, v in idx.items():
            t = math.radians(int(hr) * 30)
            for r_ in (v["inner"], v["outer"]):
                cv2.circle(ov, P((r_ * math.sin(t), r_ * math.cos(t))), 8, (255, 0, 255), 3)
        for k in ("daydate_frame", "logo_seiko", "logo_5_shield", "print_automatic_21_jewels", "print_6", "crown_box"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 3)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "crystal_ring", "lug_tip_mm", "checks", "indices", "hands",
                                           "bracelet_columns", "end_link_top_mm", "bracelet_pitch_mm")}, default=float), "->", dest)
