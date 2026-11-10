"""Measure the Hamilton H76709530 (Khaki Aviation Pilot Pioneer Mechanical Bronze 43 mm) official front render (2000 x 2000,
transparent background) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.hamilton_h76709530_trace [out.json] [overlay.png]   # default config/watches/hamilton-h76709530-trace.json

Same method as pipeline/hamilton_h82405130_trace.py. Anchor: 43 mm case (Hamilton official) across the bezel's scallop tips;
the official 20 mm lug width and 52 mm lug to lug are reported as checks. mm, x right, y toward 12, origin = hand pivot. Hand
outlines come from bright components in hand-aligned crops (MANUAL_PX); the black insert's beige prints are traced by
threshold and become inlays. The dial (numerals, railway track, logo, small seconds ring, prints) stays in the dial map.
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.hamilton_h77616533_trace import load
from pipeline.watch_print import UP, shapes_from_mask
from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/hamilton-h76709530/front_official_2000x2000.png"
OUT = ROOT / "config/watches/hamilton-h76709530-trace.json"
CASE_MM = 43.0  # Hamilton official
LISTED = {"lug_width_mm": 20.0, "lug_to_lug_mm": 52.0, "thickness_mm": 13.0}

MANUAL_PX = {
    "hand_pivot": [947, 931],
    # outlines: [distance from the pivot, half width]; hour: baton, lume bulb, needle tip; minute: widening baton, needle tip
    "hour": {"angle_deg": 302.7, "outline": [[-15, 16], [30, 18], [40, 12], [120, 12], [130, 26], [150, 33], [165, 32], [180, 27], [190, 16],
                                              [205, 10], [215, 4], [280, 3], [290, 0]], "lume": [45, 192]},
    "minute": {"angle_deg": 54.2, "outline": [[-15, 15], [30, 13], [40, 10.5], [100, 13], [200, 16], [280, 18.5], [290, 11.5], [300, 6],
                                               [310, 3.5], [385, 3], [392, 0]], "lume": [45, 285]},
    "hub_radius_px": [30, 13],  # bronze collar, steel cap
    "outline_px": 3,
    "small_seconds": {"centre": [942, 1183], "angle_deg": 217.5, "length": 112, "tail": 99, "half": 11, "hub": 27},  # needle down-left, lozenge tail up-right
    "rings_px": {"dial": 405, "insert_in": 428, "insert_out": 504},  # about the hand pivot; the rim is fitted
    "insert_print_band_px": [433, 499],
    "bezel_notch_count": 100,
    "crown": {"angle_deg": 91.0, "r": [540, 627], "radius": 96, "teeth": 18},
    "lug_inner_x_px": [706, 1180],
    "lug_tips_y": [300, 1600],
    "logo": [800, 720, 1110, 850],
    "print_mech": [820, 1000, 1080, 1040],
    "print_swiss_made": [770, 1255, 1130, 1290],
}
ARTEFACTS = ["official render: the crystal edge is semi-transparent in the alpha; the outline is the filled outer contour",
             "the dial texture, numerals, railway track and small seconds ring stay in the dial map"]


def trace(path=FRONT, overlay=None):
    im = load(path)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    alpha = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)[..., 3]
    cs, _ = cv2.findContours((alpha > 10).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    fg = np.zeros(alpha.shape, np.uint8)
    cv2.drawContours(fg, [max(cs, key=cv2.contourArea)], -1, 1, -1)
    fg = fg.astype(bool)
    h, w = gray.shape
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    at = lambda r, a: (px0 + r * math.sin(math.radians(a)), py0 - r * math.cos(math.radians(a)))
    # scallop tips: the outermost bronze along rays where the background is outside (flanks clear of lugs and crown)
    tips = []
    for a in list(np.arange(50, 76, 0.5)) + list(np.arange(106, 131, 0.5)) + list(np.arange(232, 309, 0.5)):
        rs = np.arange(480, 600, 0.5)
        xs, ys = (np.array(v) for v in at(rs, a))
        k = np.nonzero(~fg[ys.astype(int), xs.astype(int)])[0]
        if len(k):
            tips.append((rs[k[0]], xs[k[0]], ys[k[0]]))
    tips = np.array(tips)
    peak = tips[tips[:, 0] > np.percentile(tips[:, 0], 70)]  # the scallop tips, not the valleys
    ccx, ccy, rim_r = fit_circle(peak[:, 1:])
    S = 2 * rim_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    f = lambda v: round(v / S, 3)
    valley = float(np.percentile(tips[:, 0], 10))
    rg = dict(M["rings_px"], rim_out=round(float(rim_r), 1), scallop_valley=round(valley, 1))
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width = {CASE_MM} mm (Hamilton official), bezel scallop tips",
           "case": {"radius_mm": round(rim_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "bezel_rings_mm": {k: f(v) for k, v in rg.items()},
           "bezel_notches": {"count": M["bezel_notch_count"], "basis": "scallops about 33 px apart at the rim"}}
    yy, xx = np.mgrid[0:h, 0:w]
    rr = np.hypot(xx - px0, yy - py0)
    b0, b1 = M["insert_print_band_px"]
    band = (rr > b0) & (rr < b1)
    bronze = (rr > rg["insert_out"] + 6) & (rr < valley - 4)
    case_px = fg & (rr > rim_r + 25) & (np.abs(xx - px0) > 300) & (np.abs(yy - py0) < 450)
    med = lambda m: [round(float(v) / 255, 3) for v in np.median(im[m][:, ::-1], 0)]
    out["srgb"] = {"insert_print": med(band & (gray > 140)), "bezel": med(bronze & (gray > 60)), "case": med(case_px)}

    prof = []
    for y_mm in np.arange(-30, 30.01, 0.25):
        row = int(round(py0 - y_mm * S))
        xs = np.nonzero(fg[row])[0]
        prof.append([round(float(y_mm), 2), round((px0 - xs.min()) / S, 3)])  # left edge: the crown is on the right
    out["case_half_width_by_y_mm"] = prof
    t0, t1 = M["lug_tips_y"]
    xi0, xi1 = M["lug_inner_x_px"]
    out["lug"] = {"photo_tips_mm": [f(py0 - t0), f(t1 - py0)], "tip_mm": round((f(py0 - t0) + f(t1 - py0)) / 2, 3), "inner_x_mm": f((xi1 - xi0) / 2)}
    widths = {}
    for row in (t0 - 100, t0 - 10, t1 + 10, t1 + 150):
        xs = np.nonzero(fg[row])[0]
        widths[str(row)] = f(xs.max() - xs.min())
    out["checks"] = {"photo_lug_to_lug_mm": f(t1 - t0), "lug_gap_mm": f(xi1 - xi0), "strap_width_mm": widths, "listed": LISTED}

    hands = {}
    for name in ("hour", "minute"):
        hm = M[name]
        hands[name] = {"angle_deg": hm["angle_deg"], "outline_mm": [[f(r), f(v)] for r, v in hm["outline"]],
                       "lume_mm": [f(v) for v in hm["lume"]], "length_mm": f(hm["outline"][-1][0])}
    out["hands"] = hands
    ss = M["small_seconds"]
    out["small_seconds"] = {"centre_mm": mm(ss["centre"]), "angle_deg": ss["angle_deg"], "length_mm": f(ss["length"]), "tail_mm": f(ss["tail"]),
                            "half_mm": f(ss["half"]), "hub_mm": f(ss["hub"])}
    out["hub_radius_mm"] = [f(v) for v in M["hub_radius_px"]]
    out["hand_outline_mm"] = f(M["outline_px"])
    cr = M["crown"]
    out["crown"] = {"angle_deg": cr["angle_deg"], "r_mm": [f(v) for v in cr["r"]], "radius_mm": f(cr["radius"]), "teeth": cr["teeth"]}
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [f(b[2] - b[0]), f(b[3] - b[1])]}
    for k in ("logo", "print_mech", "print_swiss_made"):
        out[k] = box(M[k])

    pr = ((gray > 140) & band).astype(np.uint8) * 255
    n, lab, st, _ = cv2.connectedComponentsWithStats(pr)
    def printed(i):
        """Drop the glare arcs along the glossy insert's edges: long, thin pieces running along the ring."""
        ys, xs = np.nonzero(lab == i)
        r = np.hypot(xs - px0, ys - py0)
        a_ = np.unwrap(np.sort(np.arctan2(ys - py0, xs - px0)))
        along, across = (a_.max() - a_.min()) * r.mean(), r.max() - r.min()
        return len(xs) >= 15 and not (along > 3 * across and across < 10)

    pr = np.isin(lab, [i for i in range(1, n) if printed(i)]).astype(np.uint8) * 255
    x0b, y0b, sz = px0 - b1 - 4, py0 - b1 - 4, 2 * b1 + 8
    win = pr[y0b:y0b + sz, x0b:x0b + sz].copy()
    up = cv2.GaussianBlur(cv2.resize(win, None, fx=UP, fy=UP, interpolation=cv2.INTER_LINEAR), (0, 0), UP * 0.5)
    to_mm = lambda p: [round((p[0] / UP + x0b - px0) / S, 3), round(-(p[1] / UP + y0b - py0) / S, 3)]
    out["insert_prints"] = shapes_from_mask((up > 128).astype(np.uint8) * 255, to_mm, 8)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(ccx), int(ccy)), int(rim_r), (0, 128, 255), 2)
        for k, v in rg.items():
            cv2.circle(ov, (px0, py0), int(v), (0, 0, 255), 1)
        for name in ("hour", "minute"):
            hd = hands[name]
            t = math.radians(hd["angle_deg"])
            pts = hd["outline_mm"]
            poly = [(v * math.cos(t) + r * math.sin(t), -v * math.sin(t) + r * math.cos(t)) for r, v in pts] + \
                   [(-v * math.cos(t) + r * math.sin(t), v * math.sin(t) + r * math.cos(t)) for r, v in pts[::-1]]
            cv2.polylines(ov, [np.array([P(p) for p in poly], np.int32)], True, (0, 255, 255), 1)
        sd = out["small_seconds"]
        c, t = sd["centre_mm"], math.radians(sd["angle_deg"])
        cv2.line(ov, P((c[0] - sd["tail_mm"] * math.sin(t), c[1] - sd["tail_mm"] * math.cos(t))),
                 P((c[0] + sd["length_mm"] * math.sin(t), c[1] + sd["length_mm"] * math.cos(t))), (255, 0, 255), 1)
        for sh in out["insert_prints"]:
            for lp in [sh["outer"]] + sh["holes"]:
                cv2.polylines(ov, [np.array([P(p) for p in lp], np.int32)], True, (255, 255, 0), 1)
        for k in ("logo", "print_mech", "print_swiss_made"):
            b = M[k]
            cv2.rectangle(ov, tuple(b[:2]), tuple(b[2:]), (0, 200, 255), 1)
        for y in M["lug_tips_y"]:
            cv2.line(ov, (500, y), (1400, y), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "bezel_rings_mm", "srgb", "lug", "checks", "crown")}, default=float),
          len(data["insert_prints"]), "insert prints ->", dest)
