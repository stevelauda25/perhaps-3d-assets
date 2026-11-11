"""Measure the Tissot T127.407.11.081.00 (Gentleman Powermatic 80 Open Heart, 40 mm, steel bracelet) official front render
(1680 x 1680, transparent background) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.tissot_t127407_trace [out.json] [overlay.png]   # default config/watches/tissot-t127.407.11.081.00-trace.json

Same method as pipeline/hamilton_h70515137_trace.py. Anchor: 40 mm case (Tissot official) from a circle fitted to both case
flanks on the alpha (rows clear of the lugs and the crown). mm, x right, y toward 12, origin = hand pivot. Hands, applied
indices, open-heart aperture, crown and bracelet joints are read from gridded and hand-aligned crops (MANUAL_PX).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

from pipeline.hamilton_h77616533_trace import load
from pipeline.watch_trace import fit_circle

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/tissot-t127.407.11.081.00/front_official_1680x1680.png"
OUT = ROOT / "config/watches/tissot-t127.407.11.081.00-trace.json"
CASE_MM = 40.0  # Tissot official
LISTED = {"lug_width_mm": 21.0, "thickness_mm": 11.5}

MANUAL_PX = {
    "hand_pivot": [842, 844],
    # outlines: [distance from the pivot, half width]; faceted baton with a kite tail, needle tip, lume slot
    "hour": {"angle_deg": 304.5, "outline": [[-62, 1], [-32, 19], [-12, 9], [10, 11], [158, 11], [176, 6], [190, 1]], "lume": [100, 160]},
    "minute": {"angle_deg": 51.0, "outline": [[-62, 1], [-32, 19], [-12, 9], [10, 11], [255, 9.5], [275, 5], [292, 1]], "lume": [110, 255]},
    "seconds": {"angle_deg": 216.8, "length": 300, "half": 2.5, "tail": 75},
    "hub_radius_px": [13, 6],
    "lume_half_px": 5,
    # applied faceted batons: inner end narrow, outer end wide; polished frame, brushed centre
    "index": {"inner": 214, "outer": 297, "half_inner": 4.5, "half_outer": 16, "frame": 4},
    "rings_px": {"dial": 320, "bezel_in": 340},  # dial flat to 320, dark flange to 340, polished sloped bezel to the case edge
    # open-heart aperture: outline just outside the polished rim
    "aperture": [[644, 790], [652, 750], [672, 722], [700, 702], [735, 694], [752, 686], [762, 660], [780, 632], [805, 612], [840, 600],
                 [880, 604], [915, 620], [945, 650], [964, 690], [968, 735], [958, 775], [935, 805], [900, 826], [865, 836], [835, 842],
                 [815, 848], [790, 864], [750, 872], [710, 866], [675, 848], [652, 822]],
    "crown": {"angle_deg": 90.0, "r": [387, 448], "radius": 63, "teeth": 14},
    "lug_inner_x_px": [640, 1045],
    "lug_tips_y": [377, 1312],
    "logo": [770, 915, 918, 950],
    "print_1853": [810, 952, 878, 978],
    "print_powermatic": [738, 992, 948, 1018],
    "print_swiss_made": [690, 1138, 1000, 1165],
    # bracelet: three columns; outer links 79 px from the lug tip, polished centre pieces 41 px starting 3 px past the tip
    "bracelet": {"outer_pitch": 79, "centre_pitch": 41, "centre_start_past_tip": 3, "centre_x": [757, 922]},
}
ARTEFACTS = ["official render: the bracelet curves away from the camera, the link pitch is read on the first links past the 6 o'clock lug tips",
             "sunray dial, prints, lume dots, minute track and the open-heart movement stay in the dial map"]


def trace(path=FRONT, overlay=None):
    im = load(path)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(float)
    fg = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)[..., 3] > 128
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    pts = []
    for y in list(range(650, 780)) + list(range(930, 1050)):  # both flanks, clear of the lugs and the crown
        xs = np.nonzero(fg[y])[0]
        pts += [(xs.min(), y), (xs.max(), y)]
    ccx, ccy, case_r = fit_circle(np.array(pts, float))
    S = 2 * case_r / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    f = lambda v: round(v / S, 3)
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width = {CASE_MM} mm (Tissot official), both case flanks", "case": {"radius_mm": round(case_r / S, 3), "centre_mm": mm((ccx, ccy))},
           "rings_mm": {k: f(v) for k, v in M["rings_px"].items()}}

    prof = []
    for y_mm in np.arange(-30, 30.01, 0.25):
        row = int(round(py0 - y_mm * S))
        xs = np.nonzero(fg[row])[0]
        prof.append([round(float(y_mm), 2), round((px0 - xs.min()) / S, 3)])  # left edge: the crown and the shadow are on the right
    out["silhouette_left_mm"] = prof
    t0, t1 = M["lug_tips_y"]
    xi0, xi1 = M["lug_inner_x_px"]
    out["lug"] = {"photo_tips_mm": [f(py0 - t0), f(t1 - py0)], "tip_mm": f((t1 - t0) / 2), "inner_x_mm": f((xi1 - xi0) / 2)}
    out["checks"] = {"photo_lug_to_lug_mm": f(t1 - t0), "lug_gap_mm": f(xi1 - xi0), "listed": LISTED}

    hands = {}
    for name in ("hour", "minute"):
        hm = M[name]
        hands[name] = {"angle_deg": hm["angle_deg"], "outline_mm": [[f(r), f(v)] for r, v in hm["outline"]],
                       "lume_mm": [f(v) for v in hm["lume"]], "length_mm": f(hm["outline"][-1][0])}
    sm = M["seconds"]
    hands["seconds"] = {"angle_deg": sm["angle_deg"], "length_mm": f(sm["length"]), "half_width_mm": f(sm["half"]), "tail_mm": f(sm["tail"])}
    out["hands"] = hands
    out["hub_radius_mm"] = [f(v) for v in M["hub_radius_px"]]
    out["lume_half_mm"] = f(M["lume_half_px"])
    ix = M["index"]
    out["index"] = {k: f(v) for k, v in ix.items()}
    out["aperture_mm"] = [mm(p) for p in M["aperture"]]
    cr = M["crown"]
    out["crown"] = {"angle_deg": cr["angle_deg"], "r_mm": [f(v) for v in cr["r"]], "radius_mm": f(cr["radius"]), "teeth": cr["teeth"]}
    box = lambda b: {"x0_y0_x1_y1_mm": mm(b[:2]) + mm(b[2:]), "size_mm": [f(b[2] - b[0]), f(b[3] - b[1])]}
    for k in ("logo", "print_1853", "print_powermatic", "print_swiss_made"):
        out[k] = box(M[k])
    b = M["bracelet"]
    out["bracelet_pitch_mm"] = {"outer": f(b["outer_pitch"]), "centre": f(b["centre_pitch"])}
    out["bracelet_centre_start_past_tip_mm"] = f(b["centre_start_past_tip"])
    out["bracelet_centre_half_mm"] = f((b["centre_x"][1] - b["centre_x"][0]) / 2)
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(gray.astype(np.uint8), cv2.COLOR_GRAY2BGR) // 2
        P = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        cv2.circle(ov, (int(ccx), int(ccy)), int(case_r), (0, 128, 255), 2)
        for v in M["rings_px"].values():
            cv2.circle(ov, (px0, py0), v, (0, 0, 255), 1)
        cv2.polylines(ov, [np.array(M["aperture"], np.int32)], True, (255, 0, 255), 1)
        for name in ("hour", "minute"):
            hd = hands[name]
            t = math.radians(hd["angle_deg"])
            pts_ = hd["outline_mm"]
            poly = [(v * math.cos(t) + r * math.sin(t), -v * math.sin(t) + r * math.cos(t)) for r, v in pts_] + \
                   [(-v * math.cos(t) + r * math.sin(t), v * math.sin(t) + r * math.cos(t)) for r, v in pts_[::-1]]
            cv2.polylines(ov, [np.array([P(p) for p in poly], np.int32)], True, (0, 255, 255), 1)
        sd = hands["seconds"]
        t = math.radians(sd["angle_deg"])
        cv2.line(ov, P((-sd["tail_mm"] * math.sin(t), -sd["tail_mm"] * math.cos(t))), P((sd["length_mm"] * math.sin(t), sd["length_mm"] * math.cos(t))), (0, 255, 255), 1)
        for h in range(12):
            t = math.radians(h * 30)
            q = [(ix["half_inner"], ix["inner"]), (ix["half_outer"], ix["outer"]), (-ix["half_outer"], ix["outer"]), (-ix["half_inner"], ix["inner"])]
            cv2.polylines(ov, [np.array([(int(px0 + x * math.cos(t) + y * math.sin(t)), int(py0 - (-x * math.sin(t) + y * math.cos(t)))) for x, y in q], np.int32)],
                          True, (0, 255, 0), 1)
        for k in ("logo", "print_1853", "print_powermatic", "print_swiss_made"):
            bb = M[k]
            cv2.rectangle(ov, tuple(bb[:2]), tuple(bb[2:]), (0, 200, 255), 1)
        for y in M["lug_tips_y"]:
            cv2.line(ov, (560, y), (1130, y), (255, 128, 0), 1)
        for x in M["lug_inner_x_px"] + b["centre_x"]:
            cv2.line(ov, (x, 140), (x, 1540), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case", "rings_mm", "lug", "checks", "crown", "bracelet_pitch_mm",
                                           "bracelet_centre_half_mm", "index")}, default=float), "->", dest)
