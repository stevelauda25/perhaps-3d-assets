"""Phase 1 for the Rolex Cosmograph Daytona 40 family (template: 126500LN steel, ceramic bezel, Oyster bracelet; 126503, 126505, 126518LN, 126508 yellow / green, 126519LN, 126506, 126506A reuse this file read-only with their own key).
Native-size workflow (1920 x 2857 RGBA catalogue render, no enlargement): trace JSON, dial map and steel map, texture cap 2048 px.

    python3 -B -m pipeline.rolex_daytona40_prep <key>      # e.g. 126500ln
        reads    config/watches/rolex-daytona40-<key>-measure.json (YOU measure the photo) and the photo named in it ("photo")
        writes   config/watches/rolex-daytona40-<key>-trace.json, outputs/watches/rolex-daytona40-<key>/{dial_photo,steel_photo}.jpg (+ .json)

Variant-named copy of rolex_gmtmaster40_prep (untouched; rotating-bezel Oyster template) adapted to the Daytona:
  - no Cyclops lens, no coin edge: the bezel is a fixed ceramic ring (rings: dial_flat, crystal_edge, bezel_in, insert_in) plus an optional ellipse `bezel_ellipse` for the ceramic outer edge (the render is a few percent
    flatter vertically at the bezel than at the flange: centre / rx / ry in px) and `case_ring_ellipse` for the steel edge outside it;
  - the case outline is the CONTOUR of the alpha silhouette clipped between the lug tip rows (`tip_rows_px`): it keeps the crown guards, the two pusher barrels and the slits between lug horn and bracelet exactly
    (written as trace.case_outline_mm); the row profile `silhouette_y_left_right_mm` (0.25 mm rows) only feeds the bracelet edges;
  - hands: every name in `hands` becomes a flat polygon. Modes: "mask" (grey >= thr inside ROI shapes, for dark hands on a pale dial), "shapes" (union of ROI shapes given as [s, w] polygons / rects / circles
    along the hand), "polygons_px" (union of native-px polygons, e.g. a sub-dial hand = hub circle + needle). `pivot_px` per hand (default `hand_pivot_px`, default `pivot`) is the point the [s, w] shapes are measured from;
    the outlines are always written in mm about `pivot` (the origin);
  - `subdials` (centre_px, r_px) become mm entries for the small hub discs; `crown` (axis along +x) and `pushers` (list of {origin_px, angle_deg, ...}) are written in mm for the step;
  - the dial map is a native crop centred on the integer pivot; trace/dial json carry the sub-pixel offset of the hub so the planar UV stays registered with the steel map.
mm, x right, y toward 12, origin = pivot. The silhouette is the alpha above half (largest component).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
KEY = sys.argv[1].lower()
NAME = "rolex-daytona40-%s" % KEY
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
    if h["mode"] == "polygons_px":  # free-form hand: union of native-px polygons
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
    hp = PX.get("hand_pivot_px", [px0, py0])
    S = 2 * (PX["case_centre_x"] - PX["case_edge_left_x"]) / PX["case_mm"]
    n_, lab, stats, _ = cv2.connectedComponentsWithStats((im[..., 3] > 128).astype(np.uint8), connectivity=8)
    fg = lab == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))  # silhouette = largest alpha component above half
    cx_mm = (PX["case_centre_x"] - px0) / S
    rows = np.nonzero(fg.any(axis=1))[0]
    y_hi = math.floor((py0 - (rows[0] + 2)) / S * 4) / 4
    y_lo = -math.floor(((rows[-1] - 2) - py0) / S * 4) / 4
    prof = []
    for y in np.arange(y_lo, y_hi + 0.01, 0.25):
        r = int(round(py0 - y * S))
        xs = np.nonzero(fg[r])[0]
        prof.append([round(float(y), 2), round((xs.min() - px0) / S, 3), round((xs.max() + 1 - px0) / S, 3)])
    # case outline: contour of the silhouette between the two lug tip rows (horns, crown guards, pusher barrels, crown, slits kept)
    t_top, t_bot = PX["tip_rows_px"]
    clip = np.zeros(fg.shape, np.uint8)
    clip[int(math.ceil(t_top)):int(math.floor(t_bot))] = fg[int(math.ceil(t_top)):int(math.floor(t_bot))]
    clip4 = cv2.resize(clip, None, fx=SS, fy=SS, interpolation=cv2.INTER_NEAREST)  # contour at 4x: the polygon follows the pixel edges within 1/8 px
    cnts, _ = cv2.findContours(clip4, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    big = max(cnts, key=cv2.contourArea)
    ap = cv2.approxPolyDP(big, PX.get("outline_eps_px", 0.45) * SS, True)[:, 0, :].astype(float) / SS + 0.5 / SS
    outline = [[round(float((x - px0) / S), 3), round(float(-(y - py0) / S), 3)] for x, y in ap]
    cc = PX["ring_centre_px"]
    grey = cv2.cvtColor(im[..., :3], cv2.COLOR_BGR2GRAY)
    hands, hand_area = {}, {}
    for k, h in PX["hands"].items():
        piv = h.get("pivot_px", hp)
        poly, area = trace_hand(h, grey, piv, PX["hub_r"])
        t = math.radians(h.get("angle_deg", 0.0))
        ss = [(x - piv[0]) * math.sin(t) - (y - piv[1]) * math.cos(t) for x, y in poly]  # distance along the hand
        hands[k] = {"angle_deg": h.get("angle_deg", 0.0), "length_mm": round(max(ss) / S, 3), "tail_mm": round(-min(ss) / S, 3),
                    "outline_mm": [[round(float((x - px0) / S), 3), round(float(-(y - py0) / S), 3)] for x, y in poly]}
        hand_area[k] = round(area, 1)
    c = PX["crown"]
    out = {"source": str(SRC.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0], "native_size_px": [im.shape[1], im.shape[0]],
           "anchor": "case diameter %s mm = 2 x (case centre x %s - left case edge x %s) / S at the widest row (the flank left of the ceramic bezel)" % (PX["case_mm"], PX["case_centre_x"], PX["case_edge_left_x"]),
           "rings_mm": {k: round(v / S, 3) for k, v in PX["rings"].items()},
           "ring_centre_mm": [round((cc[0] - px0) / S, 3), round(-(cc[1] - py0) / S, 3)],
           "silhouette_y_left_right_mm": prof, "case_outline_mm": outline,
           "tips_mm": [round((py0 - t) / S, 3) for t in PX["tip_rows_px"]],
           "hands": hands, "hand_area_px": hand_area, "hub_radius_mm": round(PX["hub_r"] / S, 3),
           "hub_offset_mm": [round((hp[0] - px0) / S, 3), round(-(hp[1] - py0) / S, 3)],
           "crown": {"x_mm": [round((c["x0"] - px0) / S, 3), round((c["x1"] - px0) / S, 3)], "fluted_to_mm": round((c["fluted_x"] - px0) / S, 3),
                     "radius_mm": round((c["y1"] - c["y0"]) / 2 / S, 3), "centre_y_mm": round(-((c["y0"] + c["y1"]) / 2 - py0) / S, 3)},
           "bracelet_px": PX.get("bracelet_px", {})}
    if "bezel_ellipse" in PX:  # name -> {centre_px, rx, ry}
        out["bezel_ellipse_mm"] = {k: {"centre_mm": [round((v["centre_px"][0] - px0) / S, 3), round(-(v["centre_px"][1] - py0) / S, 3)], "rx_mm": round(v["rx"] / S, 3), "ry_mm": round(v["ry"] / S, 3)}
                                   for k, v in PX["bezel_ellipse"].items()}
    if "subdials" in PX:
        out["subdials_mm"] = [{"name": s["name"], "x_mm": round((s["centre_px"][0] - px0) / S, 3), "y_mm": round(-(s["centre_px"][1] - py0) / S, 3), "r_mm": round(s["r_px"] / S, 3)} for s in PX["subdials"]]
    if "pushers" in PX:  # axis through origin_px at angle_deg (counter-clockwise from +x, y up); distances in px along the axis
        pu = PX["pushers"]
        out["pushers"] = {"origin_mm": [round((pu["origin_px"][0] - px0) / S, 4), round(-(pu["origin_px"][1] - py0) / S, 4)], "angles_deg": pu["angles_deg"], "radius_mm": round(pu["radius_px"] / S, 3),
                          "neck_from_mm": round(pu["neck_from_px"] / S, 3), "r_from_mm": round(pu["ring_from_px"] / S, 3), "fluted_to_mm": round(pu["ring_to_px"] / S, 3), "r_to_mm": round(pu["end_px"] / S, 3),
                          "cap_radius_fraction": round(pu["cap_radius_px"] / pu["radius_px"], 4), "neck_radius_fraction": round(pu["neck_radius_px"] / pu["radius_px"], 4)}
    TRACE.write_text(json.dumps(out, indent=1) + "\n")

    # dial map: native crop out to the bezel inner edge, centred on the integer pivot; the sub-pixel hub offset is recorded for the planar UV
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
            "outline_points": len(outline), "hands": {k_: [v["length_mm"], v["tail_mm"], len(v["outline_mm"])] for k_, v in hands.items()},
            "dial_map": meta, "steel_map": {"size_px": [int(steel.shape[1]), int(steel.shape[0])], "scale": round(k, 5)}}


if __name__ == "__main__":
    print(json.dumps(build()))
