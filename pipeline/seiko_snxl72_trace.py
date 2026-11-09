"""Measure the Seiko 5 SNXL72K1 front photo, straightened by pipeline/seiko_snxl72_rectify.py, into mm. Host-side, numpy +
OpenCV, no Blender.

    python3 -B -m pipeline.seiko_snxl72_rectify          # first: outputs/watches/seiko-snxl72k1/front_rectified.png
    python3 -B -m pipeline.seiko_snxl72_trace [out.json] [overlay.png]     # default config/watches/seiko-snxl72k1-trace.json

Same method as pipeline/seiko_snkk22_trace.py. Anchor: case width on the left flank = 37.0 mm (spec sheet; the right flank
shows the case side because the photo is turned, so only the left half and the 12/6 ends are fitted); the listed 19 mm lug width
is reported as a check. mm, x right, y toward 12, origin = hand pivot. Hands, day-date, logo, crown come from gridded crops
(MANUAL_PX, +-3 px = +-0.1 mm); ring and index radii from radial profiles (black inlay of the batons). The bracelet is read on
the original photo (the straightening skews it) at its own scale, the same as the rectified one vertically.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "outputs/watches/seiko-snxl72k1/front_rectified.png"
OUT = ROOT / "config/watches/seiko-snxl72k1-trace.json"
CASE_MM = 37.0  # owner's spec sheet, 2026-11-09 (listings agree)
LUG_WIDTH_MM = 19.0  # spec sheet
HOURS = (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12)  # the day-date replaces 3

MANUAL_PX = {
    "hand_pivot": [994, 1000],
    # hour and minute: black batons with a lume insert, pointed ends (90 deg apex), a short polished base at the hub
    "hour_hand_tip": [806, 859],  # apex
    "hour_hand_tail_end": [1012, 1018],
    "hour_hand_lume": [[935, 950], [838, 885]],
    "hour_hand_half_width_px": 18,
    "minute_hand_tip": [1274, 767],  # apex
    "minute_hand_tail_end": [978, 1016],
    "minute_hand_lume": [[1060, 935], [1250, 790]],
    "minute_hand_half_width_px": 15,
    "hand_base_px": 75,  # polished base from the hub out to here, before the black blade
    "hand_tail_half_width_px": 12,
    "seconds_hand_tip": [755, 724],
    "seconds_hand_tail_end": [1073, 1090],
    "seconds_hand_half_width_px": [4, 6],  # needle, tail
    "hub_radius_px": [22, 8],  # black hub, grey centre
    "daydate_frame": [1140, 955, 1375, 1050],  # raised gold frame round both windows
    "daydate_window": [1155, 968, 1365, 1038],
    "logo_seiko": [912, 765, 1095, 800],
    "logo_5_shield": [953, 812, 1050, 870],
    "print_automatic_21_jewels": [922, 1182, 1082, 1205],  # AUTOMATIC only on this dial
    "print_6": [930, 1360, 1110, 1375],  # 7S26 calibre print
    "crown_box": [1515, 1160, 1565, 1275],  # fluted crown at about 4 o'clock
    "index_width_px": {"12": 35, "6": 35, "9": 35},  # wide batons; the rest are thin
    "index_single_px": [13, 7],  # thin baton: gold frame, black inlay
    "index_inlay_px": 20,  # wide batons
    # bracelet on the original photo (y = 1660-1720 next to the case): top surface edges, centre column
    "bracelet_row_orig": {"edges": [715, 1300], "centre": [873, 1126]},
    # first outer joints next to the case (original photo), above and below
    "bracelet_joints_y": {"outer_top": [282, 394], "outer_bottom": [1634, 1739]},
}
ARTEFACTS = ["bright arcs on the polished bezel and case: reflections, not shape",
             "straightened from a photo turned toward the crown: bezel, case and bracelet stand off the dial plane and keep some parallax; the right flank shows the case side",
             "the hands stand above the dial: their pivot sits about 5 px left of the dial centre after straightening"]


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
    for a in list(np.arange(242, 298.1, 1.0)):  # left flank only: the right one shows the case side
        rs = np.arange(450, 650, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    # crystal ring: the black gasket band inside the gold bezel; rays between the indices, skipping the day-date and crown side
    ring = []
    for a in np.arange(0, 360, 1.0):
        if 70 <= a <= 125 or abs((a + 15) % 30 - 15) < 9:
            continue
        prof = [g[int(at(r, a)[1]), int(at(r, a)[0])] for r in np.arange(400, 450, 0.5)]
        ring.append(at(400 + 0.5 * int(np.argmin(prof)), a))
    rcx, rcy, rr = fit_circle(np.array(ring))
    ccx, ccy = rcx, rcy  # a 56 deg arc cannot fix a centre: the case is concentric with the crystal ring
    case_r = float(np.median(np.hypot(*(np.array(edge) - (ccx, ccy)).T)))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width on the flanks = {CASE_MM} mm (spec sheet); lug width {LUG_WIDTH_MM} mm (spec sheet) as a check",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "crystal_ring": {"radius_mm": round(rr / S, 3), "centre_mm": mm((rcx, rcy)), "basis": "dark gasket line inside the gold bezel"}}

    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                l_ = round((xs.min() - ccx) / S, 3)  # left side mirrored: the right side shows the case flank
                prof.append([round(float(y_mm), 2), l_, -l_])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    tips = [next(y for y in np.arange(15, 30, 0.25) if width[round(sy * (y + 0.25), 2)] < width[round(sy * y, 2)] - 1.0) + 0.125
            for sy in (1, -1)]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    near = [width[y] for y in width if tips[0] + 0.5 <= y <= tips[0] + 3 or -tips[1] - 3 <= y <= -tips[1] - 0.5]
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "bracelet_past_lug_tips_mm": round(float(np.median(near)), 2),
                     "listed_lug_width_mm": LUG_WIDTH_MM}

    # indices: longest dark run along each hour ray (the black inlay of each gold baton); widths from gridded crops
    idx = {}
    for hr in HOURS:
        p = [min(g[int(at(r, hr * 30 + d)[1]), int(at(r, hr * 30 + d)[0])] for d in np.arange(-2, 2.1, 0.5))  # parallax: +-2 deg
             for r in range(220, 400)]
        lit = [i for i, v in enumerate(p) if v < 90]
        runs, s = [], lit[0]
        for a_, b_ in zip(lit, lit[1:] + [None]):
            if b_ is None or b_ > a_ + 3:  # small gaps: the dark facet of the ridge
                runs.append((s, a_))
                s = b_
        r0, r1 = max(runs, key=lambda t: t[1] - t[0])
        idx[str(hr)] = {"inner": round((220 + r0) / S, 3), "outer": round((220 + r1) / S, 3)}
    out["indices"] = {"per_hour_mm": idx,
                      "inner_mm": round(float(np.median([v["inner"] for k, v in idx.items() if k != "12"])), 3),
                      "outer_mm": round(float(np.median([v["outer"] for k, v in idx.items() if k != "12"])), 3),
                      "width_mm": round(M["index_single_px"][0] / S, 3), "inlay_width_mm": round(M["index_single_px"][1] / S, 3),
                      "wide_mm": {k: round(v / S, 3) for k, v in M["index_width_px"].items()},
                      "wide_inlay_mm": round(M["index_inlay_px"] / S, 3),
                      "layout": "applied polished gold batons with a black inlay; wide at 12, 6 and 9; none at 3 (day-date); lume dots on the dial edge stay in the dial map"}

    hands = {}
    for name in ("hour", "minute"):
        r, a = polar(M[f"{name}_hand_tip"])
        hands[name] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M[f"{name}_hand_tail_end"])[0],
                       "half_width_mm": round(M[f"{name}_hand_half_width_px"] / S, 3), "broad_tail_half_width_mm": round(M["hand_tail_half_width_px"] / S, 3), "base_mm": round(M["hand_base_px"] / S, 3),
                       "lume_from_to_mm": sorted(polar(p)[0] for p in M[f"{name}_hand_lume"])}
    r, a = polar(M["seconds_hand_tip"])
    wn, wc = M["seconds_hand_half_width_px"]
    hands["seconds"] = {"angle_deg": a, "length_mm": r, "tail_mm": polar(M["seconds_hand_tail_end"])[0],
                        "half_width_mm": round(wn / S, 3), "tail_half_width_mm": round(wc / S, 3)}
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    for k in ("daydate_frame", "daydate_window", "logo_seiko", "logo_5_shield", "print_automatic_21_jewels", "print_6", "crown_box"):
        out[k] = box(M[k])

    row = M["bracelet_row_orig"]
    c, hw = sum(row["edges"]) / 2, (row["edges"][1] - row["edges"][0]) / 2
    f = lambda x: round(abs(x - c) / hw, 3)
    out["bracelet_columns"] = {"centre_half": round((f(row["centre"][0]) + f(row["centre"][1])) / 2, 3),
                               "top_width_mm": round(2 * hw / S, 2),
                               "basis": "fractions of the bracelet half width, original photo next to the case"}
    j = M["bracelet_joints_y"]
    out["bracelet_pitch_mm"] = round(float(np.mean([(b - a) / S for a, b in j.values()])), 3)
    out["bracelet_centre_phase"] = 0.5  # photo: centre joints about half a row off the outer joints (0.54 below the case)
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
        for k in ("daydate_frame", "daydate_window", "logo_seiko", "logo_5_shield", "print_automatic_21_jewels", "print_6", "crown_box"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 3)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "crystal_ring", "lug_tip_mm", "checks", "indices", "hands",
                                           "bracelet_columns", "bracelet_pitch_mm", "bracelet_centre_phase")}, default=float), "->", dest)
