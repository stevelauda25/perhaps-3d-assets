"""Measure the Armani Exchange AX1903 front photo (transparent background, 4020 x 5202) into mm. numpy + OpenCV.

    python3 -B -m pipeline.armani_ax1903_trace [out.json] [overlay.png]   # default config/watches/armani-ax1903-trace.json

Anchor: the 16-sided case across the 9 and 3 o'clock flats = 44 mm (listing); the strap width is reported as a check.
mm, x right, y toward 12, origin = hand pivot. The photo is composited on white first (load_front).
Case: 16 flats, 8 long ones at 0, 45, 90 ... deg (support distance case_mm / 2) and 8 short ones between them (support
distance read from the silhouette). Black hand paint (the AX fork around the pivot) is thresholded inside 5 mm of the
pivot; white hand bodies, tips, seconds needle, crown, guard and the red 12 o'clock marker are read from 25-100 px
gridded crops (MANUAL_PX, about +-0.1 mm). Hands are stored posed.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/armani-ax1903/front_4020x5202.png"
OUT = ROOT / "config/watches/armani-ax1903-trace.json"
CASE_MM = 44.0  # listing: case 44 mm, taken across the 9 and 3 o'clock flats

MANUAL_PX = {
    "hand_pivot": [1894, 2600],
    # left flat of the case (9 o'clock), rows clear of the facets
    "flat_rows": [2300, 2900],
    # one point on each short facet (upper left, 22.5 deg facet) to read its support distance
    "short_facet_pts": [[490, 2144], [592, 1908]],
    # round edges inside the bezel: crystal opening, inner bevel top; the inner polygon edge of the bezel top (9 o'clock)
    "ring_radius_px": {"crystal": 1114, "bevel_top": 1159, "dial_flat": 1080},
    "bezel_inner_poly_px": 1204,
    "bezel_slope_end_px": 1288,
    # hands: tip point on the axis, white body half width, black tip start (radius px), black tip half width
    "hour": {"tip": [1280, 2247], "body_from": 40, "black_from": 640, "half_width": 34, "tip_half_width": 14},
    "minute": {"tip": [2725, 2117], "body_from": 40, "black_from": 877, "half_width": 34, "tip_half_width": 30},
    # black AX fork: dark pixels (grey < 110) inside this radius
    "fork_radius": 322, "fork_grey": 110,
    # seconds needle: tip, tail end, half width; red from this radius on
    "seconds": {"tip": [1396, 3460], "tail": [2093, 2252], "half_width": 9, "stripe_half_width": 2.5, "red_from": 700},
    # crown at 3: y top/bottom, x of the collar start, knurl start, end
    "crown": {"y_top_bottom": [2400, 2825], "x_collar_knurl_end": [3330, 3352, 3545], "collar_radius_px": 196, "teeth": 30},
    # crown guard outline (right side, upper half; mirrored about the pivot row)
    "guard_px": [[3284, 2075], [3495, 2375], [3500, 2600]],
    # red marker at 12: two trapezoids, (y top, y bottom, half width top, half width bottom)
    "marker_px": [[1225, 1275, 68, 78], [1300, 1347, 92, 100]],
}
ARTEFACTS = ["indices, minute track dots, ARMANI EXCHANGE print and the line-textured centre disc: kept in the dial map (flat)",
             "white hand bodies are straight quads along the posed axes (white on white: no threshold)"]


def load_front(path=FRONT):
    im = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
    a = im[..., 3:].astype(np.float32) / 255
    return (im[..., :3] * a + 255 * (1 - a)).astype(np.uint8), im[..., 3] > 128


def trace(path=FRONT, overlay=None):
    im, fg = load_front(path)
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    r0, r1 = M["flat_rows"]
    left = float(np.median([np.nonzero(fg[y])[0].min() for y in range(r0, r1)]))
    right = 2 * px0 - left  # the right flat is under the crown guard: symmetric about the pivot
    S = (right - left) / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    # short facet support distance: normal at 22.5 deg from the 9 o'clock flat
    n = (-math.cos(math.radians(22.5)), math.sin(math.radians(22.5)))
    short = float(np.mean([(mm(p)[0] * n[0] + mm(p)[1] * n[1]) for p in M["short_facet_pts"]]))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case flats 9-3 = {CASE_MM} mm (listing)",
           "case_support_mm": {"long": CASE_MM / 2, "short": round(short, 3)}}
    out["rings_mm"] = {k: round(v / S, 3) for k, v in M["ring_radius_px"].items()}
    out["bezel_inset_mm"] = {"inner_poly": round(CASE_MM / 2 - M["bezel_inner_poly_px"] / S, 3),
                             "slope_end": round(CASE_MM / 2 - M["bezel_slope_end_px"] / S, 3)}

    h = fg.shape[0]
    prof = []
    for y_mm in np.arange(-40.0, 40.01, 0.25):
        row = int(round(py0 - y_mm * S))
        if 0 <= row < h:
            xs = np.nonzero(fg[row])[0]
            if len(xs):
                prof.append([round(float(y_mm), 2), round((px0 - xs.min()) / S, 3), round((xs.max() - px0) / S, 3)])
    out["silhouette_y_left_right_mm"] = prof
    sil = {p[0]: p for p in prof}
    lft = lambda y: sum(sil[k][1] for k in (round(y, 2), round(-y, 2))) / 2  # left edge only: the guard is on the right
    inner = float(np.median([lft(y) for y in np.arange(27.0, 30.01, 0.25)]))
    tips = [next(float(y) for y in np.arange(20, 32, 0.25) if sil[round(sy * y, 2)][1] < inner + 0.3) for sy in (1, -1)]
    # lug starts where the silhouette leaves the 45 deg flat (support CASE_MM / 2)
    on_case = lambda y: CASE_MM / 2 * math.sqrt(2) - y
    from_y = next(float(y) for y in np.arange(12, 22, 0.25) if lft(y) > on_case(y) + 0.3)
    out["lug"] = {"inner_x_mm": round(inner, 3), "tip_mm": {"top": tips[0], "bottom": tips[1], "mean": round(sum(tips) / 2, 3)},
                  "from_y_mm": from_y, "outer_x_mm": round(max(lft(y) for y in np.arange(from_y, tips[0], 0.25)), 3)}
    out["strap_photo_end_mm"] = {"top": round((py0 - np.nonzero(fg[:, px0])[0].min()) / S - 0.2, 2),
                                 "bottom": round((np.nonzero(fg[:, px0])[0].max() - py0) / S - 0.2, 2)}
    out["checks"] = {"strap_width_mm": round(2 * inner, 2), "lug_to_lug_mm": round(sum(tips), 2)}

    ang = lambda dx, dy: math.degrees(math.atan2(dx, -dy)) % 360  # px vector -> clockwise from 12
    o = np.float32([px0, py0])

    def quad(r_a, r_b, hw_a, hw_b, u):
        nn = np.float32([-u[1], u[0]])
        return [mm(p) for p in (o + u * r_a - nn * hw_a, o + u * r_b - nn * hw_b, o + u * r_b + nn * hw_b, o + u * r_a + nn * hw_a)]

    hands = {}
    for name in ("hour", "minute"):
        hm = M[name]
        u = np.float32(hm["tip"]) - o
        L = float(np.hypot(*u))
        u /= L
        hw, tw, b = hm["half_width"], hm["tip_half_width"], hm["black_from"]
        body = quad(hm["body_from"], b, hw, hw * 0.92, u)
        if name == "hour":  # narrow black needle end with a round cap
            tip = quad(b, L - tw, tw, tw, u) + [mm(o + u * (L - tw) + np.float32([-u[1], u[0]]) * tw * math.sin(a) + u * tw * math.cos(a))
                                                 for a in np.linspace(-math.pi / 2, math.pi / 2, 9)[1:-1]]
            tip = tip[:2] + tip[4:] + tip[2:4]  # keep the outline in order: cap between the two outer corners
        else:  # black lance: full width at the body end, point at the tip
            nn = np.float32([-u[1], u[0]])
            tip = [mm(p) for p in (o + u * b - nn * tw, o + u * (L - 0.45 * (L - b)) - nn * tw, o + u * L, o + u * (L - 0.45 * (L - b)) + nn * tw,
                                   o + u * b + nn * tw)]
        lume = quad(hm["body_from"] + 12, b - 6, hw - 7, hw * 0.92 - 7, u)  # white top inside the grey edge
        hands[name] = {"angle_deg": round(ang(*u), 2), "length_mm": round(L / S, 3), "body_mm": body, "lume_mm": lume, "tip_mm": tip}

    sm = M["seconds"]
    u = np.float32(sm["tip"]) - o
    L = float(np.hypot(*u))
    u /= L
    Lt = float(np.hypot(*(np.float32(sm["tail"]) - o)))
    hw, sw = sm["half_width"], sm["stripe_half_width"]
    hands["seconds"] = {"angle_deg": round(ang(*u), 2), "length_mm": round(L / S, 3), "tail_mm": round(Lt / S, 3),
                        "outline_mm": quad(-Lt, L, hw * 1.2, hw * 0.6, u), "red_mm": quad(sm["red_from"], L - 4, sw * 1.6, sw, u),
                        "stripe_mm": quad(-Lt + 12, sm["red_from"], sw, sw, u)}

    # black AX fork: dark pixels near the pivot, outer loops with holes
    grey = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    dark = (grey < M["fork_grey"]).astype(np.uint8)
    disc = np.zeros_like(dark)
    cv2.circle(disc, (px0, py0), M["fork_radius"], 1, -1)
    dark = cv2.morphologyEx(dark & disc, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    cnts, hier = cv2.findContours(dark, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    fork = []
    for i, c in enumerate(cnts):
        if hier[0][i][3] >= 0 or cv2.contourArea(c) < 400:
            continue
        holes = [cnts[j] for j in range(len(cnts)) if hier[0][j][3] == i and cv2.contourArea(cnts[j]) > 150]
        simp = lambda c_: [mm(p) for p in cv2.approxPolyDP(c_, 1.2, True)[:, 0][::-1]]  # image y down -> ccw in mm
        fork.append({"outer": simp(c), "holes": [simp(hc) for hc in holes]})
    hands["fork"] = fork
    out["hands"] = hands
    out["hub_mm"] = round(14 / S, 3)

    cr = M["crown"]
    yt, yb = cr["y_top_bottom"]
    out["crown"] = {"angle_deg": round(ang(cr["x_collar_knurl_end"][1] - px0, (yt + yb) / 2 - py0), 2), "radius_mm": round((yb - yt) / 2 / S, 3),
                    "collar_radius_mm": round(cr["collar_radius_px"] / S, 3), "teeth": cr["teeth"],
                    "r_collar_knurl_end_mm": [round((x - px0) / S, 3) for x in cr["x_collar_knurl_end"]]}
    out["guard_mm"] = [mm(p) for p in M["guard_px"]]
    out["marker_mm"] = [[round((py0 - a) / S, 3), round((py0 - b) / S, 3), round(c / S, 3), round(d / S, 3)] for a, b, c, d in M["marker_px"]]
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2 + 60
        Pp = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        poly16 = case_outline(out["case_support_mm"]["long"], out["case_support_mm"]["short"])
        cv2.polylines(ov, [np.array([Pp(q) for q in poly16])], True, (0, 0, 255), 3)
        for r in M["ring_radius_px"].values():
            cv2.circle(ov, (px0, py0), r, (255, 128, 0), 2)
        for y_mm, l, r_ in prof:
            cv2.circle(ov, Pp((-l, y_mm)), 3, (0, 255, 0), -1)
            cv2.circle(ov, Pp((r_, y_mm)), 3, (0, 255, 0), -1)
        polys = [hands[k][f] for k in ("hour", "minute") for f in ("body_mm", "tip_mm")] + [hands["seconds"][f] for f in ("outline_mm", "red_mm")]
        polys += [s["outer"] for s in fork] + [hh for s in fork for hh in s["holes"]] + [out["guard_mm"]]
        for p in polys:
            cv2.polylines(ov, [np.array([Pp(q) for q in p])], True, (0, 200, 255), 2)
        lg = out["lug"]
        for sy in (1, -1):
            cv2.line(ov, Pp((-20, sy * lg["tip_mm"]["mean"])), Pp((20, sy * lg["tip_mm"]["mean"])), (0, 128, 255), 2)
            cv2.line(ov, Pp((-20, sy * lg["from_y_mm"])), Pp((20, sy * lg["from_y_mm"])), (255, 255, 0), 2)
        for sx in (1, -1):
            cv2.line(ov, Pp((sx * inner, -38)), Pp((sx * inner, 38)), (0, 128, 255), 2)
        k = out["crown"]
        for r_ in k["r_collar_knurl_end_mm"]:
            cv2.line(ov, Pp((r_, -k["radius_mm"])), Pp((r_, k["radius_mm"])), (255, 0, 128), 3)
        cv2.imwrite(str(overlay), ov)
    return out


def case_outline(long, short, inset=0.0):
    """16-gon from support distances: long flats at k * 45 deg (0 = 12 o'clock), short flats between them; moved in by inset.
    Same as pipeline/steps/watch_armani_ax1903.case_outline (Blender cannot import OpenCV modules)."""
    d = [(long if k % 2 == 0 else short) - inset for k in range(16)]
    pts = []
    for k in range(16):
        a1, a2 = math.radians(22.5 * k), math.radians(22.5 * (k + 1))
        d1, d2 = d[k], d[(k + 1) % 16]
        det = math.sin(a1) * math.cos(a2) - math.cos(a1) * math.sin(a2)
        pts.append(((d1 * math.cos(a2) - d2 * math.cos(a1)) / det, (d2 * math.sin(a1) - d1 * math.sin(a2)) / det))
    return pts


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case_support_mm", "rings_mm", "bezel_inset_mm", "lug", "strap_photo_end_mm",
                                           "checks", "crown", "guard_mm", "marker_mm")}, default=float), "->", dest)
    print({k: (v["angle_deg"], v["length_mm"]) for k, v in data["hands"].items() if k != "fork"}, "fork loops",
          [(len(f["outer"]), len(f["holes"])) for f in data["hands"]["fork"]])
