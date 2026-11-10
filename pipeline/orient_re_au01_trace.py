"""Measure the Orient Star RE-AU0108G / RE-AU0110N front photos into mm. Host-side, numpy + OpenCV, no Blender.

    python3 -B -m pipeline.orient_re_au01_trace <sku> [overlay.png]     # sku au0108g or au0110n
    -> config/watches/orient-re-<sku>-trace.json

Both watches are the same Contemporary power reserve model (38.5 mm case, F6N43) with a different dial colour, so the part
sizes read from gridded crops of the sharper RE-AU0110N photo are shared (SHARED_MM); each photo gives its own scale, pivot,
silhouette, lug tips and hand angles (MANUAL_PX on the 2x working copy, about +-5 px = +-0.1 mm). mm, x right, y toward 12,
origin = hand pivot. Anchor: case width on the flanks = 38.5 mm (orient-watch.com); check: gap between the lugs = 20 mm.
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
CASE_MM = 38.5
LISTED = {"lug_width_mm": 20.0, "lug_to_lug_mm": 46.9, "thickness_mm": 12.3}

PHOTOS = {
    "au0110n": {
        "front": "references/orient-re-au0110n/front_2x_2502x4164.png",
        "hand_pivot": [1197, 2075],
        "hour_hand_tip": [782, 1802],
        "minute_hand_tip": [1708, 1572],
        "seconds_hand_tip": [538, 1764],
        "pr_pivot": [1190, 1603],
        "pr_hand_tip": [1405, 1693],
        "lug_inner_x": [697, 1697],  # inner lug edges (gap between the lugs)
    },
    "au0108g": {
        "front": "references/orient-re-au0108g/front_2x_2370x4168.png",
        "hand_pivot": [1122, 1984],
        "hour_hand_tip": [722, 1735],
        "minute_hand_tip": [1480, 1530],  # a point on the hand's centre line (the tip fades into the 2 o'clock baton)
        "seconds_hand_tip": [588, 2465],
        "pr_pivot": [1124, 1527],
        "pr_hand_tip": [1340, 1612],
        "lug_inner_x": [643, 1603],
    },
}

# Read on the RE-AU0110N 2x copy (49.998 px/mm, pivot 1197, 2075) and converted; same parts on both watches.
SHARED_MM = {
    "crystal_ring_radius": 17.2,  # inner edge of the polished bezel (dark ring at 850-870 px)
    "dial_edge_radius": 16.2,  # dial flat ends, rehaut rises to the crystal ring
    "bezel_outer_radius": 19.0,  # wide polished sloped bezel 17.2 -> 19.0, thin case flank outside
    "hand_lengths": {"hour": 9.95, "minute": 14.4, "seconds": 14.6, "pr": 4.65},
    "hand_tails": {"hour": 3.0, "minute": 3.5, "seconds": 3.4},
    "hand_half_widths": {"hour": 0.78, "minute": 0.7, "neck": 0.35, "seconds": 0.06, "seconds_counterweight": 0.3, "pr": 0.2},
    "hub_radius": 0.55, "pr_cap_radius": 0.7,
    "indices": {"inner": 12.5, "outer": 14.5, "width": 1.2,
                "at_3": {"inner": 12.66, "outer": 14.76, "width": 2.2, "bars": 3},
                "at_9": {"inner": 10.74, "outer": 14.54, "width": 1.7, "bars": 2},
                "layout": "applied faceted batons with a ridge at 1 2 4 5 7 8 10 11; grooved blocks at 3 (beside the date) and 9; "
                          "applied XII and VI; printed lume dots at 15.2 mm"},
    # power reserve: applied polished crescent (print on it) around the subdial centre, 50 / 25 / 0 printed inside
    "pr_arc": {"centre": [-0.04, 9.12], "r_in": 4.95, "r_out": 6.15, "from_deg": 105, "to_deg": 255},
    "date_window": [8.06, -1.6, 12.06, 1.6],
    "pr_zero_box": [3.85, 6.5, 4.85, 7.9],
    "pr_print_boxes": [[-4.12, 7.22, -2.48, 8.22], [-0.76, 4.68, 0.78, 5.6], [3.85, 6.5, 4.85, 7.9]],  # 50, 25, 0  # printed 0 of the power reserve scale, touched by the hand tip
    "logo_box": [-4.9, -3.3, 4.9, -7.6],  # Orient Star emblem, ORIENTSTAR, AUTOMATIC
    "print_6_box": [-6.2, -12.9, 6.2, -14.0],  # JAPAN ... F6N4-UA00 TM 3
    # crown: fluted part 2146-2280 px, smooth end cap to 2303 px, 1916-2234 px tall, on the pivot row
    "crown": {"r_from": 19.0, "flute_to": 21.66, "cap_to": 22.12, "radius": 3.18, "cap_radius": 2.5},
    # bracelet (top half, 2x px 150-1000): three columns; a narrow polished rail between the brushed centre and outer links;
    # rail joints line up with the outer joints; centre joints sit about 1.3-1.6 mm nearer the case
    "bracelet": {"centre_half": 3.4, "rail": [3.55, 4.85], "pitch": 6.0, "centre_shift": 1.3,
                 "joints_px_top": {"outer": [330, 640, 950], "centre": [395, 720, 1000]},
                 "joints_px_bottom": {"outer": [3265, 3545, 3820], "centre": [3215, 3460, 3760]}},
}

# Roman numerals as strokes in mm (box read from gridded crops): serif bars, thick and thin diagonals, uprights.
NUMERALS = {
    "numeral_12": {"box": [-1.95, 10.85, 1.97, 14.53], "strokes": [
        ("bar", -1.9, 14.18, 1.95, 14.53), ("bar", -1.9, 10.85, 1.95, 11.2),
        ("line", -1.55, 14.2, 0.0, 11.2, 0.42), ("line", -0.35, 14.2, -1.75, 11.2, 0.16),
        ("bar", 0.17, 11.0, 0.8, 14.4), ("bar", 1.17, 11.0, 1.8, 14.4)]},
    "numeral_6": {"box": [-1.59, -14.57, 1.63, -11.09], "strokes": [
        ("bar", -1.59, -11.37, 0.55, -11.09), ("bar", 0.5, -11.37, 1.63, -11.09), ("bar", 0.5, -14.57, 1.63, -14.3),
        ("line", -1.1, -11.3, -0.05, -14.5, 0.48), ("line", 0.25, -11.3, -0.18, -14.5, 0.16),
        ("bar", 0.75, -14.4, 1.38, -11.2)]},
}

ARTEFACTS = ["bright arcs on the polished bezel and crystal: reflections, not shape",
             "the bracelet sits about 0.7 mm right of the pivot (watch slightly turned): the build centres it",
             "RE-AU0108G: case centre about 0.4 mm below the pivot in the photo (camera a little low); the build keeps the pivot centred"]


def numeral_shapes(spec, res=0.01):
    """Rasterise the strokes (mm) at res mm/px and return outlines with holes in mm."""
    x0, y0, x1, y1 = spec["box"]
    pad = 0.2
    w, h = int((x1 - x0 + 2 * pad) / res), int((y1 - y0 + 2 * pad) / res)
    m = np.zeros((h, w), np.uint8)
    P = lambda x, y: (int(round((x - x0 + pad) / res)), int(round((y1 + pad - y) / res)))
    for s in spec["strokes"]:
        if s[0] == "bar":
            cv2.rectangle(m, P(s[1], s[4]), P(s[3], s[2]), 255, -1)
        else:
            _, xa, ya, xb, yb, wd = s
            dx, dy = xb - xa, yb - ya
            n = math.hypot(dx, dy)
            ox, oy = -dy / n * wd / 2, dx / n * wd / 2
            poly = np.array([P(xa + ox, ya + oy), P(xb + ox, yb + oy), P(xb - ox, yb - oy), P(xa - ox, ya - oy)], np.int32)
            cv2.fillPoly(m, [poly], 255)
    m[: int(pad / res)] = m[-int(pad / res):] = 0
    # clip to the box (diagonals poke out past the serif bars)
    a, b = P(x0, y1), P(x1, y0)
    clip = np.zeros_like(m)
    clip[a[1]:b[1] + 1, a[0]:b[0] + 1] = 1
    m = m * clip
    to_mm = lambda p: [round(p[0] * res + x0 - pad, 3), round(y1 + pad - p[1] * res, 3)]
    return shapes_from_mask(m, to_mm, 50)


def trace(sku, overlay=None):
    ph = PHOTOS[sku]
    path = ROOT / ph["front"]
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    px0, py0 = ph["hand_pivot"]
    at = lambda r, a: (px0 + r * math.sin(math.radians(a)), py0 - r * math.cos(math.radians(a)))

    # case outline on the flanks only: lugs flare out above 70 / below 110 deg, the crown sits at 80-100 deg
    edge = []
    for a in list(np.arange(72, 79, 1.0)) + list(np.arange(102, 109, 1.0)) + list(np.arange(246, 295, 1.0)):
        rs = np.arange(800, 1150, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    ccx, ccy, case_r = fit_circle(np.array(edge))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    polar = lambda p: (round(math.hypot(*mm(p)), 3), round(math.degrees(math.atan2(*mm(p))) % 360, 2))
    out = {"source": ph["front"], "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width on the flanks = {CASE_MM} mm (orient-watch.com)",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))}}
    out.update({k: v for k, v in SHARED_MM.items()})
    out["crystal_ring"] = {"radius_mm": SHARED_MM["crystal_ring_radius"]}
    out["dial_edge_radius_mm"] = SHARED_MM["dial_edge_radius"]

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
    out["bracelet_width_mm"] = {f"{y:+.0f}": round(width[y], 2) for y in (24, 28, 32, 36, -24, -28, -32, -36) if y in width}
    gap = (ph["lug_inner_x"][1] - ph["lug_inner_x"][0]) / S
    out["lug_inner_x_mm"] = round(gap / 2, 3)
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "gap_between_lugs_mm": round(gap, 2), "listed": LISTED}

    hands = {}
    L, T, W = SHARED_MM["hand_lengths"], SHARED_MM["hand_tails"], SHARED_MM["hand_half_widths"]
    for name in ("hour", "minute", "seconds"):
        r, a = polar(ph[f"{name}_hand_tip"])
        hands[name] = {"angle_deg": a, "length_mm": L[name], "tail_mm": T[name], "half_width_mm": W[name]}
    hands["seconds"]["counterweight_half_width_mm"] = W["seconds_counterweight"]
    for name in ("hour", "minute"):
        hands[name]["neck_half_width_mm"] = W["neck"]  # narrow neck to 1.0 mm, step out at 1.4 mm, straight taper to the tip
    pr0 = mm(ph["pr_pivot"])
    dx, dy = (ph["pr_hand_tip"][0] - ph["pr_pivot"][0]) / S, -(ph["pr_hand_tip"][1] - ph["pr_pivot"][1]) / S
    hands["pr"] = {"pivot_mm": pr0, "angle_deg": round(math.degrees(math.atan2(dx, dy)) % 360, 2), "length_mm": L["pr"],
                   "half_width_mm": W["pr"], "measured_length_mm": round(math.hypot(dx, dy), 3)}
    out["hands"] = hands
    t = hands["hour"]["angle_deg"] / 30
    out["photo_time"] = "%d:%02d" % (int(t) or 12, round(hands["minute"]["angle_deg"] / 6) % 60)
    for k, v in NUMERALS.items():
        out[k] = {"x0_y0_x1_y1_mm": v["box"]}
        out[k + "_shapes"] = numeral_shapes(v)
    out["manual_px"] = ph
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(ccx), int(ccy)), int(case_r), (0, 0, 255), 2)
        for r_ in (SHARED_MM["crystal_ring_radius"], SHARED_MM["dial_edge_radius"], SHARED_MM["bezel_outer_radius"]):
            cv2.circle(ov, (px0, py0), int(r_ * S), (0, 0, 255), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 2, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 2, (0, 255, 0), -1)
        for name, hd in hands.items():
            if name == "pr":
                c0 = hd["pivot_mm"]
                tt = math.radians(hd["angle_deg"])
                cv2.line(ov, P(c0), P((c0[0] + hd["length_mm"] * math.sin(tt), c0[1] + hd["length_mm"] * math.cos(tt))), (0, 255, 255), 2)
                continue
            tt = math.radians(hd["angle_deg"])
            cv2.line(ov, P((-hd["tail_mm"] * math.sin(tt), -hd["tail_mm"] * math.cos(tt))),
                     P((hd["length_mm"] * math.sin(tt), hd["length_mm"] * math.cos(tt))), (0, 255, 255), 2)
        ix = SHARED_MM["indices"]
        for hr in range(1, 13):
            a = math.radians(hr * 30)
            r0, r1 = {3: (ix["at_3"]["inner"], ix["at_3"]["outer"]), 9: (ix["at_9"]["inner"], ix["at_9"]["outer"])}.get(hr, (ix["inner"], ix["outer"]))
            cv2.line(ov, P((r0 * math.sin(a), r0 * math.cos(a))), P((r1 * math.sin(a), r1 * math.cos(a))), (255, 0, 255), 2)
        pa = SHARED_MM["pr_arc"]
        for r_ in (pa["r_in"], pa["r_out"]):
            cv2.ellipse(ov, P(pa["centre"]), (int(r_ * S), int(r_ * S)), 0, pa["from_deg"] - 90, pa["to_deg"] - 90, (255, 255, 0), 2)
        for k in ("date_window", "logo_box", "print_6_box"):
            b = SHARED_MM[k]
            cv2.rectangle(ov, P(b[:2]), P(b[2:]), (0, 200, 255), 2)
        for k in NUMERALS:
            for sh in out[k + "_shapes"]:
                for lp in [sh["outer"]] + sh["holes"]:
                    cv2.polylines(ov, [np.array([P(p) for p in lp], np.int32)], True, (255, 255, 0), 1)
        cr = SHARED_MM["crown"]
        cv2.rectangle(ov, P((cr["r_from"], cr["radius"])), P((cr["flute_to"], -cr["radius"])), (0, 200, 255), 2)
        y = out["lug_tip_mm"]
        for yy in (y["top"], -y["bottom"]):
            cv2.line(ov, P((-12, yy)), P((12, yy)), (0, 128, 255), 2)
        for x in (-out["lug_inner_x_mm"], out["lug_inner_x_mm"]):
            cv2.line(ov, P((x, -26)), P((x, 26)), (0, 128, 255), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    sku = sys.argv[1]
    dest = ROOT / f"config/watches/orient-re-{sku}-trace.json"
    data = trace(sku, overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "lug_tip_mm", "lug_inner_x_mm", "checks", "hands",
                                           "photo_time", "bracelet_width_mm")}, default=float), "->", dest)
