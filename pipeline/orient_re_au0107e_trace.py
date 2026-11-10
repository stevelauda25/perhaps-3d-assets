"""Measure the Orient Star RE-AU0107E front photo (2x working copy, 2388 x 4032) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.orient_re_au0107e_trace [out.json] [overlay.png]   # default config/watches/orient-re-au0107e-trace.json

Same method as pipeline/seiko_sur419_trace.py. Anchor: case diameter 38.5 mm (listing); listed lug width 20 mm and lug to lug
46.9 mm are reported as checks. mm, x right, y toward 12, origin = hand pivot. The sunburst and the ribbed rings defeat
threshold tracing, so hands, indices, date, logo, crown and bracelet joints come from gridded crops (MANUAL_PX, +-3 px of the
2x copy = +-0.06 mm); the applied serif XII and VI are rebuilt from their measured strokes (a colour mask picks up the ribbed ring around them).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/orient-re-au0107e/front_2x_2388x4032.png"
OUT = ROOT / "config/watches/orient-re-au0107e-trace.json"
CASE_MM = 38.5  # listing (most retailers); the photo gives 46.9 mm lug to lug at this scale, as listed
LISTED = {"lug_width_mm": 20.0, "lug_to_lug_mm": 46.9}

MANUAL_PX = {
    "hand_pivot": [1123, 2008],
    # hour and minute: faceted swords with a pointed counter-tail; widths include the dark facet
    "hour_hand_tip": [730, 1728],
    "hour_hand_tail_end": [1275, 2115],
    "hour_hand_half_width_px": [40, 27],  # near the root, at 85 % of the length
    "hour_hand_tail_half_width_px": 52,
    "minute_hand_tip": [1555, 1445],
    "minute_hand_tail_end": [1044, 2111],
    "minute_hand_half_width_px": [36, 21],
    "minute_hand_tail_half_width_px": 32,
    "seconds_hand_tip": [668, 2548],
    "seconds_hand_tail_end": [1226, 1886],  # end of the dark counterweight
    "seconds_hand_width_px": [12, 24],  # needle, counterweight
    "hub_radius_px": [42, 20],
    "date_window": [1527, 1942, 1702, 2092],  # black frame included
    "logo": [860, 2160, 1345, 2370],  # Orient Star emblem, ORIENT STAR, AUTOMATIC
    "power_reserve": [820, 1500, 1350, 1885],  # silver arc, 50 25 0, its hand
    "print_6": [930, 2640, 1330, 2700],  # JAPAN ... calibre print beside the VI
    "numeral_12": [1028, 1305, 1240, 1487],
    "numeral_6": [1040, 2532, 1200, 2718],
    # applied serif numerals rebuilt from their strokes (y top, y bottom; stroke = x left/right at the top and the bottom;
    # serif = x0, x1 on the top or bottom line, 10 px tall)
    "numeral_12_glyph": {"y": [1310, 1482], "strokes": [[1052, 1082, 1090, 1118], [1098, 1108, 1044, 1054], [1143, 1173, 1143, 1173],
                                                        [1197, 1227, 1197, 1227]],
                         "serifs_top": [[1033, 1092], [1095, 1122], [1136, 1180], [1190, 1236]],
                         "serifs_bottom": [[1030, 1072], [1080, 1125], [1136, 1180], [1190, 1236]]},
    "numeral_6_glyph": {"y": [2537, 2713], "strokes": [[1063, 1098, 1100, 1112], [1128, 1140, 1102, 1112], [1155, 1183, 1155, 1183]],
                        "serifs_top": [[1043, 1103], [1113, 1155], [1150, 1197]], "serifs_bottom": [[1150, 1197]]},
    "index_3": [1732, 1957, 1830, 2077],  # wide double baton outside the date
    "index_9": [425, 1945, 612, 2055],  # wide baton with a groove
    "index_width_px": 52,  # 1 2 4 5 7 8 10 11
    "index_r_px": [545, 700],  # inner, outer end (1 and 7 measured)
    "dot_r_px": 721,  # printed lume dots outside each index
    "crown_box": [2045, 1885, 2190, 2170],  # fluted part and end cap
    "dial_edge_px": 757,  # green ends, silver rehaut starts (3 o'clock ray)
    # bracelet: centre joints sit nearer the case than the outer ones; five pieces per row (outer, narrow polished, centre)
    "bracelet_joints_y": {"top_outer": [895, 610, 320], "top_centre": [700, 400],
                          "bottom_outer": [3160, 3440, 3700], "bottom_centre": [3125, 3370, 3625, 3840]},
    "bracelet_columns_px": {"centre": [[985, 1330], [950, 1300]], "narrow": [[935, 1375], [900, 1345]]},
    "end_link_x_px": [650, 1620],
}
ARTEFACTS = ["the bracelet runs about 0.7 mm right of the pivot (watch slightly turned): the build centres it",
             "bright arcs on the polished bezel: reflections, not shape",
             "the photo is 1194 x 2016 (23.8 px/mm); the 2x copy adds no detail"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a: (px0 + r * math.sin(math.radians(a)), py0 - r * math.cos(math.radians(a)))

    # case outline on the flanks: the lugs leave the case above 57 / below 123 deg, the crown sits at 80-100 deg
    edge = []
    for a in list(np.arange(62, 78.1, 1.0)) + list(np.arange(102, 118.1, 1.0)) + list(np.arange(242, 298.1, 1.0)):
        rs = np.arange(850, 1000, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    ccx, ccy, case_r = fit_circle(np.array(edge))
    # crystal edge: the dark gasket line between the silver rehaut and the polished bezel
    ring = []
    for a in np.arange(0, 360, 3.0):
        if 75 <= a <= 105:
            continue
        rs = np.arange(780, 850, 0.5)
        v = [gray[int(at(r, a)[1]), int(at(r, a)[0])] for r in rs]
        i = int(np.argmin(v))
        if v[i] < 90:
            ring.append(at(rs[i], a))
    rcx, rcy, rr = fit_circle(np.array(ring))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case diameter = {CASE_MM} mm (listing)",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "crystal_ring": {"radius_mm": round(rr / S, 3), "centre_mm": mm((rcx, rcy)), "basis": "dark gasket line inside the polished bezel"},
           "dial_edge_radius_mm": round(M["dial_edge_px"] / S, 3)}

    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    tips = [next(y for y in np.arange(18, 30, 0.25) if width[round(sy * (y + 0.25), 2)] < width[round(sy * y, 2)] - 1.0) + 0.125
            for sy in (1, -1)]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    out["bracelet_width_mm"] = {f"{y:+.0f}": round(width[y], 2) for y in (24, 28, 32, 36, 40, -24, -28, -32, -36, -40) if y in width}
    near = [width[y] for y in width if tips[0] + 0.5 <= y <= tips[0] + 2 or -tips[1] - 2 <= y <= -tips[1] - 0.5]
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "bracelet_past_lug_tips_mm": round(float(np.median(near)), 2),
                     "end_link_width_mm": round((M["end_link_x_px"][1] - M["end_link_x_px"][0]) / S, 2), "listed": LISTED}

    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    r0, r1 = M["index_r_px"]
    out["indices"] = {"inner_mm": round(r0 / S, 3), "outer_mm": round(r1 / S, 3), "width_mm": round(M["index_width_px"] / S, 3),
                      "dot_r_mm": round(M["dot_r_px"] / S, 3), "index_3": box(M["index_3"]), "index_9": box(M["index_9"]),
                      "layout": "applied polished faceted batons at 1 2 4 5 7 8 10 11; wide batons at 3 (short, outside the date) and 9; applied XII and VI"}

    hands = {}
    for name in ("hour", "minute"):
        r, a = polar(M[f"{name}_hand_tip"])
        w0, w1 = M[f"{name}_hand_half_width_px"]
        hands[name] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M[f"{name}_hand_tail_end"])[0],
                       "half_width_root_mm": round(w0 / S, 3), "half_width_tip_mm": round(w1 / S, 3),
                       "tail_half_width_mm": round(M[f"{name}_hand_tail_half_width_px"] / S, 3)}
    r, a = polar(M["seconds_hand_tip"])
    wn, wc = M["seconds_hand_width_px"]
    hands["seconds"] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M["seconds_hand_tail_end"])[0],
                        "half_width_mm": round(wn / 2 / S, 3), "tail_half_width_mm": round(wc / 2 / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    for k in ("date_window", "logo", "power_reserve", "print_6", "numeral_12", "numeral_6", "crown_box"):
        out[k] = box(M[k])

    # applied XII and VI: strokes (quads) and serifs (rects) in mm
    for k in ("numeral_12", "numeral_6"):
        gl = M[k + "_glyph"]
        yt, yb = gl["y"]
        quads = [[mm((a, yt)), mm((b, yt)), mm((d, yb)), mm((c, yb))] for a, b, c, d in gl["strokes"]]
        quads += [[mm((x0, yt)), mm((x1, yt)), mm((x1, yt + 10)), mm((x0, yt + 10))] for x0, x1 in gl["serifs_top"]]
        quads += [[mm((x0, yb - 10)), mm((x1, yb - 10)), mm((x1, yb)), mm((x0, yb))] for x0, x1 in gl["serifs_bottom"]]
        out[k + "_quads"] = quads

    j = M["bracelet_joints_y"]
    pitch = [abs(a - b) / S for k in ("top_outer", "bottom_outer") for a, b in zip(j[k][1:], j[k][:-1])]  # outer: clean joints
    out["bracelet_pitch_mm"] = round(float(np.median(pitch)), 3)
    out["bracelet_joints_mm"] = {k: [round(abs(y - py0) / S, 3) for y in v] for k, v in j.items()}
    shift = [abs(o - c) / S for o, c in ((j["top_outer"][1], j["top_centre"][0]), (j["top_outer"][2], j["top_centre"][1]),
                                         (j["bottom_outer"][1], j["bottom_centre"][1]), (j["bottom_outer"][2], j["bottom_centre"][2]))]
    out["bracelet_centre_joint_shift_mm"] = round(float(np.mean(shift)), 3)
    cols = M["bracelet_columns_px"]
    out["bracelet_centre_half_mm"] = round(float(np.mean([(c[1] - c[0]) / 2 / S for c in cols["centre"]])), 3)
    out["bracelet_narrow_half_mm"] = round(float(np.mean([(c[1] - c[0]) / 2 / S for c in cols["narrow"]])), 3)
    out["end_link_half_mm"] = round((M["end_link_x_px"][1] - M["end_link_x_px"][0]) / 2 / S, 3)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(ccx), int(ccy)), int(case_r), (0, 0, 255), 2)
        cv2.circle(ov, (int(rcx), int(rcy)), int(rr), (0, 0, 255), 2)
        cv2.circle(ov, (px0, py0), M["dial_edge_px"], (0, 128, 255), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 2, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 2, (0, 255, 0), -1)
        for name, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            cv2.line(ov, P((-hd["tail_mm"] * math.sin(t), -hd["tail_mm"] * math.cos(t))),
                     P((hd["length_mm"] * math.sin(t), hd["length_mm"] * math.cos(t))), (0, 255, 255), 2)
        for hr in range(1, 13):
            t = math.radians(hr * 30)
            for r_ in (r0, r1, M["dot_r_px"]):
                cv2.circle(ov, (int(px0 + r_ * math.sin(t)), int(py0 - r_ * math.cos(t))), 6, (255, 0, 255), 2)
        for k in ("date_window", "logo", "power_reserve", "print_6", "index_3", "index_9", "crown_box"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 2)
        for k in ("numeral_12_quads", "numeral_6_quads"):
            for q in out[k]:
                cv2.polylines(ov, [np.array([P(p) for p in q], np.int32)], True, (255, 255, 0), 1)
        for v in j.values():
            for y in v:
                cv2.line(ov, (500, y), (1900, y), (255, 128, 0), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "crystal_ring", "dial_edge_radius_mm", "lug_tip_mm", "checks",
                                           "indices", "hands", "bracelet_pitch_mm", "bracelet_centre_joint_shift_mm",
                                           "bracelet_centre_half_mm", "bracelet_narrow_half_mm", "end_link_half_mm")}, default=float), "->", dest)
