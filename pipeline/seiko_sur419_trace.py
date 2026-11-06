"""Measure the Seiko SUR419P1 front photo (white background, 3366 x 5871) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.seiko_sur419_trace [out.json] [overlay.png]     # default config/watches/seiko-sur419p1-trace.json

Same method as pipeline/seiko_snk361_trace.py. Anchor: case width on the flanks = 39.4 mm (Irsyad); listed lug width 20 mm and
lug to lug 46.4 mm are reported as checks. mm, x right, y toward 12, origin = hand pivot. The guilloche and sunburst dial defeat
threshold tracing, so hands, date, logo, crown and bracelet joints come from gridded crops (MANUAL_PX, +-5 px = +-0.07 mm);
ring and index radii from radial profiles; the applied 12 and 6 by threshold (clean polished outline on blue).
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
FRONT = ROOT / "references/seiko-sur419p1/front_3366x5871.png"
OUT = ROOT / "config/watches/seiko-sur419p1-trace.json"
CASE_MM = 39.4  # Irsyad, 2026-11-06
LISTED = {"lug_width_mm": 20.0, "lug_to_lug_mm": 46.4}

MANUAL_PX = {
    "hand_pivot": [1636, 2812],
    # hour and minute: faceted pointed batons; the lit facet is measured, the dark facet merges with the dial (width doubled)
    "hour_hand_tip": [1072, 2460],
    "hour_hand_tail_end": [1866, 2955],
    "hour_hand_lit_facet_px": [40, 18],  # at 10 % and 90 % of the length
    "hour_hand_tail_width_px": 37,
    "minute_hand_tip": [2197, 2020],
    "minute_hand_tail_end": [1469, 3056],
    "minute_hand_lit_facet_px": [40, 15],
    "minute_hand_tail_width_px": 35,
    "seconds_hand_tip": [2205, 3652],
    "seconds_hand_tail_end": [1443, 2523],  # tip of the skeleton lancet counterweight
    "seconds_hand_width_px": [12, 50],  # needle, widest point of the counterweight
    "hub_radius_px": [41, 17],  # polished hub, cap
    "date_window": [2322, 2723, 2559, 2903],
    "logo_seiko": [1385, 2245, 1910, 2345],
    "numeral_12": [1540, 1745, 1755, 2025],
    "numeral_6": [1555, 3610, 1700, 3885],
    "crown_box": [3057, 2729, 3200, 2986],  # fluted part only, collar inside the case edge
    "index_width_px": [80, 36],  # long batons: outer end, inner end
    "short_index_width_px": 33,  # 3, outside the date window
    "index_3_x_px": [2579, 2719],
    # bracelet: joints are dark rows; the centre column's joints sit about 1 mm nearer the case than the outer columns'
    "bracelet_joints_y": {"top_outer": [813, 1230], "top_centre": [448, 880], "bottom_outer": [4483, 4958, 5405],
                          "bottom_centre": [4380, 4850, 5320]},
    "bracelet_rows": {"y": [1200, 4380], "edges": [[1000, 2380], [920, 2320]], "centre": [[1330, 2050], [1250, 1976]],
                      "grooves": [[1470, 1960], [1370, 1860]]},
}
ARTEFACTS = ["bright arcs on the polished bezel and case: reflections, not shape",
             "the bracelet sits about 1 mm right of the pivot (watch slightly turned): the build centres it",
             "the photo is about 5 % larger toward 6 (lug tip 23.3 mm at 6, 22.1 mm at 12): means are used"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    g = cv2.GaussianBlur(gray, (0, 0), 2)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a: (px0 + r * math.sin(math.radians(a)), py0 - r * math.cos(math.radians(a)))

    # case outline on the flanks: the lugs leave the case above 60 / below 120 deg, the crown sits at 80-100 deg
    edge = []
    for a in list(np.arange(60, 78.1, 1.0)) + list(np.arange(102, 120.1, 1.0)) + list(np.arange(240, 300.1, 1.0)):
        rs = np.arange(1300, 1600, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    edge = np.array(edge)
    ccx, ccy, case_r = fit_circle(edge)
    # dial edge: bright rehaut ring after the dark outer track; bezel inner edge: next bright rise after the gap
    ring, dial_edge = [], []
    for a in np.arange(0, 360, 2.0):
        if 80 <= a <= 100:  # date and crown side has a different profile
            continue
        prof = [g[int(at(r, a)[1]), int(at(r, a)[0])] for r in np.arange(1100, 1300, 1.0)]
        first = next((i for i, v in enumerate(prof) if v > 150), None)
        bez = next((i for i in range(first + 40, len(prof)) if prof[i] > 190), None) if first is not None else None
        if bez is None:  # glare or the hands on this ray
            continue
        dial_edge.append(at(1100 + first, a))
        ring.append(at(1100 + bez, a))
    rcx, rcy, rr = fit_circle(np.array(ring))
    _, _, rd = fit_circle(np.array(dial_edge))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width on the flanks = {CASE_MM} mm (Irsyad)",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "crystal_ring": {"radius_mm": round(rr / S, 3), "centre_mm": mm((rcx, rcy)), "basis": "inner edge of the polished bezel"},
           "dial_edge_radius_mm": round(rd / S, 3)}

    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    # lug tips: where the silhouette steps in from the lugs to the bracelet (more than 1 mm between rows 0.25 mm apart)
    tips = [next(y for y in np.arange(18, 30, 0.25) if width[round(sy * (y + 0.25), 2)] < width[round(sy * y, 2)] - 1.0) + 0.125
            for sy in (1, -1)]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    out["bracelet_width_mm"] = {f"{y:+.0f}": round(width[y], 2) for y in (24, 28, 32, 36, 40, -24, -28, -32, -36, -40) if y in width}
    near = [width[y] for y in width if tips[0] + 0.5 <= y <= tips[0] + 2 or -tips[1] - 2 <= y <= -tips[1] - 0.5]
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "bracelet_past_lug_tips_mm": round(float(np.median(near)), 2), "listed": LISTED}

    # indices from radial profiles: lit run along each hour ray (the polished baton is brighter than the dial)
    idx = {}
    for hr in (1, 2, 4, 5, 7, 8, 9, 10, 11):
        p = [g[int(at(r, hr * 30)[1]), int(at(r, hr * 30)[0])] for r in range(700, 1130)]
        lit = [i for i, v in enumerate(p) if v > 170]
        runs, s = [], lit[0]
        for a_, b_ in zip(lit, lit[1:] + [None]):
            if b_ != a_ + 1:
                runs.append((s, a_))
                s = b_
        r0, r1 = max(runs, key=lambda t: t[1] - t[0])
        idx[str(hr)] = {"inner": round((700 + r0) / S, 3), "outer": round((700 + r1) / S, 3)}
    long_ = [v for hr, v in idx.items() if hr != "3"]
    out["indices"] = {"per_hour_mm": idx,
                      "inner_mm": round(float(np.median([v["inner"] for v in long_])), 3),
                      "outer_mm": round(float(np.median([v["outer"] for v in long_])), 3),
                      "short_inner_mm": round((M["index_3_x_px"][0] - px0) / S, 3), "short_outer_mm": round((M["index_3_x_px"][1] - px0) / S, 3),
                      "width_outer_mm": round(M["index_width_px"][0] / S, 3), "width_inner_mm": round(M["index_width_px"][1] / S, 3),
                      "short_width_mm": round(M["short_index_width_px"] / S, 3),
                      "layout": "applied polished faceted batons, wide at the outer end, at 1 2 4 5 7 8 10 11; long at 9 too; a short baton at 3 outside the date; applied 12 and 6"}

    hands = {}
    for name in ("hour", "minute"):
        r, a = polar(M[f"{name}_hand_tip"])
        lit0, lit1 = M[f"{name}_hand_lit_facet_px"]
        hands[name] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M[f"{name}_hand_tail_end"])[0],
                       "half_width_root_mm": round(lit0 / S, 3), "half_width_tip_mm": round(lit1 / S, 3),
                       "tail_half_width_mm": round(M[f"{name}_hand_tail_width_px"] / 2 / S, 3)}
    r, a = polar(M["seconds_hand_tip"])
    wn, wc = M["seconds_hand_width_px"]
    hands["seconds"] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M["seconds_hand_tail_end"])[0],
                        "half_width_mm": round(wn / 2 / S, 3), "tail_half_width_mm": round(wc / 2 / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k in ("date_window", "logo_seiko", "numeral_12", "numeral_6", "crown_box"):
        out[k] = box(M[k])

    # applied 12 and 6: bright polished plates, the 6's loop is a hole showing the dial
    for k in ("numeral_12", "numeral_6"):
        x0, y0, x1, y1 = M[k]
        pad = 12
        crop = (gray[y0 - pad:y1 + pad, x0 - pad:x1 + pad] > 130).astype(np.uint8) * 255
        crop = cv2.morphologyEx(crop, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(crop)
        keep = [i for i in range(1, n) if st[i, 4] > 1500]  # the digits, not stray dial highlights
        crop = np.isin(lab, keep).astype(np.uint8) * 255
        n, lab, st, _ = cv2.connectedComponentsWithStats(255 - crop)  # fill specks of dark facet inside the digits; keep the 6's loop
        crop[np.isin(lab, [i for i in range(1, n) if st[i, 4] < 1500])] = 255
        up = cv2.GaussianBlur(cv2.resize(crop, None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR), (0, 0), UP * 0.45)
        to_mm = lambda p, x0=x0, y0=y0: [round((p[0] / UP + x0 - pad - px0) / S, 3), round(-(p[1] / UP + y0 - pad - py0) / S, 3)]
        out[k + "_shapes"] = shapes_from_mask((up > 128).astype(np.uint8) * 255, to_mm, 300)

    # bracelet: joints and column widths
    j = M["bracelet_joints_y"]
    pitch = [(a - b) / S for js in j.values() for a, b in zip(js[1:], js[:-1])]
    out["bracelet_pitch_mm"] = round(float(np.median(pitch)), 3)
    out["bracelet_joints_mm"] = {k: [round(abs(y - py0) / S, 3) for y in v] for k, v in j.items()}
    shift = [abs(o - c) / S for o, c in ((j["top_centre"][1], j["top_outer"][0]), (j["bottom_centre"][1], j["bottom_outer"][1]),
                                         (j["bottom_centre"][2], j["bottom_outer"][2]))]
    out["bracelet_centre_joint_shift_mm"] = round(float(np.mean(shift)), 3)
    rows = M["bracelet_rows"]
    out["bracelet_centre_half_mm"] = round(float(np.mean([(c[1] - c[0]) / 2 / S for c in rows["centre"]])), 3)
    out["bracelet_groove_half_mm"] = round(float(np.mean([(gv[1] - gv[0]) / 2 / S for gv in rows["grooves"]])), 3)

    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for r_ in (case_r, rr, rd):
            cv2.circle(ov, (int(ccx), int(ccy)), int(r_), (0, 0, 255), 3)
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
        for k in ("date_window", "logo_seiko", "numeral_12", "numeral_6", "crown_box"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 3)
        for k in ("numeral_12_shapes", "numeral_6_shapes"):
            for sh in out[k]:
                for lp in [sh["outer"]] + sh["holes"]:
                    cv2.polylines(ov, [np.array([P(p) for p in lp], np.int32)], True, (255, 255, 0), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "crystal_ring", "dial_edge_radius_mm", "lug_tip_mm", "checks",
                                           "indices", "hands", "bracelet_pitch_mm", "bracelet_centre_joint_shift_mm",
                                           "bracelet_centre_half_mm", "bracelet_groove_half_mm")}, default=float), "->", dest)
