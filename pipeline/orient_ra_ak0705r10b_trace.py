"""Measure the Orient RA-AK0705R10B front photo into mm. numpy + OpenCV.

    python3 -B -m pipeline.orient_ra_ak0705r10b_trace [out.json] [overlay.png]   # default config/watches/orient-ra-ak0705r10b-trace.json

Native 1569 x 2380 retailer photo, close to straight-on. Anchor: circle fit on the case's dark outline (rows beside the crown
left out) = 40.5 mm (listing); the strap at the lug tips (21 mm listed) is the check. The hand pivot sits 0.38 mm above the
case centre (camera a little low, domed crystal): the model is centred on the pivot, the dial UVs follow the photo's rings.
mm, x right, y toward 12, origin = hand pivot. Hands, sub-dial hands, rings and lug tips: MANUAL_PX from gridded crops.
Applied numerals, bars and the ORIENT letters: dark (or white) blobs of the photo, the hands cut out (they cover them).
trace() takes another photo's MANUAL_PX (RA-AK0704N10B, same case): optional keys case_circle (fixed [cx, cy, R] px), rings_centre
(px the dial rings are measured about, default the case centre), numeral_bright ([kernel, top-hat above, S below]: silver parts), numeral_min_area, exclude_circles
([x, y, r] px: sub-dial print) and lugs_from (trace json whose lug_mean is reused instead of this photo's lugs).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/orient-ra-ak0705r10b/front_1569x2380.jpg"
OUT = ROOT / "config/watches/orient-ra-ak0705r10b-trace.json"
CASE_MM = 40.5  # listing: 40.5 mm without crown

MANUAL_PX = {
    "hand_pivot": [751, 1103],
    # case outline rows: x windows for the left / right flank, rows beside the crown skipped on the right
    "case_rows": {"y": [820, 1400], "left_x": [30, 250], "right_x": [1300, 1460], "skip_right_y": [1010, 1250], "dark": 150},
    # radii about the case centre: inner edge of the polished bezel (crystal seat), dial edge (dark line at the rehaut foot)
    "crystal_open_r": 612, "dial_edge_r": 566,
    # hands: tip point, then [r, half width] stations of the black core along pivot -> tip, tail [r, half] toward the tail
    "hands": {
        "hour": {"tip": [503, 921], "length": 307, "stations": [[0, 13], [40, 15], [80, 14], [110, 12.5], [140, 12], [170, 10.5],
                                                               [215, 9], [260, 7.5], [290, 4.5], [300, 2.5]],
                 "tail": [[30, 10], [55, 9.5], [72, 6], [80, 0]]},
        "minute": {"tip": [1158, 928], "length": 443, "stations": [[0, 13], [60, 14.5], [100, 12.5], [160, 11.5], [200, 10], [260, 8],
                                                                   [300, 6.5], [340, 5.5], [380, 4.5], [420, 2.5]],
                   "tail": [[25, 12], [45, 10], [62, 6], [70, 0]]},
        "seconds": {"tip": [468, 715], "length": 480, "stations": [[0, 5], [60, 4], [200, 2.5], [400, 1.5], [470, 1]],
                    "tail": [[30, 6], [146, 7]], "tail_round": 7},
    },
    "rim_px": 2,  # bright edge round the dark core (polished gold reflecting the dark studio) of every hand and numeral
    "hub": {"black_r": 22, "pin_r": 6},
    # sub-dial hands: hub, tip, round head radius, body half width at the head
    "subhands": {"day": {"hub": [569, 996], "tip": [705, 1032], "head_r": 22, "half": 7},
                 "h24": {"hub": [844, 1276], "tip": [889, 1370], "head_r": 22, "half": 7}},
    # applied parts: annulus about the pivot for the numerals and bars, box for the ORIENT letters
    "numeral_r": [300, 530], "numeral_dark": 50, "logo_box": [[758, 903], [972, 955]], "logo_white": 200,
    "date_box": [[1060, 1070], [1165, 1150]],  # printed date window: not an applied numeral
    # lugs: tip row and inner (strap side) x per lug; the outer edge is the photo silhouette
    "lugs": {"tl": {"tip_y": 345, "inner_x": 403}, "tr": {"tip_y": 345, "inner_x": 1100},
             "bl": {"tip_y": 1895, "inner_x": 388}, "br": {"tip_y": 1895, "inner_x": 1090}},
    # strap: x edges at the tips, row where the photo's strap leaves the case (centre line)
    "strap": {"top": {"x": [403, 1100], "case_y": 437}, "bottom": {"x": [388, 1090], "case_y": 1810}},
    # crown at 3: y top / bottom, x where it leaves the case flank and of its end, flutes counted on the photo
    "crown": {"y_top_bottom": [1025, 1235], "x_from_to": [1427, 1528], "teeth": 18},
}
ARTEFACTS = ["minute track, sub-dial rings and print, date window, crest and Automatic stay in the photo map (flat)",
             "hands, numerals and bars are polished gold (listing); the photo shows them dark with bright edges (studio reflection)",
             "the buckle is not modelled"]


def case_circle(g, M):
    c = M["case_rows"]
    P = []
    for y in range(c["y"][0], c["y"][1], 10):
        l = np.nonzero(g[y, c["left_x"][0]:c["left_x"][1]] < c["dark"])[0]
        r = np.nonzero(g[y, c["right_x"][0]:c["right_x"][1]] < c["dark"])[0]
        if len(l):
            P.append((c["left_x"][0] + l.min(), y))
        if len(r) and not c["skip_right_y"][0] <= y <= c["skip_right_y"][1]:
            P.append((c["right_x"][0] + r.max(), y))
    P = np.array(P, float)
    cx, cy, k = np.linalg.lstsq(np.c_[2 * P, np.ones(len(P))], (P ** 2).sum(1), rcond=None)[0]
    R = math.sqrt(k + cx * cx + cy * cy)
    res = np.abs(np.hypot(P[:, 0] - cx, P[:, 1] - cy) - R)
    assert res.mean() < 1.0, "case circle fit %.2f px" % res.mean()
    return cx, cy, R


def hand_poly(o, h):
    """Black core outline (px): stations on both sides of the pivot -> tip axis, tail on the other side."""
    u = np.float32(h["tip"]) - o
    u /= np.hypot(*u)
    n = np.float32([-u[1], u[0]])
    side = lambda sgn: [o + u * r + n * sgn * w for r, w in h["stations"]]
    tail = h["tail"]
    tl = [o - u * r + n * w for r, w in tail]
    pts = side(1) + [o + u * h["length"]] + side(-1)[::-1]
    if h.get("tail_round"):  # round end: half circle about the last tail station
        c, rr = o - u * tail[-1][0], h["tail_round"]
        arc = [c + (n * math.cos(a) - u * math.sin(a)) * rr for a in np.linspace(-math.pi / 2, math.pi / 2, 9)]
        pts += [o - u * r - n * w for r, w in tail[:-1]] + arc + [o - u * r + n * w for r, w in tail[-2::-1]]
    else:
        pts += [o - u * r - n * w for r, w in tail] + tl[::-1]
    return np.float32(pts), u


def blobs(mask, min_area, S, mm):
    cnts, hier = cv2.findContours(mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    out = []
    for i, c in enumerate(cnts):
        if hier[0][i][3] >= 0 or cv2.contourArea(c) < min_area:
            continue
        simp = lambda cc: [mm(p) for p in cv2.approxPolyDP(cc, 0.8, True)[:, 0][::-1]]  # image y down -> ccw in mm
        holes, j = [], hier[0][i][2]
        while j >= 0:
            if cv2.contourArea(cnts[j]) > 12:
                holes.append(simp(cnts[j]))
            j = hier[0][j][0]
        out.append({"outer": simp(c), "holes": holes})
    return out


def trace(path=FRONT, overlay=None, M=MANUAL_PX, case_mm=CASE_MM, artefacts=ARTEFACTS):
    im = cv2.imread(str(path))
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    px0, py0 = M["hand_pivot"]
    o = np.float32([px0, py0])
    ccx, ccy, Rc = M["case_circle"] if "case_circle" in M else case_circle(g, M)
    rcx, rcy = M.get("rings_centre", (ccx, ccy))
    S = 2 * Rc / case_mm
    mm = lambda p: [round((float(p[0]) - px0) / S, 3), round(-(float(p[1]) - py0) / S, 3)]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case outline = {case_mm} mm (listing)", "case_circle_px": [round(ccx, 1), round(ccy, 1), round(Rc, 1)],
           "case_centre_mm": mm((rcx, rcy)), "case_radius_mm": round(Rc / S, 3),
           "crystal_open_mm": round(M["crystal_open_r"] / S, 3), "dial_edge_mm": round(M["dial_edge_r"] / S, 3)}

    # ---- hands ----
    ang = lambda v: round(math.degrees(math.atan2(v[0], -v[1])) % 360, 2)
    hands, hand_px = {}, {}
    rim = M["rim_px"]
    for name, h in M["hands"].items():
        core, u = hand_poly(o, h)
        hand_px[name] = core
        grown = cv2.approxPolyDP(_grow(core, rim), 0.5, True)[:, 0]
        hands[name] = {"angle_deg": ang(u), "length_mm": round(h["length"] / S, 3),
                       "core_mm": [mm(p) for p in core[::-1]], "outline_mm": [mm(p) for p in grown[::-1]],
                       # for the faceted build: [r, half width] along the axis with the bright edge included, tail toward -r
                       "stations_mm": [[round(r / S, 3), round((w + rim) / S, 3)] for r, w in h["stations"]],
                       "tail_mm": [[round(r / S, 3), round((w + rim) / S, 3)] for r, w in h["tail"]],
                       "tail_round_mm": round((h["tail_round"] + rim) / S, 3) if h.get("tail_round") else None}
    for name, h in M["subhands"].items():
        c = np.float32(h["hub"])
        u = np.float32(h["tip"]) - c
        L = float(np.hypot(*u))
        u /= L
        n = np.float32([-u[1], u[0]])
        r0 = math.sqrt(max(h["head_r"] ** 2 - h["half"] ** 2, 0))
        arc = [c + (u * math.cos(a) + n * math.sin(a)) * h["head_r"] for a in np.linspace(math.asin(h["half"] / h["head_r"]),
                                                                                           2 * math.pi - math.asin(h["half"] / h["head_r"]), 40)]
        core = np.float32(arc + [c + u * r0 - n * h["half"], c + u * L, c + u * r0 + n * h["half"]])
        hand_px["sub_" + name] = core
        hands["sub_" + name] = {"hub_mm": mm(c), "angle_deg": ang(u), "length_mm": round(L / S, 3), "core_mm": [mm(p) for p in core[::-1]],
                                "head_r_mm": round((h["head_r"] + rim) / S, 3), "half_mm": round((h["half"] + rim) / S, 3),
                                "outline_mm": [mm(p) for p in cv2.approxPolyDP(_grow(core, rim), 0.5, True)[:, 0][::-1]]}
    out["hands"] = hands
    out["hub_mm"] = {k: round(v / S, 3) for k, v in M["hub"].items()}

    # ---- applied numerals and bars (dark cores with their gold edge), ORIENT letters (white): hands cut out ----
    hmask = np.zeros(g.shape, np.uint8)
    for core in hand_px.values():
        cv2.fillPoly(hmask, [np.int32(np.round(_grow(core, rim + 3)))], 1)
    yy, xx = np.mgrid[0:g.shape[0], 0:g.shape[1]]
    rr = np.hypot(xx - px0, yy - py0)
    ann = (rr > M["numeral_r"][0]) & (rr < M["numeral_r"][1])
    (dx0, dy0), (dx1, dy1) = M["date_box"]
    ann[dy0:dy1, dx0:dx1] = False
    for x, y, r in M.get("exclude_circles", []):
        ann &= np.hypot(xx - x, yy - y) > r
    if "numeral_bright" in M:  # silver parts on a dial lit unevenly: brighter than the dial round them (top-hat)
        k, v, sat = M["numeral_bright"]
        top = cv2.morphologyEx(g, cv2.MORPH_TOPHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
        dark = ((top > v) & (hsv[..., 1] < sat) & ann).astype(np.uint8)
    else:
        dark = ((hsv[..., 2] < M["numeral_dark"]) & ann).astype(np.uint8)
    dark = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    num = cv2.dilate(dark, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * (rim + 1) + 1,) * 2)) & (1 - hmask)
    out["numerals"] = blobs(num, M.get("numeral_min_area", 150), S, mm)
    (bx0, by0), (bx1, by1) = M["logo_box"]
    logo = np.zeros_like(num)
    logo[by0:by1, bx0:bx1] = (g[by0:by1, bx0:bx1] > M["logo_white"]) & (hsv[by0:by1, bx0:bx1, 1] < 90)
    logo = cv2.morphologyEx(logo, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    out["logo"] = blobs(logo, 40, S, mm)

    # ---- lugs: outer edge = first non-background px from outside, per row from the tip to the case circle ----
    fg = (im.min(2) < 236).astype(np.uint8)
    lugs = {}
    for key, L in ({} if "lugs_from" in M else M["lugs"]).items():
        sx = -1 if key[1] == "l" else 1
        sy = 1 if key[0] == "t" else -1
        rows = []
        y = L["tip_y"]
        while True:
            x_out = None
            xs = np.nonzero(fg[y])[0]
            if len(xs):
                x_out = xs.min() if sx < 0 else xs.max()
            if x_out is None or math.hypot(x_out - ccx, y - ccy) < Rc - 2 or abs(y - L["tip_y"]) > 400:
                break
            rows.append((abs(y - L["tip_y"]) / S, abs(x_out - L["inner_x"]) / S))
            y += sy
        lugs[key] = {"tip_y_mm": round(abs(mm((0, L["tip_y"]))[1]), 3), "inner_x_mm": round(abs(mm((L["inner_x"], 0))[0]), 3),
                     "outer_by_depth": [[round(d, 3), round(w, 3)] for d, w in rows[::4]]}
    out["lugs"] = lugs
    if "lugs_from" in M:  # same case as another trace: its lugs, not this photo's
        out["lug_mean"] = json.loads((ROOT / M["lugs_from"]).read_text())["lug_mean"]
    else:  # one lug for all four: mean outer offset per 0.25 mm of depth below the tip, while every lug still has a row
        dmax = min(v["outer_by_depth"][-1][0] for v in lugs.values())
        grid = np.arange(0, dmax, 0.25)
        mean = np.mean([np.interp(grid, *np.array(v["outer_by_depth"]).T) for v in lugs.values()], axis=0)
        out["lug_mean"] = {"tip_y": round(float(np.mean([v["tip_y_mm"] for v in lugs.values()])), 3),
                           "inner_x": round(float(np.mean([v["inner_x_mm"] for v in lugs.values()])), 3),
                           "outer_offset_by_depth": [[round(float(d), 2), round(float(w), 3)] for d, w in zip(grid, mean)]}
    out["strap_mm"] = {k: {"x": [mm((x, 0))[0] for x in v["x"]], "case_y": abs(mm((0, v["case_y"]))[1]),
                           "tip_y": abs(mm((0, M["lugs"][{"top": "tl", "bottom": "bl"}[k]]["tip_y"]))[1])} for k, v in M["strap"].items()}
    out["checks"] = {"strap_width_mm": {k: round(v["x"][1] - v["x"][0], 2) for k, v in out["strap_mm"].items()},
                     "lug_to_lug_mm": round(out["strap_mm"]["top"]["tip_y"] + out["strap_mm"]["bottom"]["tip_y"], 2)}
    cr = M["crown"]
    yt, yb = cr["y_top_bottom"]
    out["crown"] = {"centre_y_mm": mm((0, (yt + yb) / 2))[1], "radius_mm": round((yb - yt) / 2 / S, 3), "teeth": cr["teeth"],
                    "x_from_to_mm": [mm((x, 0))[0] for x in cr["x_from_to"]]}
    out["manual_px"] = M
    out["artefacts_not_traced"] = artefacts

    if overlay:
        ov = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR) // 2 + 60
        Pp = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(ccx), int(ccy)), int(Rc), (0, 0, 255), 1)
        for r in (M["crystal_open_r"], M["dial_edge_r"]):
            cv2.circle(ov, (int(rcx), int(rcy)), r, (255, 128, 0), 1)
        for h in hands.values():
            cv2.polylines(ov, [np.array([Pp(q) for q in h["outline_mm"]])], True, (0, 200, 255), 1)
        for sh in out["numerals"] + out["logo"]:
            for lp in [sh["outer"]] + sh["holes"]:
                cv2.polylines(ov, [np.array([Pp(q) for q in lp])], True, (0, 255, 0), 1)
        lm = out["lug_mean"]
        for sx in (1, -1):
            for sy in (1, -1):
                pts = [(sx * (lm["inner_x"] + w), sy * (lm["tip_y"] - d)) for d, w in lm["outer_offset_by_depth"]]
                cv2.polylines(ov, [np.array([Pp((sx * lm["inner_x"], sy * lm["tip_y"]))] + [Pp(p) for p in pts])], False, (255, 0, 255), 1)
        k = out["crown"]
        for x in k["x_from_to_mm"]:
            cv2.line(ov, Pp((x, k["centre_y_mm"] - k["radius_mm"])), Pp((x, k["centre_y_mm"] + k["radius_mm"])), (255, 0, 128), 1)
        cv2.imwrite(str(overlay), ov)
    return out


def _grow(poly, px):
    """Outline grown outward by px (mask dilate, largest contour)."""
    x0, y0 = np.floor(poly.min(0)) - px - 4
    m = np.zeros((int(poly[:, 1].max() - y0 + px + 6), int(poly[:, 0].max() - x0 + px + 6)), np.uint8)
    sc = 4  # supersampled so a 2 px rim stays smooth
    big = cv2.resize(m, None, fx=sc, fy=sc, interpolation=cv2.INTER_NEAREST)
    cv2.fillPoly(big, [np.int32(np.round((poly - [x0, y0]) * sc))], 1)
    if px > 0:
        big = cv2.dilate(big, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * px * sc + 1,) * 2))
    c = max(cv2.findContours(big, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)[:, 0]
    return (c / sc + [x0, y0]).astype(np.float32)


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case_circle_px", "case_centre_mm", "crystal_open_mm", "dial_edge_mm", "strap_mm",
                                           "checks", "crown")}, default=float), "->", dest)
    print({k: (v["angle_deg"], v["length_mm"]) for k, v in data["hands"].items()}, "numerals", len(data["numerals"]), "logo", len(data["logo"]))
    print("lug", {k: v for k, v in data["lug_mean"].items() if k != "outer_offset_by_depth"}, data["lug_mean"]["outer_offset_by_depth"][::8])
