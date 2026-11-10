"""Measure the Hamilton H82405130 (Khaki Navy Scuba Auto 40 mm) front photo (1840 x 3200) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.hamilton_h82405130_trace [out.json] [overlay.png]   # default config/watches/hamilton-h82405130-trace.json

Same method as pipeline/orient_ra_aa0818l19b_trace.py. Anchor: 40 mm case (bezel) width across 3 and 9 (listing); the listed
20 mm lug width is reported as a check. mm, x right, y toward 12, origin = hand pivot. Hands, indices, date window, crown and
bracelet joints come from gridded and hand-aligned crops (MANUAL_PX, +-2 px = +-0.05 mm). The red aluminium insert's white
prints are traced by threshold and become geometry; the 13-24 numerals, minute track, logo and prints stay in the dial map.
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
FRONT = ROOT / "references/hamilton-h82405130/front_1840x3200.jpg"
OUT = ROOT / "config/watches/hamilton-h82405130-trace.json"
CASE_MM = 40.0  # listing: case width; the coin-edge bezel is the widest part at 3 and 9
LISTED = {"lug_width_mm": 20.0, "thickness_mm": 12.95}

MANUAL_PX = {
    "hand_pivot": [848, 1643],
    # hour: tapered baton, polished outline, lume; flat tip. Short outlined tail with a black fill
    "hour_hand": {"angle_deg": 303.5, "length": 312, "root": [45, 30], "tip_half": 17, "tail": [75, 14, 22]},
    # minute: tapered baton, rounded tip; a black slot over the left half near the root
    "minute_hand": {"angle_deg": 54.5, "length": 508, "root": [45, 25], "tip_half": 12.5, "tail": [75, 13, 20],
                    "slot": [45, 160]},
    # seconds: black needle with a polished edge, red frame around a white lume teardrop, red pointer to the tip
    "seconds_hand": {"angle_deg": 228.8, "length": 535, "half": 10, "tail": 90, "arrow": [290, 18, 425, 6],
                     "lume": [300, 13, 410], "pointer_half": 3},
    "hub_radius_px": [24, 10],  # collar, cap
    "outline_px": 4,  # polished hand edge
    # applied indices: polished frame around lume. 12 / 3 / 6 / 9 trapezoids, wide end out; bars elsewhere
    "wedge_px": {"r": [395, 542.5], "half": [17.1, 54.8]},
    "bar_px": {"r": [422.5, 543.5], "half": 15.5},
    "frame_px": 5,
    "date_window": [[1114, 1842], [1190, 1916], [1130, 1970], [1060, 1896]],  # corners of the white window (4:30)
    "logo": [640, 1335, 1055, 1475],  # star emblem and HAMILTON
    "print_khaki": [705, 1750, 985, 1848],
    "print_swiss_made": [690, 2140, 1060, 2200],
    "crown_box": [1585, 1515, 1710, 1772],  # case edge to the end of the fluted crown
    "bezel_notch_count": 96,  # coin-edge scallops, about 48 px apart at the rim
    "bezel_rings_px": {"dial_out": 556, "lip_in": 568, "insert_in": 582, "rim_out": 750},  # about the bezel centre; insert_out is fitted
    # bracelet: three columns; the centre links (with polished chamfered ends) are shorter than the outer ones
    "bracelet_joints_y": {"top_outer": [714, 500, 291], "top_centre": [777, 604, 409, 218],
                          "bottom_outer": [2561, 2965], "bottom_centre": [2506, 2667, 2853, 3018]},
    "bottom_outer_rows": 2,  # 2561 to 2965 spans two links
    "bracelet_centre_px": [[652, 1040], [658, 1060]],
    "end_link_x_px": [474, 1215],
}
ARTEFACTS = ["the photo is 1840 x 3200 at about 37.7 px/mm: hand and index edges are +-2 px",
             "the right facet of the hour and minute hands reflects black; widths are taken from the lit side, centred on the pivot",
             "the photo is turned about 0.3 deg counter-clockwise (12 / 6 and 3 / 9 indices); not corrected"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(float)
    fg = (765 - im.astype(int).sum(2)) > 30
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a, c=(px0, py0): (c[0] + r * math.sin(math.radians(a)), c[1] - r * math.cos(math.radians(a)))

    # bezel outline on the flanks (the lugs leave it above 60 / below 120 deg; the crown sits at 75-105 deg)
    edge = []
    for a in list(np.arange(50, 68.1, 1.0)) + list(np.arange(112, 130.1, 1.0)) + list(np.arange(232, 308.1, 1.0)):
        rs = np.arange(680, 800, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    ccx, ccy, case_r = fit_circle(np.array(edge))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    # bezel centre and insert outer edge: end of the saturated red along rays, outliers (glare) dropped
    sat = hsv[..., 1]
    pts = []
    for a in np.arange(0, 360, 1.0):
        rs = np.arange(640, 740, 0.5)
        xs, ys = (np.array(v).astype(int) for v in at(rs, a))
        red = sat[ys, xs] > 110
        k = next((i for i in range(1, len(rs) - 12) if red[i - 1] and not red[i:i + 12].any()), None)
        if k:
            pts.append((xs[k], ys[k]))
    pts = np.array(pts, float)
    keep = np.ones(len(pts), bool)
    for _ in range(6):
        bcx, bcy, ins_r = fit_circle(pts[keep])
        d = np.abs(np.hypot(pts[:, 0] - bcx, pts[:, 1] - bcy) - ins_r)
        keep = d < max(2.5, 2 * np.percentile(d[keep], 60))
    rg = dict(M["bezel_rings_px"], insert_out=round(float(ins_r), 1))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width = {CASE_MM} mm (listing)",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "bezel_offset_mm": mm((bcx, bcy)), "bezel_rings_mm": {k: round(v / S, 3) for k, v in rg.items()},
           "insert_edge_fit": {"centre_px": [round(float(bcx), 1), round(float(bcy), 1)], "points": int(keep.sum()), "of": len(pts)},
           "bezel_notches": {"count": M["bezel_notch_count"], "basis": "coin-edge scallops about 48 px apart at the rim"}}

    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot(xx - bcx, yy - bcy)
    band = (rr > rg["insert_in"] + 6) & (rr < rg["insert_out"] - 4)
    white = (hsv[..., 1] < 60) & (hsv[..., 2] > 150)
    out["insert_srgb"] = [round(float(v) / 255, 3) for v in np.median(im[band & ~white & (sat > 110)][:, ::-1], 0)]

    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    tips = [next(y for y in np.arange(20, 30, 0.25) if width[round(sy * (y + 0.25), 2)] < width[round(sy * y, 2)] - 1.0) + 0.125
            for sy in (1, -1)]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    out["bracelet_width_mm"] = {f"{y:+.0f}": round(width[y], 2) for y in (28, 32, 36, 40, -28, -32, -36, -40) if y in width}
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "end_link_width_mm": round((M["end_link_x_px"][1] - M["end_link_x_px"][0]) / S, 2),
                     "listed": LISTED}

    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    f = lambda v: round(v / S, 3)
    wd, br_ = M["wedge_px"], M["bar_px"]
    out["indices"] = {"wedge_r_mm": [f(v) for v in wd["r"]], "wedge_half_mm": [f(v) for v in wd["half"]],
                      "bar_r_mm": [f(v) for v in br_["r"]], "bar_half_mm": f(br_["half"]), "frame_mm": f(M["frame_px"]),
                      "layout": "applied polished frames with lume: trapezoids at 12 3 6 9 (lume sizes), bars at the other hours"}
    hands = {}
    for name in ("hour", "minute"):
        hm = M[name + "_hand"]
        hands[name] = {"angle_deg": hm["angle_deg"], "length_mm": f(hm["length"]), "root_mm": [f(v) for v in hm["root"]],
                       "tip_half_mm": f(hm["tip_half"]), "tail_mm": [f(v) for v in hm["tail"]]}
        if "slot" in hm:
            hands[name]["slot_mm"] = [f(v) for v in hm["slot"]]
    sm = M["seconds_hand"]
    hands["seconds"] = {"angle_deg": sm["angle_deg"], "length_mm": f(sm["length"]), "half_width_mm": f(sm["half"]), "tail_mm": f(sm["tail"]),
                        "arrow_mm": [f(v) for v in sm["arrow"]], "lume_mm": [f(v) for v in sm["lume"]], "pointer_half_mm": f(sm["pointer_half"])}
    out["hands"] = hands
    out["hub_radius_mm"] = [f(v) for v in M["hub_radius_px"]]
    out["hand_outline_mm"] = f(M["outline_px"])
    out["date_window_mm"] = [mm(p) for p in M["date_window"]]
    for k in ("logo", "print_khaki", "print_swiss_made", "crown_box"):
        out[k] = box(M[k])

    def traced(mask, x0b, y0b, min_area):
        n2, lab2, st2, _ = cv2.connectedComponentsWithStats(255 - mask)  # fill specks inside the strokes
        mask[np.isin(lab2, [i for i in range(2, n2) if st2[i, 4] < 12])] = 255
        up = cv2.GaussianBlur(cv2.resize(mask, None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR), (0, 0), UP * 0.5)
        to_mm = lambda p: [round((p[0] / UP + x0b - px0) / S, 3), round(-(p[1] / UP + y0b - py0) / S, 3)]
        return shapes_from_mask((up > 128).astype(np.uint8) * 255, to_mm, min_area)

    # insert prints: white on red between the insert edges
    pr = (white & band).astype(np.uint8) * 255
    pr = cv2.morphologyEx(pr, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(pr)

    def printed(i):
        """Drop glare on the insert's edges: thin arcs along the ring, or long pieces touching an edge."""
        ys, xs = np.nonzero(lab == i)
        r = np.hypot(xs - bcx, ys - bcy)
        a_ = np.unwrap(np.sort(np.arctan2(ys - bcy, xs - bcx)))
        along, across = (a_.max() - a_.min()) * r.mean(), r.max() - r.min()
        edge = (r.max() > rg["insert_out"] - 6 or r.min() < rg["insert_in"] + 8) and along > 2 * across
        thin = len(xs) / max(along, across, 1) < 6
        return len(xs) >= 15 and not (along > 2.5 * across and across < 12) and not edge and not thin

    pr = np.isin(lab, [i for i in range(1, n) if printed(i)]).astype(np.uint8) * 255
    x0b, y0b = int(bcx - rg["insert_out"] - 10), int(bcy - rg["insert_out"] - 10)
    sz = int(2 * rg["insert_out"] + 20)
    out["insert_prints"] = traced(pr[y0b:y0b + sz, x0b:x0b + sz].copy(), x0b, y0b, 12)

    j = M["bracelet_joints_y"]
    diffs = lambda v: [abs(a - b) for a, b in zip(v[1:], v[:-1])]
    outer = diffs(j["top_outer"]) + [abs(j["bottom_outer"][1] - j["bottom_outer"][0]) / M["bottom_outer_rows"]]
    centre = diffs(j["top_centre"]) + diffs(j["bottom_centre"])
    out["bracelet_pitch_mm"] = {"outer": f(float(np.mean(outer))), "centre": f(float(np.mean(centre)))}
    out["bracelet_joints_mm"] = {k: [f(abs(y - py0)) for y in v] for k, v in j.items()}
    shift = [abs(j["top_outer"][0] - py0) - abs(j["top_centre"][0] - py0), abs(j["bottom_outer"][0] - py0) - abs(j["bottom_centre"][0] - py0)]
    out["bracelet_centre_joint_shift_mm"] = f(float(np.mean(shift)))
    out["bracelet_centre_half_mm"] = f(float(np.mean([(c[1] - c[0]) / 2 for c in M["bracelet_centre_px"]])))
    out["end_link_half_mm"] = f((M["end_link_x_px"][1] - M["end_link_x_px"][0]) / 2)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for rk in rg.values():
            cv2.circle(ov, (int(bcx), int(bcy)), int(rk), (0, 0, 255), 1)
        cv2.circle(ov, (int(ccx), int(ccy)), int(case_r), (0, 128, 255), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 1, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 1, (0, 255, 0), -1)
        for name, hd in hands.items():
            t = math.radians(hd["angle_deg"])
            tl = hd["tail_mm"][0] if name != "seconds" else hd["tail_mm"]
            cv2.line(ov, P((-tl * math.sin(t), -tl * math.cos(t))), P((hd["length_mm"] * math.sin(t), hd["length_mm"] * math.cos(t))), (0, 255, 255), 1)
        for hr in range(12):
            t = math.radians(hr * 30)
            r0, r1 = (wd["r"] if hr % 3 == 0 else br_["r"])
            for r_ in (r0, r1):
                cv2.circle(ov, (int(px0 + r_ * math.sin(t)), int(py0 - r_ * math.cos(t))), 4, (255, 0, 255), 1)
        cv2.polylines(ov, [np.array(M["date_window"], np.int32)], True, (0, 200, 255), 1)
        for k in ("logo", "print_khaki", "print_swiss_made", "crown_box"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 1)
        for sh in out["insert_prints"]:
            for lp in [sh["outer"]] + sh["holes"]:
                cv2.polylines(ov, [np.array([P(p) for p in lp], np.int32)], True, (255, 255, 0), 1)
        for v in j.values():
            for y in v:
                cv2.line(ov, (440, y), (1260, y), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "bezel_offset_mm", "bezel_rings_mm", "insert_srgb", "lug_tip_mm",
                                           "bracelet_width_mm", "checks", "indices", "bracelet_pitch_mm", "bracelet_centre_joint_shift_mm",
                                           "bracelet_centre_half_mm", "end_link_half_mm")}, default=float), "->", dest,
          len(data["insert_prints"]), "insert prints")
