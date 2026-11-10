"""Measure the straightened Zeppelin Z86621 photo into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.zeppelin_z86621_rectify     # first: outputs/watches/zeppelin-z86621/front_rectified.png
    python3 -B -m pipeline.zeppelin_z86621_trace [out.json] [overlay.png]     # default config/watches/zeppelin-z86621-trace.json

Anchor: the case silhouette (left edge, and right edge above and below the crown) fits a circle; its diameter is 43 mm (listing).
Check: the strap between the lugs reads about 22 mm (listing). mm, x right, y toward 12, origin = dial centre.
The hour and minute hands are faceted dark steel: one facet near black, the other mid grey. Along each hand's axis the run of
pixels darker than the dial (largest channel below 160) gives the hand's half width. Sub-dial needles are black (below 95).
The top right lug sits behind the strap in the photo; lugs are measured on the left side and the bottom right.
Hand outlines are stored about their pivot seen in the photo; the build puts them on the dial (or sub-dial) centre.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.zeppelin_z96645_trace import circle, edge_profile

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "outputs/watches/zeppelin-z86621/front_rectified.png"
OUT = ROOT / "config/watches/zeppelin-z86621-trace.json"
CASE_MM = 43.0

MANUAL_PX = {
    "dial_centre": [900, 1580],  # rectify target: inner ends of the hour bars on a circle of 701.7 px
    "bar_inner_radius_px": 701.7,
    "dial_edge_px": 778,  # outer edge of the printed rehaut (radial profiles at 8 angles)
    "bezel_inner_px": 790,  # dark line where the polished bezel meets the crystal
    "case_rows": {"left": [1100, 2060], "right": [[1100, 1440], [1730, 2060]]},
    "pivot": [895, 1579],  # grey centre hub as seen (raised: parallax left of the dial centre)
    "hub_radius_px": [44, 24],  # grey collet, bright ring of the cap
    "hour": {"tip": [490, 1290], "half": 45, "thr": 160, "kite": [1.45, 1.8, 4.5]},  # kite: waist at 1.45 mm, widest within 1.8-4.5 mm
    "minute": {"tip": [1440, 1228], "half": 40, "thr": 160, "kite": [1.45, 1.8, 4.5]},
    "sub24": {"centre": [644, 1569], "tip": [556, 1398], "half": 12, "thr": 95, "hub_px": 23.5},
    "subsec": {"centre": [1049, 1765], "tip": [1145, 1918], "half": 12, "thr": 95, "hub_px": 23.5},
    # strap edges between the lugs: left 493 top and bottom; right 1350 at 12, 1336 at 6 (raised lugs, leftover parallax)
    "lug_px": {"inner_x": [493, 1343], "rows_left": [[600, 1000], [2160, 2560]], "rows_right": [[2160, 2560]]},
    "crown_px": {"x": [1740, 1877, 1925], "half_h": 126, "dome_half_h": 100, "y": 1581},
}
ARTEFACTS = ["sub-dial rings, their tracks and numerals, the gold 24 h batons: kept in the dial map (flat print)",
             "applied Zeppelin logo and print: kept in the dial map",
             "crystal glare at 3 and 9 o'clock on the minute track: stays in the dial map",
             "centre hub and the two sub-dial hubs: removed from the dial map, built as parts"]


def hand_outline(im, h, pivot, r0, S):
    g = im.astype(np.float32).max(2)
    s, w, u, n = edge_profile(g, h["thr"], pivot, h["tip"], h["half"], r0)
    L = float(s[-1]) + 0.5
    prof = [(float(si), float(wi)) for si, wi in zip(s, w)]
    poly = prof + [(L + 0.5, 0.0)] + [(si, -wi) for si, wi in reversed(prof)]
    poly = cv2.approxPolyDP(np.float32(poly)[:, None], 0.35, True)[:, 0]
    posed = lambda si, wi: [round(float(u[0] * si + n[0] * wi) / S, 3), round(float(-(u[1] * si + n[1] * wi)) / S, 3)]
    out = {"angle_deg": round(math.degrees(math.atan2(u[0], -u[1])) % 360, 2), "length_mm": round(L / S, 3),
           "outline_mm": [posed(si, wi) for si, wi in poly], "max_half_width_mm": round(float(w.max()) / S, 3)}
    if "kite" in h:  # dauphine: waist at the hub, widest point, straight taper to the tip (the raw run picks up sub-dial print near the hub)
        a0, b0, b1 = h["kite"]
        offs = np.arange(0, h["half"] + 0.5, 0.5, dtype=np.float32)

        def narrow(sv):  # the narrower side's dark run: print touching one edge (the 60 beside the minute hand) does not widen it
            side = []
            for sgn in (1, -1):
                pts = ((np.float32(pivot) + u * sv)[None] + sgn * offs[:, None] * n[None]).astype(np.float32)
                v = cv2.remap(g, pts[:, 0][None], pts[:, 1][None], cv2.INTER_LINEAR)[0] < h["thr"]
                side.append(float(offs[np.argmin(v)] if not v.all() else offs[-1]))
            return min(side) / S

        stations = np.arange(b0, b1, 0.05)
        ws = np.array([narrow(a * S) for a in stations])
        ws = np.convolve(np.pad(ws, 2, mode="edge"), np.ones(5) / 5, mode="valid")
        k = int(np.argmax(ws))
        out["half_profile_mm"] = kp = [[1.0, round(narrow(a0 * S), 3)], [round(float(stations[k]), 3), round(float(ws[k]), 3)], [round(L / S, 3), 0.0]]
        out["outline_mm"] = [posed(a * S, b * S) for a, b in kp] + [posed(a * S, -b * S) for a, b in kp[-2::-1]] + [posed(0, 0)]  # dial mask
    return out


def trace(overlay=None):
    im = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)[..., :3]
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    M = MANUAL_PX
    cx0, cy0 = M["dial_centre"]
    cr = M["case_rows"]
    left = circle([(np.nonzero(gray[y] < 235)[0].min(), y) for y in range(cr["left"][0], cr["left"][1], 20)])
    right = circle([(np.nonzero(gray[y] < 235)[0].max(), y) for a, b in cr["right"] for y in range(a, b, 20)])
    Rc = (left[2] + right[2]) / 2
    S = 2 * Rc / CASE_MM
    ccx, ccy = (left[0] + right[0]) / 2, (left[1] + right[1]) / 2
    assert abs(ccx - cx0) < 40 and abs(ccy - cy0) < 25, "case circle far from the dial centre: %.1f %.1f" % (ccx, ccy)
    out = {"source": str(SRC.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [cx0, cy0],
           "anchor": "case edge circles left r %.1f / right r %.1f px = %.0f mm diameter" % (left[2], right[2], CASE_MM),
           "case_seen_offset_mm": [round((ccx - cx0) / S, 3), round(-(ccy - cy0) / S, 3)]}
    out["rings_mm"] = {"hour_bars_inner": round(M["bar_inner_radius_px"] / S, 3), "dial_edge": round(M["dial_edge_px"] / S, 3),
                       "bezel_inner": round(M["bezel_inner_px"] / S, 3), "case": CASE_MM / 2}

    # lugs: outer silhouette about the case circle's centre (left side top and bottom, right side bottom)
    lp = M["lug_px"]
    rows = {}
    for side, spans in (("left", lp["rows_left"]), ("right", lp["rows_right"])):
        for a, b in spans:
            for y in range(a, b, 4):
                xs = np.nonzero(gray[y] < 240)[0]
                if not len(xs):
                    continue
                h = (ccx - xs.min()) if side == "left" else (xs.max() - ccx)
                rows.setdefault(round(abs(ccy - y) / S * 4) / 4, []).append(h / S)
    ys_, hs_ = zip(*[(y, float(np.mean(v))) for y, v in sorted(rows.items())])
    hs_ = np.convolve(np.pad(hs_, 2, mode="edge"), np.ones(5) / 5, mode="valid")  # rows binned to 0.25 mm alternate by one pixel row: +-0.5 mm mean
    prof = [(y, round(float(h), 3)) for y, h in zip(ys_, hs_)]
    inner = (ccx - lp["inner_x"][0] + lp["inner_x"][1] - ccx) / 2 / S
    tips = []
    for side, spans in (("left", lp["rows_left"]), ("right", lp["rows_right"])):
        for a, b in spans:
            ys = [y for y in range(a, b) if len(np.nonzero(gray[y] < 240)[0]) and
                  ((ccx - np.nonzero(gray[y] < 240)[0].min()) if side == "left" else (np.nonzero(gray[y] < 240)[0].max() - ccx)) / S > inner + 0.5]
            tips.append(abs(ccy - (min(ys) if a < ccy else max(ys))) / S)
    tip = round(float(np.mean(tips)), 2)
    from_y = 15.25
    out["lug"] = {"inner_x_mm": round(inner, 3), "outer_x_mm": round(max(h for y, h in prof if from_y < y < tip - 1.5), 3),
                  "tip_mm": {"mean": tip, "each": [round(t, 2) for t in tips]}, "from_y_mm": from_y,
                  "outline_half_mm": [[y, h] for y, h in prof if from_y - 0.25 <= y <= tip]}
    f = im.astype(int)
    brown = (f[..., 2] - f[..., 0]) > 25
    row = int(ccy + (tip + 0.6) * S)  # 6 o'clock: the 12 o'clock strap has its keeper loop beside it
    xs = np.nonzero(brown[row - 3:row + 4].mean(0) > 0.5)[0]
    out["checks"] = {"strap_at_6_past_lug_tips_mm": round(float(xs.max() - xs.min()) / S, 2), "lug_inner_gap_mm": round(2 * inner, 2)}

    pc = M["pivot"]
    out["hands"] = {k: hand_outline(im, M[k], pc, M["hub_radius_px"][0] - 6, S) for k in ("hour", "minute")}
    out["central_pivot_seen_mm"] = [round((pc[0] - cx0) / S, 3), round(-(pc[1] - cy0) / S, 3)]
    out["hub_mm"] = {"collet": round(M["hub_radius_px"][0] / S, 3), "cap": round(M["hub_radius_px"][1] / S, 3)}
    out["subdials"] = {}
    for k in ("sub24", "subsec"):
        sd = M[k]
        h = hand_outline(im, sd, sd["centre"], sd["hub_px"] - 4, S)
        out["subdials"][k] = {"centre_mm": [round((sd["centre"][0] - cx0) / S, 3), round(-(sd["centre"][1] - cy0) / S, 3)],
                              "hub_radius_mm": round(sd["hub_px"] / S, 3), **h}
    cp = M["crown_px"]
    out["crown"] = {"angle_deg": 90.0, "r_from_to_mm": [round((x - ccx) / S, 3) for x in cp["x"]], "radius_mm": round(cp["half_h"] / S, 3),
                    "dome_radius_mm": round(cp["dome_half_h"] / S, 3), "y_mm": round(-(cp["y"] - cy0) / S, 3)}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = (im // 2).copy()
        P = lambda q, o: (int(round(o[0] + q[0] * S)), int(round(o[1] - q[1] * S)))
        for c in (left, right):
            cv2.circle(ov, (int(c[0]), int(c[1])), int(c[2]), (0, 255, 0), 1)
        for r in (M["bar_inner_radius_px"], M["dial_edge_px"], M["bezel_inner_px"]):
            cv2.circle(ov, (cx0, cy0), int(r), (255, 128, 0), 1)
        for hd in out["hands"].values():
            cv2.polylines(ov, [np.array([P(q, pc) for q in hd["outline_mm"]])], True, (0, 255, 255), 1)
        for k, sd in out["subdials"].items():
            cv2.polylines(ov, [np.array([P(q, M[k]["centre"]) for q in sd["outline_mm"]])], True, (0, 255, 255), 1)
            cv2.circle(ov, tuple(M[k]["centre"]), int(M[k]["hub_px"]), (0, 255, 255), 1)
        for sx in (1, -1):
            for sy in (1, -1):
                cv2.polylines(ov, [np.array([P((sx * h, sy * y), (ccx, ccy)) for y, h in out["lug"]["outline_half_mm"]])], False, (255, 0, 255), 1)
            cv2.line(ov, P((sx * inner, -tip), (ccx, ccy)), P((sx * inner, tip), (ccx, ccy)), (255, 0, 255), 1)
        cv2.line(ov, (0, row), (ov.shape[1], row), (255, 0, 255), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case_seen_offset_mm", "rings_mm", "checks", "crown", "hub_mm")}, default=float),
          {k: (v["angle_deg"], v["length_mm"], v["max_half_width_mm"]) for k, v in list(data["hands"].items()) + list(data["subdials"].items())},
          {k: v for k, v in data["lug"].items() if k != "outline_half_mm"}, "->", dest)
