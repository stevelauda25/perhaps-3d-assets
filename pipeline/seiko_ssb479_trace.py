"""Measure the Seiko SSB479P1 front photo (white background, 3165 x 4640) into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.seiko_ssb479_trace [out.json] [overlay.png]     # default config/watches/seiko-ssb479p1-trace.json

Same method as pipeline/seiko_sur419_trace.py. Anchor: case width on the flanks = 38.7 mm (listing, Irsyad 2026-11-06);
the listed 20 mm lug width is reported as a check. mm, x right, y toward 12, origin = case and dial centre (circle through
the flanks and the indices). The hand pivot in the photo sits 9 px (0.17 mm) left of it; hands are measured from the
pivot and placed on the origin. Hands, pushers, crown, rings and bracelet joints come from gridded crops (MANUAL_PX,
+-5 px = +-0.1 mm); index radii from radial profiles; subdials from the cream areas.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/seiko-ssb479p1/front_3165x4640.jpg"
OUT = ROOT / "config/watches/seiko-ssb479p1-trace.json"
CASE_MM = 38.7  # listing, Irsyad 2026-11-06
LISTED = {"lug_width_mm": 20.0, "thickness_mm": 12.6}

MANUAL_PX = {
    "hand_pivot": [1527, 2330],
    "hub_radius_px": [30, 13],  # polished hub ring, cap
    # hour and minute: silver swords with a cream lume strip; outlines as (along, half width) from the pivot in px
    "hour_tip": [1160, 2045],
    "hour_half_width_px": 27,
    "hour_lume_px": [[1197, 2088], [1448, 2283]],  # strip ends on the axis
    "hour_lume_half_width_px": 11,
    "hour_tail_end": [1650, 2430],
    "hour_tail_half_width_px": 25,
    "minute_tip": [2090, 1862],
    "minute_half_width_px": 22,
    "minute_lume_px": [[1985, 1960], [1610, 2272]],
    "minute_lume_half_width_px": 9,
    "minute_tail_end": [1420, 2438],
    "minute_tail_half_width_px": 24,
    # chronograph seconds: vertical needle down to the 6 index, tapered counterweight up to y 2085
    "chrono_tip": [1527, 3075],
    "chrono_tail_end": [1527, 2085],
    "chrono_half_width_px": [7, 15, 8],  # needle, counterweight end, counterweight at the hub
    "hand_point_px": {"hour": 63, "minute": 55},  # length of the pointed tip
    # rings (horizontal or vertical extremes, insert measured from its own centre: the bezel sits right of the dial centre)
    "insert_inner_lrtb": [660, 2440, 1445, 3215],
    "insert_outer_lr": [548, 2540],
    "dial_edge_px": 780,  # black dial ends, grey crystal wall begins (mean radius)
    "minute_track_outer_px": 745,
    # applied indices: widths across (12 is the wide one), lume strip at the outer end
    "index_width_px": {"12": 115, "other": 45},
    "index_lume_px": 20,
    "index_short": {"3": [2213, 2295], "9": [780, 885], "6": [3010, 3085]},  # beside the subdials: x (3, 9) or y (6) extent
    # crown and pushers (axes from the case centre)
    "crown_box": [2600, 2175, 2700, 2485],  # fluted part
    "pusher_upper_centre": [2560, 1745],
    "pusher_lower_centre": [2560, 2915],
    "pusher_cap_end_r_px": 1260,
    "date_window": [1880, 2740, 2040, 2820],
    # bracelet: brushed outer and centre links share joints; the polished narrow columns are shifted toward the case
    "bracelet_joints_y": {"top_wide": [1150, 910, 690], "top_polished": [1232, 1022, 790],
                          "bottom_wide": [3530, 3750, 3970, 4200], "bottom_polished": [3435, 3665, 3895, 4125]},
    "bracelet_columns_x": {"y1000": [1050, 1290, 1300, 1365, 1370, 1745, 1750, 1820, 1825, 2075],
                           "y3800": [1060, 1265, 1268, 1335, 1340, 1720, 1725, 1800, 1805, 2060]},
}
ARTEFACTS = ["the watch is turned slightly: the left flank shows 0.35 mm more than the right; widths are used, not one side",
             "the bezel insert sits 14 px (0.27 mm) right of the dial centre in the photo; the build maps it from its own centre",
             "the bracelet sits about 0.5 mm right of the dial centre; the build centres it",
             "subdial hands, the date window frame and all print stay in the photo map"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    g = cv2.GaussianBlur(gray, (0, 0), 2)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    M = MANUAL_PX

    # case width on the centre row: left edge from the row scan; right edge from rays between the pushers and the crown
    # (70-80 and 100-110 deg, first background pixel), which sit within 0.3 mm of the 90 deg radius
    hx, hy = M["hand_pivot"]
    rr_ = []
    for a in list(np.arange(70, 80.1, 1.0)) + list(np.arange(100, 110.1, 1.0)):
        t = math.radians(a)
        rs = np.arange(900, 1150, 0.5)
        xs, ys = hx + rs * math.sin(t), hy + rs * -math.cos(t)
        rr_.append(rs[np.nonzero(~fg[ys.astype(int), xs.astype(int)])[0][0]])
    x_right = hx + float(np.median(rr_))
    x_left = float(np.nonzero(fg[hy])[0].min())
    width_px = x_right - x_left
    S = width_px / CASE_MM
    px0, py0 = int(round((x_left + x_right) / 2)), hy
    at = lambda r, a: (px0 + r * math.sin(math.radians(a)), py0 - r * math.cos(math.radians(a)))
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width on the flanks = {CASE_MM} mm (listing)",
           "case": {"radius_mm": round(width_px / 2 / S, 3), "edges_px": [x_left, round(x_right, 1)]},
           "pivot_offset_mm": mm(M["hand_pivot"])}

    l, r_, t_, b_ = M["insert_inner_lrtb"]
    ol, or_ = M["insert_outer_lr"]
    icx, icy = (l + r_) / 2, (t_ + b_) / 2
    out["rings_mm"] = {"case": round(width_px / 2 / S, 3),
                       "insert_outer": round((or_ - ol) / 2 / S, 3),
                       "insert_inner": round(((r_ - l) + (b_ - t_)) / 4 / S, 3),
                       "dial_edge": round(M["dial_edge_px"] / S, 3),
                       "minute_track_outer": round(M["minute_track_outer_px"] / S, 3)}
    out["insert_centre_mm"] = mm((icx, icy))

    # silhouette per row (left and right edge, mm from the origin)
    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    left_x = {p[0]: -p[1] for p in prof}
    # lug tips: the rounded tip steps in over about 1 mm; take where the left edge passes halfway from lug (20 mm) to bracelet (26 mm)
    mid = lambda sy: (left_x[round(sy * 20.0, 2)] + left_x[round(sy * 26.0, 2)]) / 2
    tips = [next(y for y in np.arange(20, 26, 0.25) if left_x[round(sy * y, 2)] < mid(sy)) - 0.125 for sy in (1, -1)]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    rc = width_px / 2 / S
    leave = [next(y for y in np.arange(6, 18, 0.25) if left_x[round(sy * y, 2)] > math.sqrt(max(rc * rc - y * y, 0)) + 0.1) for sy in (1, -1)]
    out["lug_leaves_case_y_mm"] = {"top": leave[0], "bottom": leave[1], "mean": round(sum(leave) / 2, 3)}
    near = [width[y] for y in width if tips[0] + 0.5 <= y <= tips[0] + 2 or -tips[1] - 2 <= y <= -tips[1] - 0.5]
    out["bracelet_width_mm"] = {f"{y:+.0f}": round(width[y], 2) for y in (24, 28, 32, 36, 40, -24, -28, -32, -36, -40) if y in width}
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "bracelet_past_lug_tips_mm": round(float(np.median(near)), 2), "listed": LISTED}

    # indices: bright run along each hour ray (polished baton and its lume strip)
    idx = {}
    for hr in range(1, 13):
        p = [g[int(at(r, hr * 30)[1]), int(at(r, hr * 30)[0])] for r in range(450, 800)]
        lit = [i for i, v in enumerate(p) if v > 150]
        runs, s = [], lit[0]
        for a_, b_ in zip(lit, lit[1:] + [None]):
            if b_ != a_ + 1:
                runs.append((s, a_))
                s = b_
        r0, r1 = max(runs, key=lambda t: t[1] - t[0])
        idx[str(hr)] = {"inner": round((450 + r0) / S, 3), "outer": round((450 + r1) / S, 3)}
    sh = M["index_short"]
    idx["3"] = {"inner": round((sh["3"][0] - px0) / S, 3), "outer": round((sh["3"][1] - px0) / S, 3)}
    idx["9"] = {"inner": round((px0 - sh["9"][1]) / S, 3), "outer": round((px0 - sh["9"][0]) / S, 3)}
    idx["6"] = {"inner": round((sh["6"][0] - py0) / S, 3), "outer": round((sh["6"][1] - py0) / S, 3)}
    out["indices"] = {"per_hour_mm": idx, "width_12_mm": round(M["index_width_px"]["12"] / S, 3),
                      "width_mm": round(M["index_width_px"]["other"] / S, 3), "lume_mm": round(M["index_lume_px"] / S, 3),
                      "layout": "applied polished batons with a cream lume strip at the outer end; wide at 12; short at 3, 6, 9 beside the subdials"}

    # subdials: cream discs (bright, warm) inside the dial
    b, gg, rr = (im[..., k].astype(int) for k in range(3))
    cream = ((rr > 200) & (rr - b > 12) & (rr < 250)).astype(np.uint8)
    yy, xx = np.mgrid[0:h, 0:w]
    cream &= (np.hypot(xx - px0, yy - py0) < 14 * S).astype(np.uint8)
    cream = cv2.morphologyEx(cream, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(cream)
    subs = {}
    for i in range(1, n):
        if st[i, 4] > 50000:
            x, y = mm(cen[i])
            name = "9" if x < -3 else "3" if x > 3 else "6"
            subs[name] = {"centre_mm": [x, y], "radius_mm": round(math.sqrt(st[i, 4] / math.pi) / S, 3)}
    out["subdials"] = subs

    # hands, measured from the pivot, placed on the origin
    piv = np.array(M["hand_pivot"], float)
    def polar(p):
        v = np.array(p, float) - piv
        return round(float(np.hypot(*v)) / S, 3), round(math.degrees(math.atan2(v[0], -v[1])) % 360, 2)
    hands = {}
    for name in ("hour", "minute"):
        L, a = polar(M[name + "_tip"])
        hands[name] = {"angle_deg": a, "length_mm": L, "half_width_mm": round(M[name + "_half_width_px"] / S, 3),
                       "lume_from_to_mm": sorted(polar(p)[0] for p in M[name + "_lume_px"]),
                       "lume_half_width_mm": round(M[name + "_lume_half_width_px"] / S, 3),
                       "tail_mm": polar(M[name + "_tail_end"])[0], "tail_half_width_mm": round(M[name + "_tail_half_width_px"] / S, 3)}
    L, a = polar(M["chrono_tip"])
    hands["chrono"] = {"angle_deg": a, "length_mm": L, "tail_mm": polar(M["chrono_tail_end"])[0],
                       "half_width_mm": [round(v / S, 3) for v in M["chrono_half_width_px"]]}
    # outlines in mm about the pivot, already turned to the photo's time (the build puts the pivot on the origin)
    turn = lambda pts, deg: [[round(x * math.cos(math.radians(deg)) + y * math.sin(math.radians(deg)), 4),
                              round(-x * math.sin(math.radians(deg)) + y * math.cos(math.radians(deg)), 4)] for x, y in pts]
    for name in ("hour", "minute"):
        hd = hands[name]
        L, w, tail, tw = hd["length_mm"], hd["half_width_mm"], hd["tail_mm"], hd["tail_half_width_mm"]
        pt = M["hand_point_px"][name] / S
        hd["outline_mm"] = turn([(-tw, -tail), (tw, -tail), (tw, 0), (w, 0), (w, L - pt), (0, L), (-w, L - pt), (-w, 0), (-tw, 0)], hd["angle_deg"])
        a, b_ = hd["lume_from_to_mm"]
        lw = hd["lume_half_width_mm"]
        hd["lume_mm"] = turn([(-lw, a), (lw, a), (lw, b_), (-lw, b_)], hd["angle_deg"])
    hd = hands["chrono"]
    nw, ew, rw = hd["half_width_mm"]
    L, tail = hd["length_mm"], hd["tail_mm"]
    hd["outline_mm"] = turn([(-rw, 0), (-ew, -tail), (ew, -tail), (rw, 0), (nw, 0), (nw, L - 0.3), (0, L), (-nw, L - 0.3), (-nw, 0)], hd["angle_deg"])
    out["hands"] = hands
    out["hub_radius_mm"] = [round(v / S, 3) for v in M["hub_radius_px"]]

    box = lambda bx: {"x0_y0_x1_y1_mm": mm(bx[:2]) + mm(bx[2:]), "size_mm": [round((bx[2] - bx[0]) / S, 3), round((bx[3] - bx[1]) / S, 3)],
                      "centre_mm": mm(((bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2))}
    out["crown_box"] = box(M["crown_box"])
    out["date_window"] = box(M["date_window"])
    pushers = {}
    for k in ("upper", "lower"):
        x, y = mm(M[f"pusher_{k}_centre"])
        pushers[k] = {"angle_deg": round(math.degrees(math.atan2(x, y)) % 360, 2)}
    out["pushers"] = pushers
    out["pusher_cap_end_r_mm"] = round(M["pusher_cap_end_r_px"] / S, 3)

    # bracelet: pitch, polished joint shift, column split as fractions of the half width
    j = M["bracelet_joints_y"]
    pitch = [abs(a - b_) / S for js in j.values() for a, b_ in zip(js[1:], js[:-1])]
    out["bracelet_pitch_mm"] = round(float(np.median(pitch)), 3)
    out["bracelet_joints_mm"] = {k: [round(abs(y - py0) / S, 3) for y in v] for k, v in j.items()}
    jm = out["bracelet_joints_mm"]
    shift = [w_ - p_ for w_, p_ in zip(jm["top_wide"], jm["top_polished"])] + [w_ - p_ for w_, p_ in zip(jm["bottom_wide"], jm["bottom_polished"])]
    out["bracelet_polished_joint_shift_mm"] = round(float(np.mean(shift)), 3)
    fr = []
    for xs in M["bracelet_columns_x"].values():
        c, hw = (xs[0] + xs[-1]) / 2, (xs[-1] - xs[0]) / 2
        fr.append([(xs[5] - xs[4]) / 2 / hw, ((xs[7] - xs[2]) / 2 + 0) / hw])
    out["bracelet_column_fractions"] = {"centre_half": round(float(np.mean([f[0] for f in fr])), 3),
                                        "polished_outer": round(float(np.mean([f[1] for f in fr])), 3)}

    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for k, rad in out["rings_mm"].items():
            cv2.circle(ov, (px0, py0), int(rad * S), (0, 0, 255), 2)
        for y_mm, l_, r2 in prof:
            cv2.circle(ov, P((l_, y_mm)), 3, (0, 255, 0), -1)
            cv2.circle(ov, P((r2, y_mm)), 3, (0, 255, 0), -1)
        for name, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            pv = (piv[0], piv[1])
            q = lambda r: (int(pv[0] + r * S * math.sin(t)), int(pv[1] - r * S * math.cos(t)))
            cv2.line(ov, q(-hd["tail_mm"]), q(hd["length_mm"]), (0, 255, 255), 3)
        for hr, v in idx.items():
            t = math.radians(int(hr) * 30)
            for r2 in (v["inner"], v["outer"]):
                cv2.circle(ov, P((r2 * math.sin(t), r2 * math.cos(t))), 8, (255, 0, 255), 3)
        for s_ in subs.values():
            cv2.circle(ov, P(s_["centre_mm"]), int(s_["radius_mm"] * S), (255, 255, 0), 3)
        for k in ("crown_box", "date_window"):
            bx = M[k]
            cv2.rectangle(ov, tuple(bx[:2]), tuple(bx[2:]), (0, 200, 255), 3)
        for y in (tips[0], -tips[1]):
            cv2.line(ov, P((-12, y)), P((12, y)), (0, 128, 255), 3)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "origin_px", "case", "pivot_offset_mm", "rings_mm", "insert_centre_mm",
                                           "lug_tip_mm", "lug_leaves_case_y_mm", "checks", "bracelet_width_mm", "indices", "subdials", "hands",
                                           "pushers", "crown_box", "bracelet_pitch_mm", "bracelet_joints_mm",
                                           "bracelet_polished_joint_shift_mm", "bracelet_column_fractions")}, default=float, indent=0), "->", dest)
