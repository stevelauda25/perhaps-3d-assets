"""watch_audemars_royaloak41: the AUDEMARS PIGUET Royal Oak Selfwinding 41 (15500ST / 15510ST, steel case, integrated steel bracelet) build; the Royal Oak 41 TEMPLATE.

Own copy of pipeline/steps/watch_audemars_offshorediver42.py (untouched; same recipe, same helpers, spec driven) with these changes for the Royal Oak:
  - the bezel is the same octagon ring by rays (outer outline = measured octagon cut back to the case silhouette, inner outline = the round opening, flat face at case.bezel_z plus a thin
    chamfer down to the opening) with eight screw heads; the dial is one flat lathe (the Grande Tapisserie plate, no rotating ring: dial.ring_z = dial.z) carrying the 2x photo map;
  - ONE crown (3 o'clock, no guards): trace.crowns = hexagonal steel cap with the flat face toward the viewer; the ring is optional (ring_len_mm 0 = none);
  - the bracelet is integrated and built from trace.bracelet (measured in the prep from the photo, mm): horizontal links = pieces between the dark seams (trace.bracelet.seams_mm, the first
    seam is the junction of the case, where the case slab ends; real gaps with the dark backing behind), in three gapped columns (left outer / centre / right outer) and two continuous
    polished pin-link bars (trace.bracelet.bars_mm, x boundaries linear in |y|) that cross the seams; outer edges follow the silhouette; heights from spec.bracelet;
  - hands: no luminous inlay objects (the polished facets and the inlay stay in the photo map under the 3D hands: spec hands.lume is empty).
A later Royal Oak 41 variant (white row 84, grey row 85, other 15500ST / 15510ST dials) needs only its own spec / measure / job JSON; copy this step only for a code change.

Params: spec. Same frame, pose (`SKO | pose`), 2.5D depth scale, materials as watch_seiko_front, whose helpers it reuses.
Rebuild with --force after regenerating the dial map (the map is not in the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def rays(poly, n):
    """Distance from the origin to the closed polygon (furthest hit) along n equal angles, counter-clockwise from +x."""
    segs = list(zip(poly, poly[1:] + poly[:1]))
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n
        dx, dy = math.cos(a), math.sin(a)
        best = 0.0
        for (x1, y1), (x2, y2) in segs:
            ex, ey = x2 - x1, y2 - y1
            den = dx * ey - dy * ex
            if abs(den) < 1e-12:
                continue
            t = (x1 * ey - y1 * ex) / den
            u = (x1 * dy - y1 * dx) / den
            if t > 0 and -1e-9 <= u <= 1 + 1e-9:
                best = max(best, t)
        out.append(best)
    return out


def circle_rays(cx, cy, r, n):
    """Points of the circle (centre cx, cy, radius r, origin inside) on the same n angles as rays()."""
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n
        dx, dy = math.cos(a), math.sin(a)
        b = dx * cx + dy * cy
        t = b + math.sqrt(b * b - (cx * cx + cy * cy - r * r))
        out.append((t * dx, t * dy))
    return out


def ring(g, outer, inner, z0, zo, zi):
    """Annulus between two equal-length counter-clockwise point lists: top sloping from zo (outer edge) to zi (inner edge), walls down to z0, flat bottom."""
    n, base = len(outer), len(g.v)
    g.v += [(x, y, z0) for x, y in outer] + [(x, y, zo) for x, y in outer] + [(x, y, z0) for x, y in inner] + [(x, y, zi) for x, y in inner]
    ob, ot, ib, it = base, base + n, base + 2 * n, base + 3 * n
    for k in range(n):
        j = (k + 1) % n
        g.f += [(ot + k, ot + j, it + j, it + k), (ob + k, ob + j, ot + j, ot + k), (it + k, it + j, ib + j, ib + k), (ib + k, ib + j, ob + j, ob + k)]
        g.smooth += [False] * 4
    return g


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    meta = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    scene = bpy.context.scene
    coll = bpy.data.collections.new("WATCH | %s front relief" % cfg["model"].split(" (")[0])
    scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    mats["dial"] = photo_material("dial_photo", ROOT / cfg["dial_map"], cfg["dial"]["roughness"])
    dn = mats["dial"].node_tree
    db = next(n for n in dn.nodes if n.type == "BSDF_PRINCIPLED")
    db.inputs["Specular IOR Level"].default_value = cfg["dial"]["specular"]
    dn.links.new(next(n for n in dn.nodes if n.type == "TEX_IMAGE").outputs["Color"], db.inputs["Emission Color"])  # keeps the printed gold as photographed
    db.inputs["Emission Strength"].default_value = cfg["dial"]["emission"]
    steel_meta = json.loads((ROOT / cfg["steel_map"]).with_suffix(".json").read_text())
    mats["steel_photo"] = photo_material("steel_photo", ROOT / cfg["steel_map"], cfg["steel"]["roughness"])
    nt = mats["steel_photo"].node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bs.inputs["Specular IOR Level"].default_value = cfg["steel"]["specular"]
    nt.links.new(next(n for n in nt.nodes if n.type == "TEX_IMAGE").outputs["Color"], bs.inputs["Emission Color"])  # the photo's own shading, not re-lit away
    bs.inputs["Emission Strength"].default_value = cfg["steel"]["emission"]
    mats["hands_photo"] = mats["steel_photo"].copy()  # same projected photo; own emission (hands.emission) so the photographed gold/lume brightness can be matched
    mats["hands_photo"].node_tree.nodes[bs.name].inputs["Emission Strength"].default_value = cfg["hands"].get("emission", cfg["steel"]["emission"])
    S_px, (px0, py0) = tr["scale_px_per_mm"], tr["origin_px"]
    cx0, cy0 = steel_meta["crop_px"][:2]
    mw, mh = steel_meta["size_px"]

    def steel_uv(me):  # the photo projected straight from the front: every steel part shows the photographed pixels at its x, y
        uv = me.uv_layers.new(name="UVMap")
        for loop in me.loops:
            x, y, _ = me.vertices[loop.vertex_index].co
            uv.data[loop.index].uv = ((px0 + x * S_px - cx0) * 2 / mw, 1 - (py0 - y * S_px - cy0) * 2 / mh)

    H = meta["half_size_mm"]
    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location, pose.scale = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"]), (0.001,) * 3
    ds = cfg["pose"]["depth_scale"]

    def add(name, geo, mat, bevel=None, smooth=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in ("steel_photo", "hands_photo"):
            steel_uv(me)
        if bevel:
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if not name.startswith("bracelet"):
            o.scale = (1, 1, ds)
        return o

    def photo_uv(me):  # planar, centred on the pivot; faces up
        if me.polygons[0].normal.z < 0:
            for poly in me.polygons:
                poly.flip()
            me.update()
        uv = me.uv_layers.new(name="UVMap")
        for loop in me.loops:
            x, y, _ = me.vertices[loop.vertex_index].co
            uv.data[loop.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
        return me

    cs, d, op = cfg["case"], cfg["dial"], tr["opening"]
    rc, R_open = op["centre_mm"], op["radius_mm"]  # the round opening of the rotating bezel sits about 0.2 mm above the pivot in the photo (camera tilt): its lathes are centred there

    def at_ring(g):
        g.v = [(x + rc[0], y + rc[1], z) for x, y, z in g.v]
        return g
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}

    y_lo, y_hi = min(sil), max(sil)

    def edges(y):  # left and right silhouette x at y (the photo is not exactly centred on the pivot)
        p = sil[round(round(max(y_lo, min(y_hi, y)) * 4) / 4, 2)]
        return p[1], p[2]

    # ---- integrated case and lugs from the silhouette (own length top and bottom), top sloping into the bracelet ----
    tt, tb = cs["tip_top"], cs["tip_bottom"]
    ys = [-tb + k * 0.25 for k in range(int(round((tt + tb) / 0.25)) + 1)]
    outline = [(edges(y)[1], y) for y in ys] + [(edges(y)[0], y) for y in reversed(ys)]
    ramp = lambda x, y: cs["body_z"] - (cs["body_z"] - cs["tip_z"]) * min(1.0, max(0.0, (abs(y) - cs["ramp_from_y"]) / ((tt if y > 0 else tb) - cs["ramp_from_y"])))
    g = Geo()
    slab(g, outline, 0.0, ramp)
    add("case", g, "steel_photo", bevel=cs["bevel"])

    # ---- bezel: octagon ring (outer edge = measured octagon cut back to the silhouette) with a polished chamfer down to the round opening, plus eight screw heads ----
    N, zb = cs["rays"], cs["bezel_z"]
    r_oct = rays([tuple(p) for p in tr["octagon_mm"]], N)
    r_sil = rays(outline, N)
    outer = [(min(ro, rs - cs["silhouette_margin_mm"]) * math.cos(2 * math.pi * k / N), min(ro, rs - cs["silhouette_margin_mm"]) * math.sin(2 * math.pi * k / N))
             for k, (ro, rs) in enumerate(zip(r_oct, r_sil))]
    mid = circle_rays(rc[0], rc[1], R_open + cs["chamfer_mm"], N)
    inner = circle_rays(rc[0], rc[1], R_open, N)
    add("core", Geo().prism(inner, 0.0, d["z"] - 0.05), "steel_gap")
    g = ring(Geo(), outer, mid, 0.0, zb, zb)
    ring(g, mid, inner, 0.0, zb, cs["chamfer_z"])
    add("bezel", g, "steel_photo", bevel=cs["bezel_bevel"])
    sr = tr["screw_radius_mm"]
    for k, (sx, sy) in enumerate(tr["screws_mm"]):  # shallow domed heads; hexagon and slot come from the projected photo
        add("screw_%d" % k, Geo().lathe([(0, zb + cs["screw_z"]), (sr * 0.8, zb + cs["screw_z"]), (sr, zb + cs["screw_z"] * 0.3), (sr, zb - 0.05), (0, zb - 0.05)], segs=24,
                                         m=Matrix.Translation((sx, sy, 0))), "steel_photo", smooth=True)

    # ---- crystal and dial (flat waffle plate, step up to the plane of the rotating ring, out to the opening) ----
    cr = cfg["crystal"]
    ce = R_open - 0.05
    dome = [(ce * f, cr["z1"] + cr["dome"] * (1 - f * f)) for f in (1.0, 0.85, 0.65, 0.4, 0.0)]  # shallow dome
    add("crystal", at_ring(Geo().lathe([(0, cr["z0"]), (ce, cr["z0"]), (ce, cr["z1"])] + dome[1:], segs=192)), "crystal")
    add("dial", photo_uv(at_ring(Geo().lathe([(0, d["z"]), (op["dial_flat_mm"], d["z"]), (op["ring_in_mm"], d["ring_z"]), (R_open, d["ring_z"])], segs=192)).mesh(P + "dial", True)), "dial")

    # ---- hands at the photographed pose: outlines from the spec (mm along the hand from the pivot, half width), the last point sits at the traced length ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute", "seconds"):
        h = t[name]
        L, deg, z = h["length_mm"], h["angle_deg"], hs["z"][name]
        prof = [list(p) for p in hs["profile"][name]]
        prof[-1][0] = L
        half_outline = [(0, prof[0][0])] + [(w, y) for y, w in prof] if prof[-1][1] == 0 else [(0, prof[0][0])] + [(w, y) for y, w in prof] + [(0, L)]
        g_ = Geo()
        for sx in (1, -1):  # two facets meeting at a ridge on the centre line
            slab(g_, [rot(sx * x, y, deg) for x, y in half_outline], z, lambda x, y, z=z, deg=deg: z + th + hs["ridge"] * _on_axis(x, y, deg))
        add("hand_" + name, g_, hs.get("material", "gold"), bevel=0.02)
        if name in hs["lume"]:  # lume: +w side outline [s, w] in mm along the hand, mirrored about the axis; polygon extruded over the hand ridge
            half = [(w, y) for y, w in hs["lume"][name]]
            poly = half + [(-w, y) for w, y in reversed(half) if w > 0]
            add("lume_" + name, Geo().prism([rot(x, y, deg) for x, y in poly], z + th + hs["ridge"] * 0.4, z + th + hs["ridge"] + hs["lume_height"]), hs.get("lume_material", "lume"))
    hub_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, hs["z"]["minute"] + th), (hub_r * 0.55, hs["z"]["seconds"] + th + 0.1), (0, hs["z"]["seconds"] + th + 0.1)], segs=48),
        hs.get("material", "gold"), smooth=True)

    # ---- crown (3 o'clock): hexagonal steel cap with a flat face toward the viewer along the axis (optional short ring); local z = along the axis, local y = up ----
    c = cfg["crown"]
    for cw in tr["crowns"]:
        ax, ay = math.sin(math.radians(cw["angle_deg"])), math.cos(math.radians(cw["angle_deg"]))
        m = Matrix(((-ay, 0, ax), (ax, 0, ay), (0, 1, 0))).to_4x4()
        m.translation = (cw["base_mm"][0], cw["base_mm"][1], c["z"])
        hr, hl, rr, rl = cw["hex_r_mm"], cw["hex_len_mm"], cw["ring_r_mm"], cw["ring_len_mm"]
        add(cw["name"], Geo().prism([(hr * math.cos(math.radians(60 * k)), hr * math.sin(math.radians(60 * k))) for k in range(6)], 0.0, hl, m), "steel_photo", bevel=c.get("bevel", 0.15))
        if rl > 0:
            add(cw["name"] + "_ring", Geo().lathe([(0, hl), (rr, hl), (rr, hl + rl * 0.8), (rr * 0.9, hl + rl), (0, hl + rl)], segs=48, m=m), "steel_photo", smooth=True)

    # ---- integrated bracelet: links between the measured seams, polished pin-link bars across them (flat columns of pieces, top and bottom separately) ----
    br, tbr = cfg["bracelet"], tr["bracelet"]
    gap, ins, bins, za = br["gap"], br["inset"], br["backing_inset"], ds * br["z0"]

    def bars(y):  # x boundaries (left bar x0, x1, right bar x0, x1) at y: linear in |y| between the measured rows, held beyond the first and last
        pts = tbr["bars_mm"]["top" if y > 0 else "bottom"]
        a_ = abs(y)
        if a_ <= pts[0][0]:
            return pts[0][1:]
        for p, q in zip(pts, pts[1:]):
            if a_ <= q[0]:
                f = (a_ - p[0]) / (q[0] - p[0])
                return [u + (v - u) * f for u, v in zip(p[1:], q[1:])]
        return pts[-1][1:]
    cols = {"left": (lambda y: edges(y)[0] + ins, lambda y: bars(y)[0] - gap / 2, False),
            "bar_left": (lambda y: bars(y)[0] + gap / 2, lambda y: bars(y)[1] - gap / 2, True),
            "centre": (lambda y: bars(y)[1] + gap / 2, lambda y: bars(y)[2] - gap / 2, False),
            "bar_right": (lambda y: bars(y)[2] + gap / 2, lambda y: bars(y)[3] - gap / 2, True),
            "right": (lambda y: bars(y)[3] + gap / 2, lambda y: edges(y)[1] - ins, False)}
    links, bar_geo, back, pieces = Geo(), Geo(), Geo(), 0
    for sy, key, end in ((1, "top", y_hi), (-1, "bottom", -y_lo)):
        seams = tbr["seams_mm"][key]
        sh = br["seam_shrink"]  # the pieces reach sh mm into each seam: the photo's seams hold dark and light lines, the open gap shows only the dark core
        spans = [(seams[k][1] - sh, seams[k + 1][0] + sh) for k in range(len(seams) - 1)] + [(seams[-1][1] - sh, end)]  # link pieces between the seams, the last one runs to the strap end
        for cname, (xl, xr, is_bar) in cols.items():
            for a_, b_ in ([(seams[0][0] - 0.05, end)] if is_bar else spans):  # a bar is one piece from the case junction to the end
                n_ = max(1, math.ceil((b_ - a_) / 0.5))
                ys_ = [sy * (a_ + j * (b_ - a_) / n_) for j in range(n_ + 1)]  # columns follow the photo's tapering edges
                slab(bar_geo if is_bar else links, [(xr(y), y) for y in ys_] + [(xl(y), y) for y in reversed(ys_)], za, lambda x, y, b=is_bar: ds * (br["z"] + (br["bar_lift"] if b else 0.0)))
                pieces += 1
        s0, s1 = seams[0][0], end
        ys_ = [sy * (s0 + j * (s1 - s0) / round((s1 - s0) / 0.5)) for j in range(round((s1 - s0) / 0.5) + 1)]
        slab(back, [(edges(y)[1] - bins, y) for y in ys_] + [(edges(y)[0] + bins, y) for y in reversed(ys_)], ds * br["backing_z"][0], lambda x, y: ds * br["backing_z"][1])
    add("bracelet_links", links, "steel_photo", bevel=br["bevel"] or None, smooth=False)  # bevel 0 = flat shading: the long thin top faces shade wrongly with smooth normals
    add("bracelet_bars", bar_geo, "steel_photo", bevel=br["bevel"] or None, smooth=False)
    add("bracelet_backing", back, "steel_gap")
    kind = "bracelet"

    out = {"diameter": round(sorted(p[2] - p[1] for p in tr["silhouette_y_left_right_mm"] if abs(p[0]) < 3)[len([1 for p in tr["silhouette_y_left_right_mm"] if abs(p[0]) < 3]) // 2], 3),
           "lug_to_lug": round(tt + tb, 3)}  # diameter = median silhouette width within 3 mm of the pivot row (left flat to the guard notch wall)
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "bracelet": kind, "bracelet_pieces": pieces, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}


def _on_axis(x, y, deg):
    """1 on the radial centre line through angle deg (the ridge), 0 elsewhere."""
    a = math.radians(deg)
    return 1.0 if abs(x * math.cos(a) - y * math.sin(a)) < 1e-4 else 0.0
