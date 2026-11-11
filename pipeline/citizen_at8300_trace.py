"""Measure the Citizen AT8300-58L (Promaster Navihawk A-T, 41 mm, blue dial, slide rule, steel bracelet) official front render
(1366 x 2048, transparent background) into mm. Host-side, numpy + OpenCV.

    python3 -B -m pipeline.citizen_at8300_trace [out.json] [overlay.png]   # default config/watches/citizen-at8300-58l-trace.json

Anchor: 41 mm case (Citizen listing) = the diameter of a circle fitted to the bezel's outer edge on the alpha (the bezel is the
widest round part). Origin = the dial centre (mid point of the three subdial hubs); the main hand stack shows 0.2 mm off it in
the render (parallax) and is placed on the origin. mm, x right, y toward 12. The hour, minute and chronograph hands and the
applied indices are traced from the white mask (outline and lume as polygons in their photographed orientation); hub,
counterweight, subdials, crowns, pushers, crown guard, horns and bracelet joints are read from gridded crops (MANUAL_PX,
about +-1 px = +-0.04 mm). The slide rules, city ring, dial, subdials and their needles and all print stay in the dial map.
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
FRONT = ROOT / "references/citizen-at8300-58l/front_official_1366x2048.png"
OUT = ROOT / "config/watches/citizen-at8300-58l-trace.json"
CASE_MM = 41.0  # Citizen listing: case width (the bezel)
LISTED = {"case_mm": 41.0, "thickness_mm": 11.87, "band_mm": 21.0}

MANUAL_PX = {
    "dial_centre": [638.6, 904.6],  # mid point of the 12 and 6 subdial hubs; the 9 subdial hub lies on the same row
    "hand_pivot": [633.5, 901.5],
    # traced hands: wedge about the pivot (deg, half width px, radius range px) and a seed radius on the axis
    "hour": {"angle_deg": 302.8, "wedge": [48, 18, 230], "seed": 120},
    "minute": {"angle_deg": 56.5, "wedge": [40, 18, 330], "seed": 160},
    # chronograph: thin white needle (traced, it touches the subdial print, so only its axis and length are used)
    "chrono": {"angle_deg": 209.1, "tip": 365, "half": [3.5, 2.0], "tail": 18},
    # chronograph counterweight: black, tapered to (697, 792), with a C hook to the right and an S curl to the left of its
    # root; hooks as [angle, radius, disc radius] about the pivot
    "counter": {"angle_deg": 29.8, "length": 127, "half": [14, 3], "hooks": [[51.6, 49, 15], [4.1, 48.6, 13]]},
    "hub_radius_px": [36, 8],  # black hub disc, white screw
    "subs": {"centres": [[640.5, 705.5], [440.0, 905.7], [636.7, 1103.3]], "hub": 22},
    # bezel 508-583, outer slide rule 448-508, inner slide rule 392-447, grey city ring 368-392, dial inside (about the centre)
    "rings_px": {"dial": 368, "city": 392, "inner_rule": 447, "bezel_in": 508},
    "index_band": [250, 372],
    "crown": {"angle_deg": 90.4, "r": [590, 690], "radius": 75, "teeth": 30},  # alpha: rows 835-985, right edge 1329
    "crown_left": {"angle_deg": 239.1, "r": [560, 650], "radius": 72, "teeth": 30},
    "pushers": [{"angle_deg": 61.7, "r": [560, 655], "radius": 46}, {"angle_deg": 118.3, "r": [560, 655], "radius": 46}],
    # crown guard on the right flank and the shoulder by the left crown: outlines in px
    "guard": [[1150, 686], [1189, 686], [1230, 699], [1249, 786], [1249, 1114], [1230, 1167], [1189, 1183], [1150, 1183]],
    "left_shoulder": [[110, 1030], [70, 1040], [52, 1080], [58, 1125], [100, 1137], [130, 1137]],
    "right_rows": [500, 1290],  # rows where pushers, guard and crown widen the right side
    "left_rows": [1020, 1300],  # rows where the left crown and its shoulder widen the left side
    "horn_tips_y": [275, 1575],
    "end_link": {"half": 282, "tips_y": [256, 1593]},  # the end link between the horns, a little past their tips
    "bracelet": {"centre": [501, 780], "pitch_rows": {"centre": [1546, 1675, 1814], "outer": [1593, 1725, 1875]}},
    "date": [868, 848, 966, 930],
}
ARTEFACTS = ["the horns show 0.8 mm lower than the bezel in the render (camera slightly below): the case is drawn symmetric about the centre",
             "the render's silhouette sits 7 px right of the hand pivot and 2 px right of the dial centre",
             "bracelet pitch from the bottom end, where the links lie flat; the top end turns away from the camera"]


def traced(mask, to_mm, eps=0.8):
    cs, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)
    c = cv2.approxPolyDP(c, eps, True)[:, 0, :]
    return [to_mm(p) for p in c]


def trace(path=FRONT, overlay=None):
    im = load(path)
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(float)
    alpha = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)[..., 3] > 128
    h, w = alpha.shape
    M = MANUAL_PX
    cx, cy = M["dial_centre"]
    hx, hy = M["hand_pivot"]

    # bezel outer edge on the alpha where the bezel is the silhouette (clear of crowns, pushers, guard and horns)
    # (between the left crown's shoulder at 246-258 deg and the horn at 311 deg); the bezel is concentric with the dial, so
    # the radius is taken about the dial centre and the free fit is kept as a check
    pts = []
    for a in np.arange(262, 305.1, 0.5):
        rs = np.arange(540, 620, 0.5)
        xs, ys = cx + rs * np.sin(np.radians(a)), cy - rs * np.cos(np.radians(a))
        fg = alpha[ys.astype(int), xs.astype(int)]
        k = next(i for i in range(1, len(rs)) if fg[i - 1] and not fg[i])
        pts.append((xs[k], ys[k]))
    pts = np.array(pts)
    fcx, fcy, fr = fit_circle(pts)
    bcx, bcy, br = cx, cy, float(np.median(np.hypot(pts[:, 0] - cx, pts[:, 1] - cy)))
    S = 2 * br / CASE_MM
    mm = lambda p: [round((float(p[0]) - cx) / S, 3), round(-(float(p[1]) - cy) / S, 3)]
    f = lambda v: round(float(v) / S, 3)
    out = {"source": str(path.relative_to(ROOT)), "scale_px_per_mm": round(S, 4), "origin_px": [cx, cy], "hand_pivot_px": [hx, hy],
           "anchor": f"case width = {CASE_MM} mm (Citizen listing) = bezel circle fitted on the alpha",
           "bezel_fit": {"radius_mm": f(br), "free_fit": {"centre_mm": mm((fcx, fcy)), "radius_mm": f(fr)}, "points": len(pts)},
           "rings_mm": dict({k: f(v) for k, v in M["rings_px"].items()}, bezel_out=f(br))}

    # silhouette rows: per row the left and right half widths about the centre
    r0, r1 = M["right_rows"]
    l0, l1 = M["left_rows"]
    rows = []
    for y in range(M["horn_tips_y"][0], M["horn_tips_y"][1] + 1, 2):
        xs = np.nonzero(alpha[y])[0]
        L, R = cx - xs.min(), xs.max() + 1 - cx
        yr = -(y - cy)
        circ = math.sqrt(max(br ** 2 - (y - bcy) ** 2, 0))
        right_busy, left_busy = r0 <= y <= r1, l0 <= y <= l1
        half = circ if right_busy and left_busy else (L if right_busy else (R if left_busy else (L + R) / 2))
        rows.append([f(yr), f(half)])
    out["case_half_width_mm"] = rows
    t0, t1 = M["horn_tips_y"]
    out["horn_tip_mm"] = f((t1 - t0) / 2)
    el = M["end_link"]
    out["end_link"] = {"half_mm": f(el["half"]), "tip_mm": f((el["tips_y"][1] - el["tips_y"][0]) / 2)}
    b = M["bracelet"]
    pc, po = b["pitch_rows"]["centre"], b["pitch_rows"]["outer"]
    out["bracelet"] = {"centre_half_mm": f((b["centre"][1] - b["centre"][0]) / 2),
                       "pitch_mm": f(np.mean(np.diff(pc).tolist() + np.diff(po).tolist())),
                       "centre_lead_mm": f(po[0] - pc[0])}  # the centre links start this much nearer the case
    widths = [np.nonzero(alpha[y])[0] for y in range(40, 240, 4)]
    out["bracelet"]["width_mm_near_case"] = f(np.ptp(widths[-1]))
    out["checks"] = {"horn_to_horn_mm": f(t1 - t0), "bracelet_width_mm": out["bracelet"]["width_mm_near_case"], "listed": LISTED}

    # hands: white mask in a wedge about the pivot, the component through the seed; lume = the matt grey inside the bright frame
    white = (hsv[..., 1] < 45) & (hsv[..., 2] > 150)
    yy, xx = np.mgrid[0:h, 0:w]
    to_mm = lambda p: mm(p)
    hands = {}
    for name in ("hour", "minute"):
        hm = M[name]
        a = math.radians(hm["angle_deg"])
        ux, uy = math.sin(a), -math.cos(a)
        al = (xx - hx) * ux + (yy - hy) * uy
        ac = np.abs(-(xx - hx) * uy + (yy - hy) * ux)
        hw, s0, s1 = hm["wedge"]
        m = (white & (al > s0) & (al < s1) & (ac < hw)).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, lab = cv2.connectedComponents(m)
        seed = lab[int(round(hy + hm["seed"] * uy)), int(round(hx + hm["seed"] * ux))]
        assert seed > 0, name
        hand = lab == seed
        hand = cv2.morphologyEx(hand.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)).astype(bool)
        entry = {"angle_deg": hm["angle_deg"], "outline_mm": traced(hand, to_mm), "length_mm": f(al[hand].max())}
        lume = hand & (hsv[..., 2] < 232)
        lume = cv2.morphologyEx(lume.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)).astype(bool)
        entry["lume_mm"] = traced(lume, to_mm, 1.2)
        hands[name] = entry
    c = M["chrono"]
    hands["chrono"] = {"angle_deg": c["angle_deg"], "tip_mm": f(c["tip"]), "half_mm": [f(v) for v in c["half"]], "tail_mm": f(c["tail"])}
    out["hands"] = hands
    c = M["counter"]
    out["counter"] = {"angle_deg": c["angle_deg"], "length_mm": f(c["length"]), "half_mm": [f(v) for v in c["half"]],
                      "hooks": [{"angle_deg": a_, "r_mm": f(r_), "radius_mm": f(d_)} for a_, r_, d_ in c["hooks"]]}
    out["hub_radius_mm"] = [f(v) for v in M["hub_radius_px"]]
    out["hand_offset_mm"] = mm((hx, hy))  # where the render shows the hand stack; the build moves it to the origin
    out["subs"] = {"centres_mm": [mm(p) for p in M["subs"]["centres"]], "hub_mm": f(M["subs"]["hub"])}

    # applied indices: the white parts in the index band, one rotated rectangle each (frame and lume together)
    rp = np.hypot(xx - cx, yy - cy)
    ib = white & (rp > M["index_band"][0]) & (rp < M["index_band"][1])
    ib = cv2.morphologyEx(ib.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(ib)
    bars = []
    for i in range(1, n):
        if st[i, 4] < 250:
            continue
        ys_, xs_ = np.nonzero(lab == i)
        (bx, by), (bw, bh), _ = cv2.minAreaRect(np.column_stack([xs_, ys_]).astype(np.float32))
        x_mm, y_mm = mm((bx, by))
        ang = math.degrees(math.atan2(x_mm, y_mm)) % 360
        off = abs((ang + 15) % 30 - 15)
        if off > 6 or st[i, 4] > 4000:
            continue  # print, a hand or the date frame
        bars.append({"centre_mm": [x_mm, y_mm], "angle_deg": round(ang, 2), "half_len_mm": f(max(bw, bh) / 2), "half_w_mm": f(min(bw, bh) / 2),
                     "area_px": int(st[i, 4])})
    # batons at 1 2 4 5 7 8 10 11 all alike (one is under the city print at 11): median size and radius on the hour angles;
    # the small squares (a pair at 12, one at 3 by the date, 6 and 9) as detected
    batons = [b_ for b_ in bars if 1.2 < b_["half_len_mm"] < 1.5 and abs((b_["angle_deg"] + 15) % 30 - 15) < 2]
    small = [b_ for b_ in bars if b_["half_len_mm"] < 0.75 and min(abs((b_["angle_deg"] - q + 180) % 360 - 180) for q in (0, 90, 180, 270)) < 5]
    assert len(batons) >= 5 and len(small) == 5, (len(batons), len(small))
    med = lambda k: float(np.median([b_[k] for b_ in batons]))
    out["indices"] = {"baton": {"r_mm": round(float(np.median([math.hypot(*b_["centre_mm"]) for b_ in batons])), 3), "half_len_mm": round(med("half_len_mm"), 3),
                                "half_w_mm": round(med("half_w_mm"), 3), "hours": [1, 2, 4, 5, 7, 8, 10, 11], "measured": len(batons)},
                      "small": sorted(small, key=lambda b_: b_["angle_deg"]), "frame_mm": 0.12}

    for k in ("crown", "crown_left"):
        cr = M[k]
        out[k] = {"angle_deg": cr["angle_deg"], "r_mm": [f(v) for v in cr["r"]], "radius_mm": f(cr["radius"]), "teeth": cr["teeth"]}
    out["pushers"] = [{"angle_deg": p["angle_deg"], "r_mm": [f(v) for v in p["r"]], "radius_mm": f(p["radius"])} for p in M["pushers"]]
    out["guard_mm"] = [mm(p) for p in M["guard"]]
    out["left_shoulder_mm"] = [mm(p) for p in M["left_shoulder"]]
    d = M["date"]
    out["date_mm"] = mm(d[:2]) + mm(d[2:])
    out["manual_px"] = M
    out["artefacts_not_traced"] = ARTEFACTS

    if overlay:
        ov = im.copy() // 2 + 60
        P = lambda q: (int(round(cx + q[0] * S)), int(round(cy - q[1] * S)))
        cv2.circle(ov, (int(bcx), int(bcy)), int(br), (0, 0, 255), 1)
        for v in M["rings_px"].values():
            cv2.circle(ov, (int(cx), int(cy)), int(v), (0, 0, 255), 1)
        for yr, hh in rows:
            for sx in (1, -1):
                cv2.circle(ov, P((sx * hh, yr)), 1, (0, 200, 255), -1)
        for name, hd in hands.items():
            if "outline_mm" not in hd:
                a = math.radians(hd["angle_deg"])
                cv2.line(ov, (int(hx), int(hy)), (int(hx + hd["tip_mm"] * S * math.sin(a)), int(hy - hd["tip_mm"] * S * math.cos(a))), (0, 255, 255), 1)
                continue
            cv2.polylines(ov, [np.array([P(q) for q in hd["outline_mm"]], np.int32)], True, (0, 255, 255), 1)
            if "lume_mm" in hd:
                cv2.polylines(ov, [np.array([P(q) for q in hd["lume_mm"]], np.int32)], True, (255, 0, 255), 1)
        ix = out["indices"]
        shown = [{"centre_mm": [ix["baton"]["r_mm"] * math.sin(math.radians(30 * hr)), ix["baton"]["r_mm"] * math.cos(math.radians(30 * hr))], "angle_deg": 30 * hr,
                  "half_len_mm": ix["baton"]["half_len_mm"], "half_w_mm": ix["baton"]["half_w_mm"]} for hr in ix["baton"]["hours"]] + ix["small"]
        for bb in shown:
            a = math.radians(bb["angle_deg"])
            u, v = (math.sin(a), math.cos(a)), (math.cos(a), -math.sin(a))
            L, W = bb["half_len_mm"], bb["half_w_mm"]
            x0, y0 = bb["centre_mm"]
            poly = [(x0 + su * L * u[0] + sv * W * v[0], y0 + su * L * u[1] + sv * W * v[1]) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            cv2.polylines(ov, [np.array([P(q) for q in poly], np.int32)], True, (0, 255, 0), 1)
        for k in ("guard", "left_shoulder"):
            cv2.polylines(ov, [np.array(M[k], np.int32)], True, (255, 0, 255), 1)
        for k in ("crown", "crown_left") + tuple(range(len(M["pushers"]))):
            cr = M[k] if isinstance(k, str) else M["pushers"][k]
            a = math.radians(cr["angle_deg"])
            for r in cr["r"]:
                cv2.circle(ov, (int(cx + r * math.sin(a)), int(cy - r * math.cos(a))), 4, (0, 0, 255), -1)
        for x, y in M["subs"]["centres"]:
            cv2.circle(ov, (int(x), int(y)), 4, (0, 0, 255), -1)
        for y in M["horn_tips_y"] + M["end_link"]["tips_y"]:
            cv2.line(ov, (int(cx - 350), y), (int(cx + 350), y), (255, 128, 0), 1)
        cv2.imwrite(str(overlay), ov)
    return out


if __name__ == "__main__":
    dest = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT
    data = trace(overlay=Path(sys.argv[2]) if len(sys.argv) > 2 else None)
    dest.write_text(json.dumps(data, indent=1, default=float) + "\n")
    print(json.dumps({k: data[k] for k in ("scale_px_per_mm", "bezel_fit", "rings_mm", "horn_tip_mm", "end_link", "bracelet", "checks", "hand_offset_mm",
                                           "subs")}, default=float), "->", dest)
    print(json.dumps(data["indices"]["baton"]), [(b["angle_deg"], b["half_len_mm"], b["half_w_mm"]) for b in data["indices"]["small"]])
    print({k: (len(v["outline_mm"]), v["length_mm"]) for k, v in data["hands"].items() if "outline_mm" in v})
