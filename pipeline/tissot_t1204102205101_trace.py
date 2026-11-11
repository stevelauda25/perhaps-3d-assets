"""Measure the Tissot T120.410.22.051.01 (Seastar 1000 40 mm quartz, black dial, rose gold PVD bezel and centre links) front
photo (1177 x 2012) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.tissot_t1204102205101_trace [out.json] [overlay.png]   # default config/watches/tissot-t120.410.22.051.01-trace.json

Same method as pipeline/tissot_t120607_trace.py. Anchor: 40 mm case width (Tissot listing) from a circle fitted to the
coin-edge bezel on the flanks; the listed 20 mm lug width is reported as a check. mm, x right, y toward 12, origin = hand
pivot. Hands, triangle, bars, crown, crown guards and bracelet joints come from gridded crops and profiles along each hand
(MANUAL_PX, about +-1 px = +-0.05 mm); the round lume dots are found by threshold. The insert's rose gold prints are traced
by threshold and become raised inlays; the dial, its prints, the date and the rehaut minute track stay in the dial map.
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
FRONT = ROOT / "references/tissot-t120.410.22.051.01/front_1177x2012.jpg"
OUT = ROOT / "config/watches/tissot-t120.410.22.051.01-trace.json"
CASE_MM = 40.0  # listing: case width; the coin-edge bezel is the widest part at 9
LISTED = {"lug_width_mm": 20.0, "thickness_mm": 9.97}

MANUAL_PX = {
    "hand_pivot": [547, 1021],
    # hour: baton with a rose gold frame and lume, blunt point; tail full width behind the hub, then narrow
    "hour_hand": {"angle_deg": 304.8, "tip": 214, "shoulder": 188, "half": 24, "lume": [55, 196, 16], "tail": [34, 66, 24, 12]},
    # minute: narrower baton, thin lume channel, blunt point; short stub tail
    "minute_hand": {"angle_deg": 61.7, "tip": 330, "shoulder": 309, "half": 19, "lume": [90, 296, 5], "tail": [26, 32, 19, 19]},
    # seconds: rose gold needle, lume dot in a ring at the index radius, counterweight shaft with a cross bar
    "seconds_hand": {"angle_deg": 59.5, "half": 2.5, "tip": 346, "dot_r": 309, "dot": [7, 10], "shaft": [77, 8], "bar": [77, 97, 24.5]},
    "hub_radius_px": [15, 5],  # boss, cap
    "outline_px": 5,  # rose gold frame round the lume (hands and indices)
    # applied indices (rose gold frame around lume): round dots, triangle at 12, bars at 3 and 9 (date at 6)
    "frame_px": 5,
    "triangle_px": {"r": [270, 327], "half": 38},  # lume: apex, base
    "bar_px": {"r": [262, 326], "half": 15},
    "date_window": [513, 1218, 578, 1307],  # rose gold frame round the white date (30), kept in the dial map
    "logo": [455, 785, 640, 860],  # TISSOT 1853
    "print_seastar": [440, 1160, 660, 1200],  # SEASTAR, 30 bar (300m / 1000 ft)
    "print_swiss_made": [470, 1340, 630, 1372],
    "crown_box": [1012, 946, 1105, 1096],  # case edge to the end of the fluted crown
    "crown_teeth": 20,
    # crown guards (steel shoulders round the crown at 3), px
    "guard_top": [[985, 868], [1036, 878], [1058, 902], [1066, 950], [1012, 950], [985, 950]],
    "guard_bottom": [[985, 1176], [1036, 1166], [1058, 1142], [1066, 1094], [1012, 1094], [985, 1094]],
    "bezel_notch_count": 60,  # coin-edge notches at the rim
    "bezel_rings_px": {"dial_out": 366, "lip_in": 366, "insert_in": 372},  # about the pivot (radial profiles)
    # bracelet: three columns, steel outer and rose gold centre links, joints staggered
    "bracelet_joints_y": {"top_outer": [459, 337, 206, 84], "top_centre": [481, 362, 234, 112],
                          "bottom_outer": [1566, 1690, 1814], "bottom_centre": [1545, 1650, 1778, 1890]},
    "bracelet_centre_px": [[433, 667], [433, 667]],
    "end_link_x_px": [306, 790],
}
ARTEFACTS = ["the photo is 1177 x 2012 at about 22 px/mm: hand and index edges are +-1 px (+-0.05 mm)",
             "the dots at 2 (under the minute hand) and 5 (glare) are placed on the mean radius with the others",
             "the minute tail and the seconds shaft overlap at 7-8 o'clock; the minute stub length is an estimate",
             "bracelet joints differ between the two ends of the photo; one mean pitch is used"]


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(float)
    tot = im.astype(int).sum(2)
    fg = (765 - tot) > 12
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a, c=(px0, py0): (c[0] + r * np.sin(np.radians(a)), c[1] - r * np.cos(np.radians(a)))

    # coin-edge bezel on the flanks (lugs above 50 / below 130 deg; crown and guards at 60-120 deg)
    edge = []
    for a in list(np.arange(232, 308.1, 1.0)) + list(np.arange(50, 58.1, 1.0)) + list(np.arange(122, 130.1, 1.0)):
        rs = np.arange(430, 520, 0.5)
        xs, ys = at(rs, a)
        hit = np.nonzero(fg[ys.astype(int), xs.astype(int)])[0]
        edge.append((xs[hit[-1]], ys[hit[-1]]))
    ccx, ccy, case_r = fit_circle(np.array(edge))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    # insert outer edge: the black insert meets the rose gold coin edge
    pts = []
    for a in np.arange(0, 360, 1.0):
        rs = np.arange(430, 470, 0.5)
        xs, ys = (v.astype(int) for v in at(rs, a, (ccx, ccy)))
        v = tot[ys, xs]
        k = next((i for i in range(1, len(rs)) if v[i - 1] < 250 and v[i] >= 250), None)
        if k:
            pts.append((xs[k], ys[k]))
    pts = np.array(pts, float)
    keep = np.ones(len(pts), bool)
    for _ in range(6):
        bcx, bcy, ins_r = fit_circle(pts[keep])
        d = np.abs(np.hypot(pts[:, 0] - bcx, pts[:, 1] - bcy) - ins_r)
        keep = d < max(1.5, 2 * np.percentile(d[keep], 60))
    rg = dict(M["bezel_rings_px"], insert_out=round(float(ins_r), 1), rim_out=round(float(case_r), 1))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width = {CASE_MM} mm (listing)",
           "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "bezel_offset_mm": mm((bcx, bcy)), "bezel_rings_mm": {k: round(v / S, 3) for k, v in rg.items()},
           "insert_edge_fit": {"centre_px": [round(float(bcx), 1), round(float(bcy), 1)], "points": int(keep.sum()), "of": len(pts)},
           "bezel_notches": {"count": M["bezel_notch_count"], "basis": "coin-edge notches counted at the rim"}}

    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot(xx - bcx, yy - bcy)
    band = (rr > rg["insert_in"] + 4) & (rr < rg["insert_out"] - 3)
    gold = (hsv[..., 0] < 30) & (hsv[..., 1] > 60) & (hsv[..., 2] > 110)  # rose gold prints on the black insert
    out["insert_srgb"] = [round(float(v) / 255, 3) for v in np.median(im[band & ~gold & (tot < 200)][:, ::-1], 0)]
    out["print_srgb"] = [round(float(v) / 255, 3) for v in np.median(im[band & gold & (hsv[..., 2] > 170)][:, ::-1], 0)]

    prof = []
    for y_mm in np.arange(-44, 44.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((xs.min() - px0) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    width = {p[0]: p[2] - p[1] for p in prof}
    # rounded lug ends: the tip is where the outline comes within 0.6 mm of the bracelet width next to it
    tips = [next(y for y in np.arange(20, 28, 0.25) if width[round(sy * y, 2)] < width[round(sy * 25.0, 2)] + 0.6) for sy in (1, -1)]
    out["lug_tip_mm"] = {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)}
    out["bracelet_width_mm"] = {f"{y:+.0f}": round(width[y], 2) for y in (26, 30, 34, -26, -30, -34) if y in width}
    out["checks"] = {"lug_to_lug_mm": round(sum(tips), 2), "end_link_width_mm": round((M["end_link_x_px"][1] - M["end_link_x_px"][0]) / S, 2),
                     "listed": LISTED}

    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [round((b[2] - b[0]) / S, 3), round((b[3] - b[1]) / S, 3)],
                     "centre_mm": mm(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2))}
    f = lambda v: round(v / S, 3)

    # round lume dots by threshold (1 2 4 5 7 8 10 11), measured about the pivot; frame = rose gold ring round them
    lum = ((hsv[..., 1] < 60) & (hsv[..., 2] > 190)).astype(np.uint8)
    rp = np.hypot(xx - px0, yy - py0)
    lum[(rp < 280) | (rp > 340)] = 0
    n, lab, st, cen = cv2.connectedComponentsWithStats(lum)
    dots, areas = [], []
    for i in range(1, n):
        if 500 < st[i, 4] < 1600 and abs(st[i, 2] - st[i, 3]) < 5:
            dots.append(mm(cen[i]))
            areas.append(st[i, 4])
    assert len(dots) >= 6, dots  # the dot at 5 carries a glare that breaks the threshold
    turn = float(np.mean([(math.degrees(math.atan2(*p)) + 15) % 30 - 15 for p in dots]))
    dot_r = float(np.mean([math.hypot(*p) for p in dots]))
    dots = [[round(dot_r * math.sin(math.radians(hr * 30 + turn)), 3), round(dot_r * math.cos(math.radians(hr * 30 + turn)), 3)]
            for hr in (1, 2, 4, 5, 7, 8, 10, 11)]
    lume_r = math.sqrt(float(np.median(areas)) / math.pi)
    out["indices"] = {"dots_mm": dots, "dot_r_mm": round(dot_r, 3), "turn_deg": round(turn, 2),
                      "dot_lume_r_mm": f(lume_r), "frame_mm": f(M["frame_px"]),
                      "triangle_r_mm": [f(v) for v in M["triangle_px"]["r"]], "triangle_half_mm": f(M["triangle_px"]["half"]),
                      "bar_r_mm": [f(v) for v in M["bar_px"]["r"]], "bar_half_mm": f(M["bar_px"]["half"]),
                      "layout": "applied rose gold frames with lume: triangle at 12, bars at 3 and 9, round dots elsewhere, date at 6"}
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

    # insert prints: rose gold on black between the insert edges
    pr = (gold & band).astype(np.uint8) * 255
    n, lab, st, _ = cv2.connectedComponentsWithStats(pr)
    pr = np.isin(lab, [i for i in range(1, n) if st[i, 4] >= 12]).astype(np.uint8) * 255

    def traced(mask, x0b, y0b, min_area):
        n2, lab2, st2, _ = cv2.connectedComponentsWithStats(255 - mask)  # fill specks inside the strokes
        mask[np.isin(lab2, [i for i in range(2, n2) if st2[i, 4] < 6])] = 255
        up = cv2.GaussianBlur(cv2.resize(mask, None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR), (0, 0), UP * 0.5)
        to_mm = lambda p: [round((p[0] / UP + x0b - px0) / S, 3), round(-(p[1] / UP + y0b - py0) / S, 3)]
        return shapes_from_mask((up > 128).astype(np.uint8) * 255, to_mm, min_area)

    x0b, y0b = int(bcx - rg["insert_out"] - 10), int(bcy - rg["insert_out"] - 10)
    sz = int(2 * rg["insert_out"] + 20)
    area = lambda lp: 0.5 * abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(lp, lp[1:] + lp[:1])))
    # specks under 0.1 mm2 are glare on the coin edge, not print (the smallest minute bar is 0.49 mm2)
    out["insert_prints"] = [sh for sh in traced(pr[y0b:y0b + sz, x0b:x0b + sz].copy(), x0b, y0b, 4) if area(sh["outer"]) > 0.1]

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
        ov = im.copy() // 2 + 60
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        for k_, rk in rg.items():
            cv2.circle(ov, (int(bcx), int(bcy)) if k_ != "rim_out" else (int(ccx), int(ccy)), int(rk), (0, 0, 255), 1)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, P((l, y_mm)), 1, (0, 255, 0), -1)
            cv2.circle(ov, P((r_, y_mm)), 1, (0, 255, 0), -1)
        for name, hd in M.items():
            if name.endswith("_hand"):
                t = math.radians(hd["angle_deg"])
                L = hd["tip"]
                cv2.line(ov, (px0, py0), (int(px0 + L * math.sin(t)), int(py0 - L * math.cos(t))), (0, 255, 255), 1)
        for p in dots:
            cv2.circle(ov, P(p), int(lume_r), (255, 0, 255), 1)
            cv2.circle(ov, P(p), int(lume_r + M["frame_px"]), (255, 0, 255), 1)
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
                cv2.line(ov, (300, y), (800, y), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "bezel_offset_mm", "bezel_rings_mm", "insert_srgb", "print_srgb",
                                           "lug_tip_mm", "bracelet_width_mm", "checks", "bracelet_pitch_mm", "bracelet_centre_joint_shift_mm",
                                           "bracelet_centre_half_mm", "end_link_half_mm")}, default=float), "->", dest,
          len(data["insert_prints"]), "insert prints", "dot r", data["indices"]["dot_r_mm"], "lume r", data["indices"]["dot_lume_r_mm"])
