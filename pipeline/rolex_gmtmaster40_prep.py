"""Phase 1 for the Rolex GMT-Master II 40 family (template: 126710BLNR 'Batman' Jubilee; 126720VTNR, 126711CHNR, 126713GRNR, 126710BLRO reuse this file read-only with their own key).
Native-size workflow (1920 x 2857 RGBA catalogue render, no enlargement): trace JSON, dial map and steel map, texture cap 2048 px.

    python3 -B -m pipeline.rolex_gmtmaster40_prep <key>      # e.g. 126710blnr
        reads    config/watches/rolex-gmtmaster40-<key>-measure.json (YOU measure the photo) and the photo named in it ("photo")
        writes   config/watches/rolex-gmtmaster40-<key>-trace.json, outputs/watches/rolex-gmtmaster40-<key>/{dial_photo,steel_photo}.jpg (+ .json)

Variant-named copy of rolex_submarinerdate41_prep (untouched; rotating-bezel Oyster template with the Cyclops lens outline) with ONE addition for the fourth (GMT) hand: the hand mode "polygons_px":
  mode "polygons_px": the hand outline is the union of the polygons listed in `polygons_px` ([[x, y], ...] native photo px; e.g. the blue GMT shaft as a rectangle plus the triangular head), outer contour. The hands dict may hold any number of
  hands (hour, minute, seconds, gmt ...), the build step turns every name in spec hands.z into a flat polygon. The rest is as the template: the scale anchored on the coin-edge bezel tips (case_edge_left_x mirrored about case_centre_x),
  crown rows that take a straight guard line (`crown_rows`), the ring list of a rotating bezel (dial_flat, crystal_edge, bezel_in, insert_out, rim_out, bezel_tip), the optional Cyclops outline `date.lens_px`, and TRACED hand outlines:
  mode "mask":   photo pixels with grey >= thr inside the ROI shapes (rect [s0, s1, w0, w1] / circle [s, w, r] / poly [[s, w], ...], s along the hand from the pivot, w perpendicular), the
                 component through the hub, closed, holes filled (the black facets and the thin bright rim of the photographed hand end up inside), outer contour;
  mode "shapes": the union of the ROI shapes themselves (thin seconds needle next to print and indices).
mm, x right, y toward 12, origin = hand pivot. The silhouette is the alpha above half (largest component).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
KEY = sys.argv[1].lower()
NAME = "rolex-gmtmaster40-%s" % KEY
MEASURE = ROOT / ("config/watches/%s-measure.json" % NAME)
PX = json.loads(MEASURE.read_text())
SRC = ROOT / PX["photo"]
TRACE = ROOT / ("config/watches/%s-trace.json" % NAME)
STEEL = ROOT / ("outputs/watches/%s/steel_photo.jpg" % NAME)
DIAL = ROOT / ("outputs/watches/%s/dial_photo.jpg" % NAME)
SS = 4  # supersampling of the hand masks


def hand_mask(shape_hw, pivot, deg, shapes, grey=None, thr=None):
    """Union of the ROI shapes (supersampled), optionally ANDed with grey >= thr; returns a uint8 mask at SS x resolution."""
    t = math.radians(deg)
    u, n = np.array([math.sin(t), -math.cos(t)]), np.array([math.cos(t), math.sin(t)])
    px = lambda s, w: (np.array(pivot) + u * s + n * w) * SS
    roi = np.zeros((shape_hw[0] * SS, shape_hw[1] * SS), np.uint8)
    for sh in shapes:
        if "rect" in sh:
            s0, s1, w0, w1 = sh["rect"]
            cv2.fillPoly(roi, [np.round(np.array([px(s0, w0), px(s1, w0), px(s1, w1), px(s0, w1)])).astype(np.int32)], 255)
        elif "poly" in sh:
            cv2.fillPoly(roi, [np.round(np.array([px(s, w) for s, w in sh["poly"]])).astype(np.int32)], 255)
        else:
            s, w, r = sh["circle"]
            c = px(s, w)
            cv2.circle(roi, (int(round(c[0])), int(round(c[1]))), int(round(r * SS)), 255, -1)
    if grey is not None:
        big = cv2.resize(grey, None, fx=SS, fy=SS, interpolation=cv2.INTER_LINEAR)
        roi = roi & ((big >= thr).astype(np.uint8) * 255)
    return roi


def trace_hand(h, grey, pivot, hub_r):
    if h["mode"] == "polygons_px":  # free-form hand (GMT hand): union of native-px polygons
        m = np.zeros((grey.shape[0] * SS, grey.shape[1] * SS), np.uint8)
        for pg in h["polygons_px"]:
            cv2.fillPoly(m, [np.round(np.array(pg) * SS).astype(np.int32)], 255)
        cnts, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        best = max(cnts, key=cv2.contourArea)
        return cv2.approxPolyDP(best, h.get("eps_px", 0.5) * SS, True)[:, 0, :] / SS, float(cv2.contourArea(best)) / SS / SS
    mask = hand_mask(grey.shape, pivot, h["angle_deg"], h["roi"], grey if h["mode"] == "mask" else None, h.get("thr"))
    if h["mode"] == "mask":
        cv2.circle(mask, (int(round(pivot[0] * SS)), int(round(pivot[1] * SS))), int((hub_r + 2) * SS), 255, -1)  # the hub joins the pieces of the hand
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((SS + 1, SS + 1), np.uint8))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    best = None
    for c in cnts:  # the component through the hub (mask mode) or the largest one
        if h["mode"] == "mask" and cv2.pointPolygonTest(c, (float(pivot[0] * SS), float(pivot[1] * SS)), False) < 0:
            continue
        if best is None or cv2.contourArea(c) > cv2.contourArea(best):
            best = c
    assert best is not None, "no hand contour"
    ap = cv2.approxPolyDP(best, h.get("eps_px", 0.5) * SS, True)[:, 0, :] / SS
    return ap, float(cv2.contourArea(best)) / SS / SS


def build():
    im = cv2.imread(str(SRC), cv2.IMREAD_UNCHANGED)
    px0, py0 = PX["pivot"]
    S = 2 * (PX["case_centre_x"] - PX["case_edge_left_x"]) / PX["case_mm"]
    n_, lab, stats, _ = cv2.connectedComponentsWithStats((im[..., 3] > 128).astype(np.uint8), connectivity=8)
    fg = lab == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))  # silhouette = largest alpha component above half
    cx_mm = (PX["case_centre_x"] - px0) / S
    rows = np.nonzero(fg.any(axis=1))[0]
    y_hi = math.floor((py0 - (rows[0] + 2)) / S * 4) / 4
    y_lo = -math.floor(((rows[-1] - 2) - py0) / S * 4) / 4
    c, cr = PX["crown"], PX["crown_rows"]
    prof = []
    for y in np.arange(y_lo, y_hi + 0.01, 0.25):
        r = int(round(py0 - y * S))
        xs = np.nonzero(fg[r])[0]
        left = (xs.min() - px0) / S
        right = (cr["right_x"] - px0) / S if cr["y0"] <= r <= cr["y1"] else (xs.max() + 1 - px0) / S  # crown rows: the straight guard line
        prof.append([round(float(y), 2), round(float(left), 3), round(float(right), 3)])
    cc = PX["ring_centre_px"]
    grey = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2GRAY)
    hands, hand_area = {}, {}
    for k, h in PX["hands"].items():
        poly, area = trace_hand(h, grey, (px0, py0), PX["hub_r"])
        t = math.radians(h["angle_deg"])
        ss = [(x - px0) * math.sin(t) - (y - py0) * math.cos(t) for x, y in poly]  # distance along the hand
        hands[k] = {"angle_deg": h["angle_deg"], "length_mm": round(max(ss) / S, 3), "tail_mm": round(-min(ss) / S, 3),
                    "outline_mm": [[round(float((x - px0) / S), 3), round(float(-(y - py0) / S), 3)] for x, y in poly]}
        hand_area[k] = round(area, 1)
    out = {"source": str(SRC.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0], "native_size_px": [im.shape[1], im.shape[0]],
           "anchor": "bezel (coin edge tip) diameter = case diameter %s mm = 2 x (case centre x %s - left tip x %s) / S at the pivot row" % (PX["case_mm"], PX["case_centre_x"], PX["case_edge_left_x"]),
           "rings_mm": {k: round(v / S, 3) for k, v in PX["rings"].items()},
           "ring_centre_mm": [round((cc[0] - px0) / S, 3), round(-(cc[1] - py0) / S, 3)],
           "silhouette_y_left_right_mm": prof,
           "tips_mm": [round((py0 - t) / S, 3) for t in PX["tip_rows_px"]],
           "hands": hands, "hand_area_px": hand_area, "hub_radius_mm": round(PX["hub_r"] / S, 3),
           "crown": {"x_mm": [round((c["x0"] - px0) / S, 3), round((c["x1"] - px0) / S, 3)], "fluted_to_mm": round((c["fluted_x"] - px0) / S, 3),
                     "radius_mm": round((c["y1"] - c["y0"]) / 2 / S, 3), "centre_y_mm": round(-((c["y0"] + c["y1"]) / 2 - py0) / S, 3)},
           "bracelet_px": PX.get("bracelet_px", {})}
    if "date" in PX:  # Cyclops lens outline (closed polygon) in mm from the pivot, x right / y up
        L = np.array(PX["date"]["lens_px"], float)
        lens = [[round(float((x - px0) / S), 3), round(float(-(y - py0) / S), 3)] for x, y in L]
        out["date"] = {"lens_mm": lens, "centre_mm": [round(float((L[:, 0].min() + L[:, 0].max()) / 2 - px0) / S, 3), round(float(-((L[:, 1].min() + L[:, 1].max()) / 2 - py0)) / S, 3)],
                       "size_mm": [round(float(np.ptp(L[:, 0])) / S, 3), round(float(np.ptp(L[:, 1])) / S, 3)]}
    TRACE.write_text(json.dumps(out, indent=1) + "\n")

    # dial map: native crop out to the bezel inner edge, centred on the pivot
    R = int(math.ceil(PX["rings"]["bezel_in"] + abs(cc[0] - px0) + abs(cc[1] - py0) + 3))
    crop = im[py0 - R:py0 + R, px0 - R:px0 + R, :3]
    DIAL.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(DIAL), crop, [cv2.IMWRITE_JPEG_QUALITY, PX.get("dial_quality", 93)])
    meta = {"source": out["source"], "centre_px": [px0, py0], "half_size_mm": round(R / S, 3), "size_px": int(crop.shape[0]), "scale": 1.0}
    DIAL.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n")
    # steel map: the whole watch (alpha bbox plus a 4 px margin) composited on grey, capped at steel_max_px on the long side
    cols = np.nonzero(fg.any(axis=0))[0]
    X0, Y0, X1, Y1 = int(cols[0]) - 4, int(rows[0]) - 4, int(cols[-1]) + 5, int(rows[-1]) + 5
    a = (im[Y0:Y1, X0:X1, 3] * fg[Y0:Y1, X0:X1])[..., None] / 255.0
    flat = (im[Y0:Y1, X0:X1, :3] * a + 128 * (1 - a)).astype(np.uint8)
    k = min(1.0, PX.get("steel_max_px", 2048) / max(flat.shape[:2]))
    steel = cv2.resize(flat, None, fx=k, fy=k, interpolation=cv2.INTER_AREA) if k < 1 else flat
    cv2.imwrite(str(STEEL), steel, [cv2.IMWRITE_JPEG_QUALITY, PX.get("steel_quality", 92)])
    STEEL.with_suffix(".json").write_text(json.dumps({"crop_px": [X0, Y0, X1, Y1], "size_px": [int(steel.shape[1]), int(steel.shape[0])], "scale": round(k, 5)}) + "\n")
    return {"scale_px_per_mm": out["scale_px_per_mm"], "rings_mm": out["rings_mm"], "ring_centre_mm": out["ring_centre_mm"], "tips_mm": out["tips_mm"], "crown": out["crown"],
            "hands": {k_: [v["length_mm"], v["tail_mm"], len(v["outline_mm"])] for k_, v in hands.items()},
            "dial_map": meta, "steel_map": {"size_px": [int(steel.shape[1]), int(steel.shape[0])], "scale": round(k, 5)}}


if __name__ == "__main__":
    print(json.dumps(build()))
