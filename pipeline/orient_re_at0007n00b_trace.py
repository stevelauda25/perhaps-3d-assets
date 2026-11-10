"""Measure the Orient Star RE-AT0007N00B front photo into mm. numpy + OpenCV.

    python3 -B -m pipeline.orient_re_at0007n00b_trace [out.json] [overlay.png]   # default config/watches/orient-re-at0007n00b-trace.json

Working reference since round 4: Orient's official straight front render (2000 x 2000, sharper than the 1000 x 1617 retailer
photo of rounds 2-3). The crystal ring is still read as an ellipse (it is nearly round here). The model follows the photo's own outline (the photo is projected on it from the front), so the outline is the
photo silhouette, not a circle:
  - head mask = not background, not black strap, the component holding the bezel, clipped to an envelope (case disk, four lug
    quads, crown box) that cuts the strap highlights away; the crown is cut out and built as its own part;
  - case outline = the mask edge per angle about the pivot; across the lugs and the crown it is interpolated;
  - lugs = the mask inside each lug quad; their inner (strap side) and tip edges are the quad edges read from gridded crops.
Anchor: case width through the pivot row (left flank to the right flank under the crown) = 39.3 mm (listing); the strap between
the lugs (20 mm listed) is the check. mm, x right, y toward 12, origin = hand pivot. Hands, crown, rings: MANUAL_PX (+-0.1 mm).
"""
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FRONT = ROOT / "references/orient-re-at0007n00b/front_official_2000x2000.webp"
OUT = ROOT / "config/watches/orient-re-at0007n00b-trace.json"
CASE_MM = 39.3  # listing: case diameter 39.3 mm
STEP_DEG = 2.0  # case outline samples

# Orient's official straight front render (2000 x 2000, time 10:08:37); read from gridded crops and rotated hand strips.
# Hand half widths are the round 3 values in mm (same watch) at this photo's scale.
MANUAL_PX = {
    "hand_pivot": [950, 877],
    # crystal opening (inner edge of the polished bezel): 452 / 1447 on the pivot row, 378 / 1360 on the pivot column
    "crystal_ellipse": {"centre": [950, 869], "rx": 497, "ry": 491},
    "dial_flat_px": 415,  # inner edge of the black chapter ring
    "hands": {"hour": {"tip": [724, 721], "tail": [1036, 937], "half_base": 21, "base_r": 71, "half_hub": 13},
              "minute": {"tip": [1284, 636], "tail": [845, 953], "half_base": 14, "base_r": 71, "half_hub": 12},
              "seconds": {"tip": [679, 1239], "tail": [1040, 757], "half_base": 3, "base_r": 26, "half_hub": 4.5}},
    "hub_px": 8,
    # envelope: case disk and one quad per lug (inner edge and tip edge exact, outer side generous: the white background cuts it)
    "case_disk": {"centre": [950, 884], "r": 590},
    "lug_quads": {"tl": [[590, 284], [684, 284], [684, 430], [400, 720]],
                  "tr": [[1252, 284], [1350, 284], [1580, 700], [1252, 430]],
                  "bl": [[400, 1040], [659, 1330], [659, 1555], [590, 1555]],
                  "br": [[1234, 1330], [1580, 1040], [1350, 1565], [1234, 1565]]},
    # strap between the lugs at the tips: x of the left / right lug inner edges, tip row
    "strap": {"top": {"x": [683, 1252], "tip_y": 285}, "bottom": {"x": [659, 1234], "tip_y": 1555}},
    # crown at 3: y top / bottom, x where it leaves the case flank and of its end
    "crown": {"y_top_bottom": [804, 997], "x_from_to": [1497, 1591], "teeth": 22},
}
ARTEFACTS = ["Roman numerals, applied indices, minute track, power reserve scale and hand, open-heart movement and the logo stay in the photo map (flat)",
             "hands are needles from the picked tips, tails and half widths; the photo shows on them, so a px of outline error shows dial pixels at the edge",
             "the deployant buckle and the strap keeper are not modelled"]


def head_mask(im, M):
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    cand = ((im.min(2) < 238) & (g >= 80)).astype(np.uint8)  # not white background, not black leather
    env = np.zeros(g.shape, np.uint8)
    cd = M["case_disk"]
    cv2.circle(env, tuple(cd["centre"]), cd["r"], 1, -1)
    for q in M["lug_quads"].values():
        cv2.fillPoly(env, [np.int32(q)], 1)
    cr = M["crown"]
    crown_box = np.zeros_like(env)
    cv2.rectangle(crown_box, (cr["x_from_to"][0], cr["y_top_bottom"][0] - 10), (g.shape[1] - 1, cr["y_top_bottom"][1] + 10), 1, -1)
    cand = cv2.morphologyEx(cand & env & (1 - crown_box), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    _, lab = cv2.connectedComponents(cand)
    px0, py0 = M["hand_pivot"]
    k = lab[py0, px0 - int(0.86 * M["case_disk"]["r"])]  # the polished bezel at 9 o'clock
    cnt = max(cv2.findContours((lab == k).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
    head = np.zeros_like(env)
    cv2.drawContours(head, [cnt], -1, 1, -1)  # dial, strap shadows inside the outline: filled
    return cv2.morphologyEx(head, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))


def trace(path=FRONT, overlay=None):
    im = cv2.imread(str(path))
    M = MANUAL_PX
    px0, py0 = M["hand_pivot"]
    head = head_mask(im, M)
    xs = np.nonzero(head[py0])[0]
    S = (xs.max() - xs.min() + 1) / CASE_MM
    mm = lambda p: [round((p[0] - px0) / S, 3), round(-(p[1] - py0) / S, 3)]
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [px0, py0],
           "anchor": f"case width through the pivot row = {CASE_MM} mm (listing)", "case_row_px": [int(xs.min()), int(xs.max())]}

    # ---- case outline: mask edge per angle about the pivot, interpolated across the lugs and the crown ----
    env_lugs = np.zeros_like(head)
    for q in M["lug_quads"].values():
        cv2.fillPoly(env_lugs, [np.int32(q)], 1)
    cr = M["crown"]
    angs = np.arange(0, 360, STEP_DEG)
    r_edge, blocked = [], []
    for deg in angs:
        a = math.radians(deg)
        rr = np.arange(int(0.55 * M["case_disk"]["r"]), int(1.1 * M["case_disk"]["r"]))
        xx = np.clip(np.round(px0 + rr * math.sin(a)).astype(int), 0, im.shape[1] - 1)
        yy = np.clip(np.round(py0 - rr * math.cos(a)).astype(int), 0, im.shape[0] - 1)
        inside = head[yy, xx] > 0
        r_edge.append(float(rr[np.argmin(inside)]) if not inside.all() else 999.0)  # first px outside the head
        e = min(int(r_edge[-1]) - rr[0] - 2, len(rr) - 1)  # just inside the edge: a lug edge, not the case edge
        lug = env_lugs[yy[e], xx[e]] > 0
        crown = cr["y_top_bottom"][0] - 30 <= py0 - 0.95 * M["case_disk"]["r"] * math.cos(a) <= cr["y_top_bottom"][1] + 30 and math.sin(a) > 0.8
        blocked.append(bool(lug or crown))
    r_edge, blocked = np.array(r_edge), np.array(blocked)
    ok = np.nonzero(~blocked)[0]
    r_case = np.interp(np.arange(len(angs)), np.r_[ok - len(angs), ok, ok + len(angs)], np.r_[r_edge[ok], r_edge[ok], r_edge[ok]])
    r_case = np.convolve(np.r_[r_case[-2:], r_case, r_case[:2]], np.ones(5) / 5, mode="valid")  # 10 deg mean drops the edge noise
    out["case_polar_mm"] = {"step_deg": STEP_DEG, "r": [round(float(r) / S, 3) for r in r_case]}
    ce = M["crystal_ellipse"]
    out["crystal_ellipse_mm"] = {"centre": mm(ce["centre"]), "rx": round(ce["rx"] / S, 3), "ry": round(ce["ry"] / S, 3)}
    out["dial_flat_mm"] = round(M["dial_flat_px"] / S, 3)

    # ---- lugs: the head mask inside each quad ----
    lugs = {}
    for key, q in M["lug_quads"].items():
        qm = np.zeros_like(head)
        cv2.fillPoly(qm, [np.int32(q)], 1)
        part = (head & qm).astype(np.uint8)
        cnt = max(cv2.findContours(part, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
        poly = cv2.approxPolyDP(cnt, 1.0, True)[:, 0]
        d = [math.hypot(x - px0, y - py0) for x, y in poly]
        lugs[key] = {"outline_mm": [mm(p) for p in poly[::-1]], "r_max_mm": round(max(d) / S, 3)}  # image y down -> ccw in mm
    out["lugs"] = lugs
    out["strap_mm"] = {k: {"x": [mm((x, 0))[0] for x in v["x"]], "tip_y": abs(mm((0, v["tip_y"]))[1])} for k, v in M["strap"].items()}
    out["checks"] = {"strap_width_mm": {k: round(v["x"][1] - v["x"][0], 2) for k, v in out["strap_mm"].items()},
                     "lug_to_lug_mm": round(out["strap_mm"]["top"]["tip_y"] + out["strap_mm"]["bottom"]["tip_y"], 2)}

    # ---- hands: needles from tip to tail, widest at base_r ----
    ang = lambda dx, dy: math.degrees(math.atan2(dx, -dy)) % 360
    hands = {}
    o = np.float32([px0, py0])
    for name, h in M["hands"].items():
        u = np.float32(h["tip"]) - o
        L = float(np.hypot(*u))
        u /= L
        n = np.float32([-u[1], u[0]])
        Lt = float(np.hypot(*(np.float32(h["tail"]) - o)))
        b = o + u * h["base_r"]
        poly = [o + u * L, b - n * h["half_base"], o - n * h["half_hub"], o - u * Lt, o + n * h["half_hub"], b + n * h["half_base"]]
        hands[name] = {"angle_deg": round(ang(*u), 2), "length_mm": round(L / S, 3), "outline_mm": [mm(p) for p in poly]}
    out["hands"] = hands
    out["hub_mm"] = round(M["hub_px"] / S, 3)

    yt, yb = cr["y_top_bottom"]
    out["crown"] = {"centre_y_mm": mm((0, (yt + yb) / 2))[1], "radius_mm": round((yb - yt) / 2 / S, 3), "teeth": cr["teeth"],
                    "x_from_to_mm": [mm((x, 0))[0] for x in cr["x_from_to"]]}
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = cv2.cvtColor(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR) // 2 + 60
        Pp = lambda xy: (int(round(px0 + xy[0] * S)), int(round(py0 - xy[1] * S)))
        case_pts = [Pp((r * math.sin(math.radians(a)), r * math.cos(math.radians(a)))) for a, r in zip(angs, out["case_polar_mm"]["r"])]
        cv2.polylines(ov, [np.array(case_pts)], True, (0, 0, 255), 2)
        cv2.ellipse(ov, tuple(ce["centre"]), (ce["rx"], ce["ry"]), 0, 0, 360, (255, 128, 0), 2)
        cv2.circle(ov, (px0, py0), M["dial_flat_px"], (255, 128, 0), 1)
        for p in [v["outline_mm"] for v in lugs.values()] + [v["outline_mm"] for v in hands.values()]:
            cv2.polylines(ov, [np.array([Pp(q) for q in p])], True, (0, 200, 255), 2)
        for k, sy in (("top", 1), ("bottom", -1)):
            s = out["strap_mm"][k]
            cv2.line(ov, Pp((s["x"][0], sy * s["tip_y"])), Pp((s["x"][1], sy * s["tip_y"])), (0, 255, 0), 2)
        k = out["crown"]
        for x in k["x_from_to_mm"]:
            cv2.line(ov, Pp((x, k["centre_y_mm"] - k["radius_mm"])), Pp((x, k["centre_y_mm"] + k["radius_mm"])), (255, 0, 128), 2)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "case_row_px", "crystal_ellipse_mm", "dial_flat_mm", "strap_mm", "checks", "crown")},
                     default=float), "->", dest)
    r = data["case_polar_mm"]["r"]
    print({k: (v["angle_deg"], v["length_mm"]) for k, v in data["hands"].items()}, {k: (v["r_max_mm"], len(v["outline_mm"])) for k, v in data["lugs"].items()},
          "case r", min(r), max(r))
