"""Measure the straightened Zeppelin Z70371 photo into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.zeppelin_z70371_rectify     # first: outputs/watches/zeppelin-z70371/front_rectified.png
    python3 -B -m pipeline.zeppelin_z70371_trace [out.json] [overlay.png]     # default config/watches/zeppelin-z70371-trace.json

Anchor: the case's left edge (the side facing away from the camera, so its silhouette is the top edge) fits a circle concentric
with the minute track; its diameter is 40 mm (Irsyad, 2026-11-09). Check: the strap next to the case reads about 20 mm.
mm, x right, y toward 12, origin = dial centre. Hand pivots, tips and corridors come from gridded crops (MANUAL_PX); the hand
outlines are measured: at every pixel along each hand's axis the dark run across the axis gives the left and right edge.
The raised hands sit up to 0.6 mm off the dial centre in the 3/4 photo (parallax); the outlines are stored about their own
pivot so the build can put them on the centre.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "outputs/watches/zeppelin-z70371/front_rectified.png"
OUT = ROOT / "config/watches/zeppelin-z70371-trace.json"
CASE_MM = 40.0
DARK = 120

MANUAL_PX = {
    "dial_centre": [1100, 1700],  # rectify target: minute-track dots on a circle of 689.6 px
    "track_dot_radius_px": 689.6,
    "dial_edge_radius_px": 798,  # silver dial meets the bezel (left side; the right side shows the crystal edge reflection)
    "case_edge_rows": [1150, 2260],  # rows used for the left-edge circle fit
    # central hands: pivot seen at the hub pin (parallax), tip, corridor half width, start radius (under the hub)
    "pivot_central": [1078, 1689],
    "hub_radius_px": 66,  # gold stepped hub cap
    "hour": {"tip": [730, 1420], "half": 20},
    "minute": {"tip": [1624, 1309], "half": 18},
    "seconds": {"tip": [440, 1485], "half": 6},
    "week": {"tip": [1560, 2120], "half": 6},
    "week_c": {"centre": [1612, 2165], "r_out": 62, "r_in": 50, "arc_from_to_deg": [100, 340]},  # red crescent over the top, open to the lower right; image angles (x right, y down)
    "day": {"pivot": [763, 1693], "tip": [603, 1727], "half": 10, "hub_px": 33},
    "date": {"pivot": [1423, 1693], "tip": [1545, 1795], "half": 10, "hub_px": 33},
    "subdial_parallax_px": [-7, -7],  # sub hubs seen left/up of the symmetric sub-dial centres (raised hubs, 3/4 view)
    "seconds_tail": {"length": 141, "half_root": 6, "half_end": 10},  # gold counterweight opposite the seconds hand
    "bezel_inner_radius_px": 802,
}
# same case as Z70363 (that session's straight front photo, 35.09 px/mm): crown, pusher and lugs in mm. This photo reads the
# lug tips at 21.0 (12) and 21.9 (6) mm and the lug outer edge at about 12.4 mm.
SAME_CASE_MM = {
    "crown": {"angle_deg": 90.0, "radius_mm": 3.078, "collar_radius_mm": 1.795, "r_from_to_mm": [19.377, 20.688, 23.11]},
    "pusher": {"angle_deg": 119.53, "head_radius_mm": 1.71, "stem_radius_mm": 0.855, "r_from_to_mm": [19.605, 21.372, 23.053]},
    "lug": {"inner_x_mm": 10.0, "from_y_mm": 15.75, "tip_mm": {"top": 21.0, "bottom": 21.9, "mean": 21.45}, "outer_x_mm": 12.6,
            "outline_half_mm": [[15.75, 13.0], [16.0, 12.6], [17.0, 12.42], [18.0, 12.27], [19.0, 12.1], [20.0, 11.93], [20.45, 11.7], [21.0, 11.1], [21.45, 10.2]]},
}
ARTEFACTS = ["right side between the dial edge and the bezel: the crystal edge reflects the outer week numbers (mirrored)",
             "gold hub and the sub-dial hubs: removed from the dial map, built as parts",
             "the strap's tan underside on the right of the lower strap: cut away in the strap map"]


def edge_profile(g, pivot, tip, half, r0):
    """Left/right dark extents (px) across the axis at each pixel from r0 to the tip; median filtered."""
    p, t = np.float32(pivot), np.float32(tip)
    L = float(np.hypot(*(t - p)))
    u = (t - p) / L
    n = np.float32([-u[1], u[0]])  # left of the axis in image coordinates
    offs = np.arange(-half, half + 0.5, 0.5, dtype=np.float32)
    rows = []
    for s in np.arange(r0, L + 0.5, 1.0):
        c = p + u * s
        pts = (c[None] + offs[:, None] * n[None]).astype(np.float32)
        v = cv2.remap(g, pts[:, 0][None], pts[:, 1][None], cv2.INTER_LINEAR)[0]
        dark = v < DARK
        k0 = len(offs) // 2
        near = [k for k in range(len(offs)) if dark[k] and abs(offs[k]) <= 2.5]
        if not near:
            rows.append((s, None, None))
            continue
        k = min(near, key=lambda k: abs(offs[k]))
        a = b = k
        while a > 0 and dark[a - 1]:
            a -= 1
        while b < len(offs) - 1 and dark[b + 1]:
            b += 1
        rows.append((s, float(offs[b]) + 0.5, float(-offs[a]) + 0.5))  # left (+n), right (-n)
    good = [r for r in rows if r[1] is not None]
    s = np.array([r[0] for r in good])
    lw, rw = (np.array([r[k] for r in good]) for k in (1, 2))
    med = lambda a: np.array([np.median(a[max(0, i - 4):i + 5]) for i in range(len(a))])
    lw, rw = med(lw), med(rw)
    return s, lw, rw, u, n, L


def hand_outline(g, pivot, tip, half, r0, S):
    """Closed outline in mm about the hand's own pivot (x right, y up), rotated to its angle; simplified."""
    s, lw, rw, u, n, L = edge_profile(g, pivot, tip, half, r0)
    w = (lw + rw) / 2  # symmetric hands: mean of both sides (the photo's edge blur is one-sided near crossings)
    pts_l = [(si, wi) for si, wi in zip(s, w)]
    poly = pts_l + [(L + 0.5, 0.0)] + [(si, -wi) for si, wi in reversed(pts_l)]
    poly = cv2.approxPolyDP(np.float32(poly)[:, None], 0.35, True)[:, 0]
    # axis frame -> image px -> mm (y up)
    out = []
    for si, wi in poly:
        x, y = u * si + n * wi
        out.append([round(float(x) / S, 3), round(float(-y) / S, 3)])
    ang = math.degrees(math.atan2(u[0], -u[1])) % 360
    return {"angle_deg": round(ang, 2), "length_mm": round(L / S, 3), "outline_mm": out,
            "max_half_width_mm": round(float(w.max()) / S, 3)}


def trace(overlay=None):
    im = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)[..., :3]
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)
    M = MANUAL_PX
    cx0, cy0 = M["dial_centre"]
    pts = []
    for y in range(M["case_edge_rows"][0], M["case_edge_rows"][1], 30):
        xs = np.nonzero(g[y, :cx0] < 238)[0]
        pts.append((float(xs.min()), float(y)))
    p = np.float32(pts)
    A = np.c_[2 * p[:, 0], 2 * p[:, 1], np.ones(len(p))]
    fx, fy, c = np.linalg.lstsq(A, (p ** 2).sum(1), rcond=None)[0]
    Rc = float(np.sqrt(c + fx ** 2 + fy ** 2))
    S = 2 * Rc / CASE_MM
    assert abs(fx - cx0) < 10 and abs(fy - cy0) < 10, "case edge circle not concentric: %.1f %.1f" % (fx, fy)
    out = {"source": str(SRC.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [cx0, cy0],
           "anchor": "case left edge circle (r %.1f px, centre %.1f %.1f) = %.0f mm diameter" % (Rc, fx, fy, CASE_MM)}
    out["rings_mm"] = {"track_dots": round(M["track_dot_radius_px"] / S, 3), "dial_edge": round(M["dial_edge_radius_px"] / S, 3)}

    # strap width at the 6 o'clock lug tips (the 12 o'clock strap curls away to the right behind its lug)
    row = int(cy0 + 21.5 * S)
    xs = np.nonzero(g[row - 3:row + 4].mean(0) < 90)[0]
    xs = xs[(xs > cx0 - 15 * S) & (xs < cx0 + 15 * S)]
    out["checks"] = {"strap_at_6_lug_tips_mm": round(float(xs.max() - xs.min()) / S, 2), "strap_listed_mm": 20.0}

    pc = M["pivot_central"]
    hands = {}
    for name in ("hour", "minute", "seconds", "week"):
        h = M[name]
        hands[name] = hand_outline(g, pc, h["tip"], h["half"], M["hub_radius_px"] - 12, S)
    mmp = lambda q, o: [round((q[0] - o[0]) / S, 3), round(-(q[1] - o[1]) / S, 3)]
    wc = M["week_c"]
    arc = [math.radians(a) for a in np.linspace(*wc["arc_from_to_deg"], 40)]
    ring = [(wc["centre"][0] + r * math.cos(a), wc["centre"][1] + r * math.sin(a)) for r, aa in ((wc["r_out"], arc), (wc["r_in"], arc[::-1])) for a in aa]
    hands["week"]["crescent_mm"] = [mmp(q, pc) for q in ring]
    st = M["seconds_tail"]
    a = math.radians(hands["seconds"]["angle_deg"] + 180)
    u, n = (math.sin(a), math.cos(a)), (math.cos(a), -math.sin(a))
    loc = [(-st["half_root"], 0), (-st["half_end"], st["length"] - st["half_end"])]
    loc += [(st["half_end"] * math.cos(t), st["length"] - st["half_end"] + st["half_end"] * math.sin(t)) for t in np.linspace(math.pi, 0, 9)]
    loc += [(st["half_end"], st["length"] - st["half_end"]), (st["half_root"], 0)]
    hands["seconds"]["tail_mm"] = [[round((x * n[0] + y * u[0]) / S, 3), round((x * n[1] + y * u[1]) / S, 3)] for x, y in loc]
    out["hands"] = hands
    subs = {}
    for name in ("day", "date"):
        h = M[name]
        hd = hand_outline(g, h["pivot"], h["tip"], h["half"], h["hub_px"] - 6, S)
        c = [h["pivot"][0] - M["subdial_parallax_px"][0], h["pivot"][1] - M["subdial_parallax_px"][1]]
        cm = mmp(c, (cx0, cy0))
        subs[name] = {"centre_mm": cm, "pivot_seen_mm": mmp(h["pivot"], (cx0, cy0)), "hand_angle_deg": hd["angle_deg"], "hand_length_mm": hd["length_mm"],
                      "hand_mm": [[round(x + cm[0], 3), round(y + cm[1], 3)] for x, y in hd["outline_mm"]]}
    out["subdials"] = subs
    out["sub_hub_radius_mm"] = round(M["day"]["hub_px"] / S, 3)
    out["central_pivot_seen_mm"] = mmp(pc, (cx0, cy0))
    out["hub_radius_mm"] = [round(M["hub_radius_px"] / S, 3), 0.3]
    out["rings_mm"]["bezel_inner"] = round(M["bezel_inner_radius_px"] / S, 3)
    out["rings_mm"]["case"] = CASE_MM / 2
    out.update(SAME_CASE_MM)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = (im // 2).copy()
        P = lambda xy, o: (int(round(o[0] + xy[0] * S)), int(round(o[1] - xy[1] * S)))
        cv2.circle(ov, (int(fx), int(fy)), int(Rc), (0, 255, 0), 2)
        for r in (M["track_dot_radius_px"], M["dial_edge_radius_px"]):
            cv2.circle(ov, (cx0, cy0), int(r), (255, 128, 0), 1)
        for poly in [hd["outline_mm"] for hd in hands.values()] + [hands["seconds"]["tail_mm"], hands["week"]["crescent_mm"]]:
            cv2.polylines(ov, [np.array([P(q, pc) for q in poly])], True, (0, 255, 255), 1)
        for sd in subs.values():
            o = [cx0 + (sd["pivot_seen_mm"][0] - sd["centre_mm"][0]) * S, cy0 - (sd["pivot_seen_mm"][1] - sd["centre_mm"][1]) * S]
            cv2.polylines(ov, [np.array([P(q, o) for q in sd["hand_mm"]])], True, (0, 255, 255), 1)
        cv2.line(ov, (0, row), (ov.shape[1], row), (255, 0, 255), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "rings_mm", "checks", "central_pivot_seen_mm")}, default=float),
          {k: (v["angle_deg"], v["length_mm"], v["max_half_width_mm"]) for k, v in data["hands"].items()}, data["subdials"]["day"]["centre_mm"], "->", dest)
