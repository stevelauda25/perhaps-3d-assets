"""Measure the Tissot T120.607.11.041.00 (Seastar 2000 Professional 46 mm) front photo (2208 x 3262) into mm. Host-side,
numpy + OpenCV.

    python3 -B -m pipeline.tissot_t120607_trace [out.json] [overlay.png]   # default config/watches/tissot-t120.607.11.041.00-trace.json

Same method as pipeline/hamilton_h82405130_trace.py. Anchor: 46 mm case width (listing) from a circle fitted to the coin-edge
bezel on the flanks; the listed 22 mm lug width is reported as a check. mm, x right, y toward 12, origin = hand pivot. Hands,
indices, crown, crown guards and bracelet joints come from gridded and hand-aligned crops (MANUAL_PX, +-2 px = +-0.05 mm); the
round lume dots are found by threshold. The dark insert's white prints are traced by threshold and become geometry; the wave
dial, prints, date and the flange minute track stay in the dial map.
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
FRONT = ROOT / "references/tissot-t120.607.11.041.00/front_2208x3262.jpg"
OUT = ROOT / "config/watches/tissot-t120.607.11.041.00-trace.json"
CASE_MM = 46.0  # listing: case width; the coin-edge bezel is the widest part at 3 and 9
LISTED = {"lug_width_mm": 22.0, "thickness_mm": 15.8}

MANUAL_PX = {
    "hand_pivot": [1013, 1603],
    # hour: sword. Black body with a polished edge, lume blade, a black cross guard over the lume, black grip to the hub
    "hour_hand": {"angle_deg": 306.5, "tip": 423, "shoulder": 368, "half": 58, "neck": [60, 110, 16],
                  "lume": [209, 395, 39], "lume_low": [118, 162, 45], "guard": [162, 209, 72], "grip_half": 16,
                  "tail": [73, 127, 57, 39]},  # pommel behind the hub: wide to 73 px, narrow to 127 px
    # minute: long baton with an arrow tip, polished edge, lume; stepped black tail
    "minute_hand": {"angle_deg": 61.8, "tip": 650, "shoulder": 600, "half": 50, "tail": [80, 125, 48, 29],
                    "lume": [130, 615, 31]},
    # seconds: black needle with a polished edge, lume dot in a polished ring, outlined tip past the dot
    "seconds_hand": {"angle_deg": 127.7, "half": 3.5, "tail": 100, "dot_r": 593, "dot": [22, 27], "tip": [655, 10]},
    "hub_radius_px": [33, 11],  # hour-hand ring, cap
    "outline_px": 5,  # polished hand edge
    # applied indices (polished frame around lume): round dots, triangle at 12, bars at 3, 9 and 6
    "dot_lume_r": 39, "frame_px": 8,
    "triangle_px": {"r": [483, 622], "half": 76},
    "bar_px": {"r": [474, 622], "half": 29.5},  # 3 and 9
    "bar6_px": {"r": [538, 624], "half": 30},
    "date_window": [943, 1950, 1080, 2118],  # polished frame round the black date (31), kept in the dial map
    "logo": [850, 1200, 1180, 1350],  # TISSOT 1853
    "print_seastar": [640, 1770, 1390, 1935],  # SEASTAR, PROFESSIONAL 600M / 2000FT, POWERMATIC 80
    "print_swiss_made": [835, 2135, 1185, 2195],
    "crown_box": [1958, 1445, 2155, 1765],  # case edge to the end of the fluted crown
    "crown_teeth": 20,
    # crown guards (polished, reflect black in the photo): outlines from the case edge, px
    "guard_top": [[1925, 1300], [1985, 1335], [2022, 1392], [2030, 1470], [1980, 1500], [1925, 1500]],
    "guard_bottom": [[1925, 1905], [1985, 1872], [2022, 1815], [2030, 1740], [1980, 1712], [1925, 1712]],
    "bezel_notch_count": 90,  # coin-edge notches about 63 px apart at the rim (FFT of the rim radius: 90 per turn)
    "bezel_rings_px": {"dial_out": 697, "lip_in": 698, "insert_in": 738, "coin_in": 918},  # about the bezel centre
    # bracelet: three columns; outer and centre links of about the same pitch, joints staggered
    "bracelet_joints_y": {"top_outer": [555, 405, 218], "top_centre": [590, 410, 235],
                          "bottom_outer": [2660, 2797, 2935, 3100], "bottom_centre": [2650, 2725, 2900, 3060]},
    "bracelet_centre_px": [[800, 1262], [785, 1240]],
    "end_link_x_px": [560, 1470],
}
ARTEFACTS = ["the photo is 2208 x 3262 at about 41.5 px/mm: hand and index edges are +-2 px",
             "the hand pivot sits 0.1 mm above the bezel centre (photo taken slightly from below); not corrected",
             "the seconds tail lies under the hour hand's grip (same angle): its length is an estimate",
             "bracelet joints differ between the two ends of the photo; one mean pitch is used"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(float)
    tot = im.astype(int).sum(2)
    fg = (765 - tot) > 12  # the lit coin edge is close to the white background
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a, c=(px0, py0): (c[0] + r * np.sin(np.radians(a)), c[1] - r * np.cos(np.radians(a)))

    # coin-edge bezel on the flanks (the lugs leave it above 52 / below 128 deg; crown and guards at 70-112 deg)
    edge = []
    for a in list(np.arange(232, 308.1, 1.0)) + list(np.arange(52, 68.1, 1.0)) + list(np.arange(114, 126.1, 1.0)):
        rs = np.arange(900, 1010, 0.5)
        xs, ys = at(rs, a)
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    ccx, ccy, case_r = fit_circle(np.array(edge))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    # insert outer edge: the dark ceramic meets the polished lip; outliers (prints, glare) dropped
    pts = []
    for a in np.arange(0, 360, 1.0):
        rs = np.arange(870, 930, 0.5)
        xs, ys = (v.astype(int) for v in at(rs, a, (ccx, ccy)))
        v = tot[ys, xs]
        k = next((i for i in range(1, len(rs)) if v[i - 1] < 350 and v[i] >= 350), None)
        if k:
            pts.append((xs[k], ys[k]))
    pts = np.array(pts, float)
    keep = np.ones(len(pts), bool)
    for _ in range(6):
        bcx, bcy, ins_r = fit_circle(pts[keep])
        d = np.abs(np.hypot(pts[:, 0] - bcx, pts[:, 1] - bcy) - ins_r)
        keep = d < max(2.5, 2 * np.percentile(d[keep], 60))
    rg = dict(M["bezel_rings_px"], insert_out=round(float(ins_r), 1), rim_out=round(float(case_r), 1))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width = {CASE_MM} mm (listing)",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "bezel_offset_mm": mm((bcx, bcy)), "bezel_rings_mm": {k: round(v / S, 3) for k, v in rg.items()},
           "insert_edge_fit": {"centre_px": [round(float(bcx), 1), round(float(bcy), 1)], "points": int(keep.sum()), "of": len(pts)},
           "bezel_notches": {"count": M["bezel_notch_count"], "basis": "coin-edge notches about 63 px apart at the rim"}}

    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot(xx - bcx, yy - bcy)
    band = (rr > rg["insert_in"] + 6) & (rr < rg["insert_out"] - 4)
    white = (hsv[..., 1] < 70) & (hsv[..., 2] > 210)  # glare on the ceramic reaches V 170
    out["insert_srgb"] = [round(float(v) / 255, 3) for v in np.median(im[band & ~white & (tot < 300)][:, ::-1], 0)]

    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    tips = [next(y for y in np.arange(22, 30, 0.25) if width[round(sy * (y + 0.25), 2)] < width[round(sy * y, 2)] - 1.0) + 0.125
            for sy in (1, -1)]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    out["bracelet_width_mm"] = {f"{y:+.0f}": round(width[y], 2) for y in (28, 32, 36, -28, -32, -36) if y in width}
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "end_link_width_mm": round((M["end_link_x_px"][1] - M["end_link_x_px"][0]) / S, 2),
                     "listed": LISTED}

    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    f = lambda v: round(v / S, 3)

    # round lume dots by threshold (1 2 4 5 7 8 10 11), measured about the pivot
    lum = ((hsv[..., 1] < 50) & (hsv[..., 2] > 200)).astype(np.uint8)
    rp = np.hypot(xx - px0, yy - py0)
    lum[(rp < 540) | (rp > 640)] = 0
    n, lab, st, cen = cv2.connectedComponentsWithStats(lum)
    dots = []
    for i in range(1, n):
        if 3500 < st[i, 4] < 6000 and abs(st[i, 2] - st[i, 3]) < 4:
            dots.append(mm(cen[i]))
    # the dot at 2 lies under the minute hand: all eight placed on the mean radius at the hours, plus the mean turn
    assert len(dots) == 7, dots
    turn = float(np.mean([(math.degrees(math.atan2(*p)) + 15) % 30 - 15 for p in dots]))
    dot_r = float(np.mean([math.hypot(*p) for p in dots]))
    dots = [[round(dot_r * math.sin(math.radians(hr * 30 + turn)), 3), round(dot_r * math.cos(math.radians(hr * 30 + turn)), 3)]
            for hr in (1, 2, 4, 5, 7, 8, 10, 11)]
    out["indices"] = {"dots_mm": dots, "dot_r_mm": round(dot_r, 3), "turn_deg": round(turn, 2),
                      "dot_lume_r_mm": f(M["dot_lume_r"]), "frame_mm": f(M["frame_px"]),
                      "triangle_r_mm": [f(v) for v in M["triangle_px"]["r"]], "triangle_half_mm": f(M["triangle_px"]["half"]),
                      "bar_r_mm": [f(v) for v in M["bar_px"]["r"]], "bar_half_mm": f(M["bar_px"]["half"]),
                      "bar6_r_mm": [f(v) for v in M["bar6_px"]["r"]], "bar6_half_mm": f(M["bar6_px"]["half"]),
                      "layout": "applied polished frames with lume: triangle at 12, bars at 3 9 6, round dots elsewhere"}
    hands = {}
    for name in ("hour_hand", "minute_hand", "seconds_hand"):
        hands[name.split("_")[0]] = {k: (v if k == "angle_deg" else ([f(x) for x in v] if isinstance(v, list) else f(v))) for k, v in M[name].items()}
    out["hands"] = hands
    out["hub_radius_mm"] = [f(v) for v in M["hub_radius_px"]]
    out["hand_outline_mm"] = f(M["outline_px"])
    for k in ("date_window", "logo", "print_seastar", "print_swiss_made", "crown_box"):
        out[k] = box(M[k])
    out["crown_teeth"] = M["crown_teeth"]
    out["crown_guards_mm"] = [[mm(p) for p in M[k]] for k in ("guard_top", "guard_bottom")]

    # insert prints: white on dark between the insert edges
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
        return len(xs) >= 40 and not (along > 2.5 * across and across < 12) and not edge and not thin

    pr = np.isin(lab, [i for i in range(1, n) if printed(i)]).astype(np.uint8) * 255

    def traced(mask, x0b, y0b, min_area):
        n2, lab2, st2, _ = cv2.connectedComponentsWithStats(255 - mask)  # fill specks inside the strokes
        mask[np.isin(lab2, [i for i in range(2, n2) if st2[i, 4] < 12])] = 255
        up = cv2.GaussianBlur(cv2.resize(mask, None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR), (0, 0), UP * 0.5)
        to_mm = lambda p: [round((p[0] / UP + x0b - px0) / S, 3), round(-(p[1] / UP + y0b - py0) / S, 3)]
        return shapes_from_mask((up > 128).astype(np.uint8) * 255, to_mm, min_area)

    x0b, y0b = int(bcx - rg["insert_out"] - 10), int(bcy - rg["insert_out"] - 10)
    sz = int(2 * rg["insert_out"] + 20)
    out["insert_prints"] = traced(pr[y0b:y0b + sz, x0b:x0b + sz].copy(), x0b, y0b, 12)

    j = M["bracelet_joints_y"]
    diffs = lambda v: [abs(a - b) for a, b in zip(v[1:], v[:-1])]
    out["bracelet_pitch_mm"] = {"outer": f(float(np.mean(diffs(j["top_outer"]) + diffs(j["bottom_outer"])))),
                                "centre": f(float(np.mean(diffs(j["top_centre"]) + diffs(j["bottom_centre"]))))}
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
        for name, hd in M.items():
            if name.endswith("_hand"):
                t = math.radians(hd["angle_deg"])
                L = hd.get("tip", 0) if not isinstance(hd.get("tip"), list) else hd["tip"][0]
                cv2.line(ov, (px0, py0), (int(px0 + L * math.sin(t)), int(py0 - L * math.cos(t))), (0, 255, 255), 1)
        ix = out["indices"]
        for p in dots:
            cv2.circle(ov, P(p), M["dot_lume_r"], (255, 0, 255), 1)
            cv2.circle(ov, P(p), M["dot_lume_r"] + M["frame_px"], (255, 0, 255), 1)
        for k in ("date_window", "logo", "print_seastar", "print_swiss_made", "crown_box"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 1)
        for g in ("guard_top", "guard_bottom"):
            cv2.polylines(ov, [np.array(M[g], np.int32)], True, (0, 200, 255), 1)
        for sh in out["insert_prints"]:
            for lp in [sh["outer"]] + sh["holes"]:
                cv2.polylines(ov, [np.array([P(p) for p in lp], np.int32)], True, (255, 255, 0), 1)
        for v in j.values():
            for y in v:
                cv2.line(ov, (540, y), (1500, y), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "bezel_offset_mm", "bezel_rings_mm", "insert_srgb", "lug_tip_mm",
                                           "bracelet_width_mm", "checks", "bracelet_pitch_mm", "bracelet_centre_joint_shift_mm",
                                           "bracelet_centre_half_mm", "end_link_half_mm")}, default=float), "->", dest,
          len(data["insert_prints"]), "insert prints", "dot r", data["indices"]["dot_r_mm"])
