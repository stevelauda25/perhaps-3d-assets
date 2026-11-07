"""watch_tudor_bb54: build a TUDOR Black Bay 54 (M79000N-xxxx variant) as a flat-backed front relief (like the Seiko GLBs in models/watches/).

Copy of watch_tudor_ranger39 (untouched) for the Black Bay 54: rotating bezel with a black insert inside a steel coin-edge ring (numerals, markers and the
triangle come from the projected photo), domed crystal, snowflake hour hand / sword minute hand / lollipop seconds hand from profile and lume polygon
lists in the spec, a fluted crown without guards, and a strap section selected by `strap.kind`:
  "bracelet": three-column brushed steel bracelet (outer / centre / outer) at the photo's own joints (M79000N-0001, built)
  "rubber":   one continuous strap column over the silhouette (M79000N-0002; only the placeholder parameters exist, tune them from its photo)
Everything model specific is in the spec and the trace, so a variant only needs its own spec/measure JSON, maps and the strap section.
Spec per variant: config/watches/tudor-bb54-<sku>.json.

Params: spec. Same frame, pose (`SKO | pose`), 2.5D depth scale, materials as watch_seiko_front, whose helpers it reuses.
Parts: integrated case and lugs cut from the photo silhouette (top sloping into the strap), bezel ring (insert + coin edge), domed crystal, the dial photo
map (print, indices and track stay in the map), hands with lume, a fluted crown, and the strap.
Rebuild with --force after regenerating the dial map (the map is not in the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


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

    rg, cs, bz, d = tr["rings_mm"], cfg["case"], cfg["bezel"], cfg["dial"]
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

    # ---- bezel: steel coin-edge ring around a black insert (flat top, small chamfer toward the dial, rounded outer edge) ----
    ri, ro, rins = rg["bezel_in"], rg["bezel_out"], rg["insert_out"]
    add("bezel_ring", Geo().lathe([(ri, bz["z_inner"]), (ri + bz["chamfer_mm"], bz["z_insert"]), (rins, bz["z_insert"]), (rins, bz["z_coin"]), (ro - bz["round_mm"], bz["z_coin"]),
                                   (ro, bz["z_coin"] - bz["round_mm"]), (ro, bz["z0"]), (ri, bz["z0"])], segs=192), "steel_photo")

    # ---- crystal and dial ----
    cr = cfg["crystal"]
    ce = rg["crystal_edge"]
    dome = [(ce * f, cr["z1"] + cr["dome"] * (1 - f * f)) for f in (1.0, 0.85, 0.65, 0.4, 0.0)]  # shallow dome
    add("crystal", Geo().lathe([(0, cr["z0"]), (ce, cr["z0"]), (ce, cr["z1"])] + dome[1:], segs=192), "crystal")
    add("dial", photo_uv(Geo().lathe([(0, d["z"]), (rg["dial_flat"], d["z"]), (rg["crystal_edge"], d["rehaut_z"])], segs=192).mesh(P + "dial", True)), "dial")

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

    # ---- crown on the 3 o'clock axis: fluted cylinder plus a plain cap ----
    c, cw = cfg["crown"], tr["crown"]
    rad, r_from, r_to, r_fl = cw["radius_mm"], cw["x_mm"][0], cw["x_mm"][1], c["fluted_to_mm"]  # the fluted part starts where the photo shows it
    star = [((rad if i % 2 == 0 else rad - c["flute_depth"]) * math.cos(math.pi * i / c["teeth"]),
             (rad if i % 2 == 0 else rad - c["flute_depth"]) * math.sin(math.pi * i / c["teeth"])) for i in range(c["teeth"] * 2)]
    m = Matrix(((0, -1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_4x4()
    m.translation = (0, cw["centre_y_mm"], c["z"])
    add("crown", Geo().prism(star, r_from, r_fl, m), "steel_photo", bevel=c.get("bevel", 0.15))
    if "base_chamfer_mm" in c:  # chamfered shoulder on the case side of the fluted crown
        bc = c["base_chamfer_mm"]
        add("crown_base", Geo().lathe([(0, r_from), (rad * 0.8, r_from), (rad - 0.02, r_from + bc), (0, r_from + bc)], segs=48, m=m), "steel_photo", smooth=True)
    if "neck_radius_fraction" in c:  # narrower tube between the case and the fluted crown (the photo's rounded shoulder)
        add("crown_neck", Geo().lathe([(0, rg["bezel_out"] - 0.5), (rad * c["neck_radius_fraction"], rg["bezel_out"] - 0.5), (rad * c["neck_radius_fraction"], r_from + 0.1), (0, r_from + 0.1)], segs=48, m=m),
            "steel_photo", smooth=True)
    cap = [(0, r_fl), (rad - 0.1, r_fl), (rad * c["cap_radius_fraction"], r_to - 0.3), (rad * c["cap_radius_fraction"] * 0.6, r_to), (0, r_to)]
    add("crown_cap", Geo().lathe(cap, segs=48, m=m), "steel_photo", smooth=True)

    # ---- strap: strap.kind picks the section; every kind is flat columns of pieces at measured y ranges, top and bottom separately ----
    kind = cfg["strap"]["kind"]
    br = cfg["strap"][kind]
    gap, za, ins, bins = br["gap"], ds * br["z0"], br["inset"], br["backing_inset"]

    def centre(y):  # left and right x of the centre column at y: linear in the spec's [|y|, left, right] lists, one per side
        pts = br["centre_x_mm"]["top" if y > 0 else "bottom"]
        for (y0, l0, r0), (y1, l1, r1) in zip(pts, pts[1:]):
            if abs(y) <= y1:
                f = max(0.0, (abs(y) - y0) / (y1 - y0))
                return l0 + (l1 - l0) * f, r0 + (r1 - r0) * f
        return pts[-1][1], pts[-1][2]

    if kind == "bracelet":  # outer / centre / outer brushed columns with the photo's vertical joint lines
        cols = {"left": (lambda y: edges(y)[0] + ins, lambda y: centre(y)[0] - gap / 2, "outer"),
                "centre": (lambda y: centre(y)[0] + gap / 2, lambda y: centre(y)[1] - gap / 2, "centre"),
                "right": (lambda y: centre(y)[1] + gap / 2, lambda y: edges(y)[1] - ins, "outer")}
    elif kind == "rubber":  # one column over the whole silhouette width (pieces_mm.strap lists the transverse grooves / end pieces)
        cols = {"strap": (lambda y: edges(y)[0] + ins, lambda y: edges(y)[1] - ins, "strap")}
    else:
        raise ValueError("strap.kind %r" % kind)
    first = next(iter(cols.values()))[2]
    links, back, pieces = Geo(), Geo(), 0
    for sy, key in ((1, "top"), (-1, "bottom")):
        for xl, xr, ckind in cols.values():
            lst = br["pieces_mm"][ckind][key]
            for k, (a_, b_) in enumerate(lst):
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

    out = {"diameter": round(2 * max(abs(p[1]) for p in tr["silhouette_y_left_right_mm"] if abs(p[0]) < 3), 3), "lug_to_lug": round(tt + tb, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "strap": kind, "strap_pieces": pieces, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}


def _on_axis(x, y, deg):
    """1 on the radial centre line through angle deg (the ridge), 0 elsewhere."""
    a = math.radians(deg)
    return 1.0 if abs(x * math.cos(a) - y * math.sin(a)) < 1e-4 else 0.0
