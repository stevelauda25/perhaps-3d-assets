"""watch_rolex_submarinerdate41: build a ROLEX Submariner Date 41 (126610LN; 126610LV, 126613LB and 126613LN reuse this file read-only with their own spec / trace / maps) as a flat-backed front relief
(like the other Rolex / Tudor / Omega GLBs in models/watches/).

Copy of watch_rolex_submariner41 (untouched, the no-date 124060 template) plus the CYCLOPS date lens (spec `date`, trace `date.lens_mm`, see below), spec driven:
  - the case and lugs are cut from the photo silhouette (coin-edge bezel tips at the left, crown guards at the right, crown rows replaced by the straight guard line, done in the prep);
  - the bezel is a black ceramic insert (flat top, small chamfer toward the dial, numerals / minute scale / lume pearl are texture), a flat polished rim ring and a COIN EDGE ring whose outer
    edge is a real fluted outline (`bezel.teeth` scallops of `flute_depth` mm between rings.rim_out and rings.bezel_tip) sloping down to the case; all rings share one angular sampling;
  - the hands are the traced photo OUTLINES (trace.hands[name].outline_mm, mm from the pivot, x right / y up): flat polygons at their own heights (hands_photo projects the photographed pixels
    on them: Mercedes ring, lume, black facets); the photographed hands also stay in the dial map;
  - a fluted crown with neck and rounded cap on the 3 o'clock axis, the guards are part of the case slab;
  - a three-column Oyster bracelet (outer / centre / outer) whose columns, joints and column lines come from the spec (`strap.bracelet.columns`, `bounds_x_mm`, `pieces_mm`).
Native-size maps (prep: pipeline/rolex_submarinerdate41_prep.py): the maps carry a `scale` (map px per photo px, 1.0 unless the 2048 cap bites).
  - the Cyclops lens (only when the spec has a `date` section): the photographed lens outline (trace.date.lens_mm, a closed polygon) raised above the crystal: a vertical wall, then two offset
    rings (scaled about the polygon centre, `date.rings`) so the edge reads as a bevel, then the flat top; the photo (front projection, own emission `date.emission`) supplies the bright frame,
    the glass reflection and the date window; the date numeral and the window itself also stay in the dial map.
A variant (green bezel, blue / black two-tone) only needs its own spec / measure / job JSON and maps. Spec per variant: config/watches/rolex-submarinerdate41-<key>.json.

Params: spec. Same frame, pose (`SKO | pose`), 2.5D depth scale, materials as watch_seiko_front, whose helpers it reuses.
Rebuild with --force after regenerating the maps (the maps are not in the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT


def strip(g, outer, inner, zo, zi):
    """Top face of an annulus between two equal-length counter-clockwise point lists, height zo at the outer and zi at the inner edge (no walls)."""
    n, base = len(outer), len(g.v)
    g.v += [(x, y, zo) for x, y in outer] + [(x, y, zi) for x, y in inner]
    for k in range(n):
        j = (k + 1) % n
        g.f.append((base + k, base + j, base + n + j, base + n + k))
        g.smooth.append(False)
    return g


def wall(g, pts, zt, zb):
    """Vertical outer wall under a counter-clockwise outline, from zt down to zb."""
    n, base = len(pts), len(g.v)
    g.v += [(x, y, zt) for x, y in pts] + [(x, y, zb) for x, y in pts]
    for k in range(n):
        j = (k + 1) % n
        g.f.append((base + n + k, base + n + j, base + j, base + k))
        g.smooth.append(False)
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
    dn.links.new(next(n for n in dn.nodes if n.type == "TEX_IMAGE").outputs["Color"], db.inputs["Emission Color"])  # the printed dial as photographed
    db.inputs["Emission Strength"].default_value = cfg["dial"]["emission"]
    steel_meta = json.loads((ROOT / cfg["steel_map"]).with_suffix(".json").read_text())
    mats["steel_photo"] = photo_material("steel_photo", ROOT / cfg["steel_map"], cfg["steel"]["roughness"])
    nt = mats["steel_photo"].node_tree
    bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    bs.inputs["Specular IOR Level"].default_value = cfg["steel"]["specular"]
    nt.links.new(next(n for n in nt.nodes if n.type == "TEX_IMAGE").outputs["Color"], bs.inputs["Emission Color"])  # the photo's own shading, not re-lit away
    bs.inputs["Emission Strength"].default_value = cfg["steel"]["emission"]
    mats["hands_photo"] = mats["steel_photo"].copy()  # same projected photo; own emission so the photographed hand brightness can be matched
    mats["hands_photo"].node_tree.nodes[bs.name].inputs["Emission Strength"].default_value = cfg["hands"].get("emission", cfg["steel"]["emission"])
    if "bezel_emission" in cfg["steel"]:  # the ceramic insert and the coin ring can need their own emission (black ceramic with a baked sheen)
        mats["bezel_photo"] = mats["steel_photo"].copy()
        mats["bezel_photo"].node_tree.nodes[bs.name].inputs["Emission Strength"].default_value = cfg["steel"]["bezel_emission"]
    if "date" in cfg:  # the lens shows the projected photo with its own emission
        mats["date_photo"] = mats["steel_photo"].copy()
        mats["date_photo"].node_tree.nodes[bs.name].inputs["Emission Strength"].default_value = cfg["date"]["emission"]
    S_px, (px0, py0) = tr["scale_px_per_mm"], tr["origin_px"]
    cx0, cy0 = steel_meta["crop_px"][:2]
    mw, mh = steel_meta["size_px"]
    k_map = steel_meta.get("scale", 1.0)  # map px per photo px

    def steel_uv(me):  # the photo projected straight from the front: every steel part shows the photographed pixels at its x, y
        uv = me.uv_layers.new(name="UVMap")
        for loop in me.loops:
            x, y, _ = me.vertices[loop.vertex_index].co
            uv.data[loop.index].uv = ((px0 + x * S_px - cx0) * k_map / mw, 1 - (py0 - y * S_px - cy0) * k_map / mh)

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
        if mat in ("steel_photo", "hands_photo", "bezel_photo", "date_photo"):
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

    rg, cs, bz, d = tr["rings_mm"], cfg["case"], cfg["bezel"], cfg["dial"]
    rc = cfg.get("ring_centre_mm", tr["ring_centre_mm"])  # the photo's dial / bezel circle sits a px off the hub: bezel, crystal and dial are centred there

    def at_ring(g):
        g.v = [(x + rc[0], y + rc[1], z) for x, y, z in g.v]
        return g
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}
    y_lo, y_hi = min(sil), max(sil)

    def edges(y):  # left and right silhouette x at y
        p = sil[round(round(max(y_lo, min(y_hi, y)) * 4) / 4, 2)]
        return p[1], p[2]

    # ---- case and lugs from the silhouette (own length top and bottom), sloping toward the bracelet; the crown guards are part of the outline ----
    tt, tb = cs["tip_top"], cs["tip_bottom"]
    ys = [-tb + k * 0.25 for k in range(int(round((tt + tb) / 0.25)) + 1)]
    outline = [(edges(y)[1], y) for y in ys] + [(edges(y)[0], y) for y in reversed(ys)]
    ramp = lambda x, y: cs["body_z"] - (cs["body_z"] - cs["tip_z"]) * min(1.0, max(0.0, (abs(y) - cs["ramp_from_y"]) / ((tt if y > 0 else tb) - cs["ramp_from_y"])))
    g = Geo()
    slab(g, outline, 0.0, ramp)
    add("case", g, "steel_photo", bevel=cs["bevel"])

    # ---- bezel: ceramic insert (chamfer + flat top), polished rim ring, coin-edge ring with a fluted outer outline; all strips use the same N angles ----
    teeth, spp = bz["teeth"], bz["samples_per_tooth"]
    N = teeth * spp
    ang = [2 * math.pi * k / N for k in range(N)]
    circ = lambda r: [(r * math.cos(a), r * math.sin(a)) for a in ang]
    r_tip, fd = rg["bezel_tip"], bz["flute_depth"]
    fl = lambda a: fd * (0.5 - 0.5 * math.cos(teeth * (a - math.pi / 2))) ** bz.get("flute_power", 1.0)  # 0 on a ridge (one at 12 o'clock), fd in a flute
    star = [((r_tip - fl(a)) * math.cos(a), (r_tip - fl(a)) * math.sin(a)) for a in ang]  # scalloped outline: ridges between concave flutes
    gb, gc = Geo(), Geo()
    strip(gb, circ(rg["bezel_in"] + bz["chamfer_mm"]), circ(rg["bezel_in"]), bz["z_insert"], bz["z_inner"])  # chamfer toward the dial
    strip(gb, circ(rg["insert_out"]), circ(rg["bezel_in"] + bz["chamfer_mm"]), bz["z_insert"], bz["z_insert"])  # flat black ceramic top (numerals are texture)
    strip(gb, circ(rg["rim_out"]), circ(rg["insert_out"]), bz["z_rim"], bz["z_rim"])  # polished rim ring around the insert
    strip(gc, star, circ(rg["rim_out"]), bz["z_coin_out"], bz["z_rim"])  # coin edge: scalloped outer outline sloping down to the case
    wall(gc, star, bz["z_coin_out"], bz["z0"])
    bm = "bezel_photo" if "bezel_photo" in mats else "steel_photo"
    add("bezel", at_ring(gb), bm)
    add("bezel_coin_edge", at_ring(gc), "steel_photo")

    # ---- crystal and dial ----
    cr = cfg["crystal"]
    ce = rg["crystal_edge"]
    dome = [(ce * f, cr["z1"] + cr["dome"] * (1 - f * f)) for f in (1.0, 0.85, 0.65, 0.4, 0.0)]  # shallow dome
    add("crystal", at_ring(Geo().lathe([(0, cr["z0"]), (ce, cr["z0"]), (ce, cr["z1"])] + dome[1:], segs=192)), "crystal")
    add("dial", photo_uv(at_ring(Geo().lathe([(0, d["z"]), (rg["dial_flat"], d["z"]), (rg["crystal_edge"], d["rehaut_z"])], segs=192)).mesh(P + "dial", True)), "dial")


    # ---- Cyclops date lens: wall + two bevel rings + flat top, the photographed outline, above the crystal ----
    if "date" in cfg:
        dc = cfg["date"]
        pts = [tuple(q) for q in tr["date"]["lens_mm"]]
        if sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1])) < 0:
            pts = pts[::-1]  # counter-clockwise
        cen = tr["date"]["centre_mm"]
        ring = lambda f: [(cen[0] + (x - cen[0]) * f, cen[1] + (y - cen[1]) * f) for x, y in pts]
        z0, ze, zt = dc["z0"], dc["z_edge"], dc["z_top"]
        f1, f2 = dc["rings"]
        gl = Geo()
        wall(gl, pts, ze, z0)
        strip(gl, pts, ring(f1), ze, ze + (zt - ze) * 0.6)
        strip(gl, ring(f1), ring(f2), ze + (zt - ze) * 0.6, zt)
        gl.f.append(tuple(range(len(gl.v) - len(pts), len(gl.v))))  # flat top (the last ring is the last block of vertices)
        gl.smooth.append(False)
        add("date_cyclops", gl, "date_photo")

    # ---- hands: the traced photo outlines as flat polygons at their own heights ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute", "seconds"):
        z = hs["z"][name]
        add("hand_" + name, slab(Geo(), [tuple(p) for p in t[name]["outline_mm"]], z, lambda x, y, z=z: z + th), hs.get("material", "hands_photo"), bevel=0.02)
    hub_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, hs["z"]["minute"] + th), (hub_r * 0.55, hs["z"]["seconds"] + th + 0.1), (0, hs["z"]["seconds"] + th + 0.1)], segs=48),
        hs.get("material", "hands_photo"), smooth=True)

    # ---- crown on the 3 o'clock axis: neck, fluted cylinder, rounded cap (the coronet is texture) ----
    c, cw = cfg["crown"], tr["crown"]
    rad, r_from, r_to, r_fl = cw["radius_mm"], cw["x_mm"][0], cw["x_mm"][1], cw["fluted_to_mm"]
    star_c = [((rad if i % 2 == 0 else rad - c["flute_depth"]) * math.cos(math.pi * i / c["teeth"]),
               (rad if i % 2 == 0 else rad - c["flute_depth"]) * math.sin(math.pi * i / c["teeth"])) for i in range(c["teeth"] * 2)]
    m = Matrix(((0, -1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_4x4()
    m.translation = (0, cw["centre_y_mm"], c["z"])
    add("crown", Geo().prism(star_c, r_from, r_fl, m), "steel_photo", bevel=c.get("bevel", 0.15))
    add("crown_neck", Geo().lathe([(0, rg["rim_out"] - 0.5), (rad * c["neck_radius_fraction"], rg["rim_out"] - 0.5), (rad * c["neck_radius_fraction"], r_from + 0.1), (0, r_from + 0.1)], segs=48, m=m),
        "steel_photo", smooth=True)
    cap = [(0, r_fl), (rad - 0.1, r_fl), (rad * c["cap_radius_fraction"], r_to - 0.3), (rad * c["cap_radius_fraction"] * 0.6, r_to), (0, r_to)]
    add("crown_cap", Geo().lathe(cap, segs=48, m=m), "steel_photo", smooth=True)

    # ---- bracelet: columns left to right (strap.bracelet.columns), each a chain of flat pieces at measured y ranges, top and bottom separately ----
    kind = cfg["strap"]["kind"]
    assert kind == "bracelet", "strap.kind %r" % kind
    br = cfg["strap"][kind]
    gap, za, ins, bins = br["gap"], ds * br["z0"], br["inset"], br["backing_inset"]
    seq = br["columns"]

    def bounds(y):  # x of the vertical joint lines between the columns at y: linear in the spec's [|y|, x1, x2, ...] lists, one per side
        pts = br["bounds_x_mm"]["top" if y > 0 else "bottom"]
        for p0, p1 in zip(pts, pts[1:]):
            if abs(y) <= p1[0]:
                f = max(0.0, (abs(y) - p0[0]) / (p1[0] - p0[0]))
                return [a_ + (b_ - a_) * f for a_, b_ in zip(p0[1:], p1[1:])]
        return pts[-1][1:]

    cols = [((lambda y: edges(y)[0] + ins) if i == 0 else (lambda y, i=i: bounds(y)[i - 1] + gap / 2),
             (lambda y: edges(y)[1] - ins) if i == len(seq) - 1 else (lambda y, i=i: bounds(y)[i] - gap / 2), ck) for i, ck in enumerate(seq)]
    first = seq[0]
    links, back, pieces = Geo(), Geo(), 0
    for sy, key in ((1, "top"), (-1, "bottom")):
        for xl, xr, ckind in cols:
            for k, (a_, b_) in enumerate(br["pieces_mm"][ckind][key]):
                y0, y1 = a_ + (gap / 2 if k else 0), b_ - gap / 2
                n_ = max(1, math.ceil((y1 - y0) / 0.5))
                ys_ = [sy * (y0 + j * (y1 - y0) / n_) for j in range(n_ + 1)]  # columns follow the photo's tapering edges
                slab(links, [(xr(y), y) for y in ys_] + [(xl(y), y) for y in reversed(ys_)], za, lambda x, y, k_=ckind: ds * br["z_" + k_])
                pieces += 1
        s0, s1 = min(p[0] for p in br["pieces_mm"][first][key]), max(p[1] for p in br["pieces_mm"][first][key])
        ys_ = [sy * (s0 + j * (s1 - s0) / round((s1 - s0) / 0.5)) for j in range(round((s1 - s0) / 0.5) + 1)]
        slab(back, [(edges(y)[1] - bins, y) for y in ys_] + [(edges(y)[0] + bins, y) for y in reversed(ys_)], ds * br["backing_z"][0], lambda x, y: ds * br["backing_z"][1])
    add("bracelet_links", links, "steel_photo", bevel=br["bevel"])
    add("bracelet_backing", back, "steel_gap")

    out = {"diameter": round(2 * rg["bezel_tip"], 3), "lug_to_lug": round(tt + tb, 3)}  # the coin-edge tips are the 41 mm anchor
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "strap": kind, "strap_pieces": pieces, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
