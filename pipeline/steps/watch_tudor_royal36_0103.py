"""Variant copy for M2836C1A0-0103 of watch_tudor_royal36: identical except spec key hands.lume_material (default "lume") picks the lume strip material,
so it can show the front-projected photo (steel_photo) like the hands. Do not edit watch_tudor_royal36.py (shared).
"""
"""watch_tudor_royal36: build a TUDOR Royal 36 (M2836C1A0-xxxx variant; spec key hands.material picks the hand metal, default gold) as a flat-backed front relief (like the Seiko GLBs in models/watches/).

Params: spec (config/watches/tudor-royal36-m2836c1a0-0101.json). Same frame, pose (`SKO | pose`), 2.5D depth scale, materials and
bracelet curl as watch_seiko_front, whose helpers it reuses. Parts: integrated case and lugs cut from the photo silhouette (brushed
top sloping into the bracelet), a 48-segment bezel (plain polished facets alternating with five-rib facets), box crystal, the dial
photo map (print, Roman numerals, date window and track stay in the map), gold baton hands with lume, a fluted crown, and a brushed
bracelet with two polished channels. Rebuild with --force after regenerating the dial map (the map is not in the stage fingerprint).
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
    coll = bpy.data.collections.new("WATCH | Tudor Royal 36 M2836C1A0-0103 front relief")
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
        if mat == "steel_photo":
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

    def half(y):  # case half width at y (nearest 0.25 mm row of the photo silhouette)
        return (lambda p: (p[2] - p[1]) / 2)(sil[round(round(max(-32.5, min(29.75, y)) * 4) / 4, 2)])

    # ---- integrated case and lugs from the silhouette (own length top and bottom), top sloping into the bracelet ----
    tt, tb = cs["tip_top"], cs["tip_bottom"]
    ys = [-tb + k * 0.25 for k in range(int(round((tt + tb) / 0.25)) + 1)]
    outline = [(half(y), y) for y in ys] + [(-half(y), y) for y in reversed(ys)]
    ramp = lambda x, y: cs["body_z"] - (cs["body_z"] - cs["tip_z"]) * min(1.0, max(0.0, (abs(y) - cs["ramp_from_y"]) / ((tt if y > 0 else tb) - cs["ramp_from_y"])))
    g = Geo()
    slab(g, outline, 0.0, ramp)
    add("case", g, "steel_photo", bevel=cs["bevel"])

    # ---- bezel: polished ring, 24 plain facets, 24 five-rib facets ----
    ri, ro, n_seg = rg["bezel_in"], rg["bezel_out"], 48
    seg = 360.0 / n_seg

    def sector(a0, a1):
        arc = [a0 + (a1 - a0) * k / bz["arc_steps"] for k in range(bz["arc_steps"] + 1)]
        return [rot(0, ro, a) for a in arc] + [rot(0, ri, a) for a in reversed(arc)]

    add("bezel_ring", Geo().lathe([(ri, bz["z0"]), (ro, bz["z0"]), (ro, bz["z_base"]), (ri, bz["z_base"])], segs=192), "steel_photo")
    plain, ribs, grooves = Geo(), Geo(), Geo()
    nr, fill, ratio = bz["ribs"], bz["rib_fill"] * seg, bz["rib_to_gap"]
    rw = fill / (nr + (nr - 1) / ratio)
    for k in range(n_seg // 2):
        c = 2 * k * seg  # plain facet centred on 0, 15, 30 ... deg
        plain.prism(sector(c - seg / 2 + 0.15, c + seg / 2 - 0.15), bz["z_base"] - 0.05, bz["z_plain"])
        c += seg  # ribbed facet centred on 7.5 + 15 k deg
        grooves.prism(sector(c - seg / 2 + 0.15, c + seg / 2 - 0.15), bz["z_base"] - 0.05, bz["z_base"] + 0.02)
        for j in range(nr):
            a0 = c - fill / 2 + j * (rw + rw / ratio)
            ribs.prism(sector(a0, a0 + rw), bz["z_base"] - 0.05, bz["z_rib"])
    add("bezel_plain", plain, "steel_photo", bevel=0.05)
    add("bezel_grooves", grooves, "steel_photo")
    add("bezel_ribs", ribs, "steel_photo")

    # ---- crystal and dial ----
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (rg["crystal_edge"], cr["z0"]), (rg["crystal_edge"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")
    add("dial", photo_uv(Geo().lathe([(0, d["z"]), (rg["dial_flat"], d["z"]), (rg["crystal_edge"], d["rehaut_z"])], segs=192).mesh(P + "dial", True)), "dial")

    # ---- hands at the photographed pose: gold batons (lume strip), thin seconds needle with a counterweight ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute", "seconds"):
        h = t[name]
        L, deg, z, hw, tw = h["length_mm"], h["angle_deg"], hs["z"][name], hs["half_width"][name], hs["tail_half_width"][name]
        r = hw
        tipArc = [(hw * math.cos(math.radians(a)), L - r + r * math.sin(math.radians(a))) for a in range(0, 91, 18)]
        half_outline = [(0, -h["tail_mm"]), (tw, -h["tail_mm"]), (tw, -0.3), (hw, 0.0), *tipArc]
        g_ = Geo()
        for sx in (1, -1):  # two facets meeting at a ridge on the centre line
            slab(g_, [rot(sx * x, y, deg) for x, y in half_outline], z, lambda x, y, z=z, deg=deg: z + th + hs["ridge"] * _on_axis(x, y, deg))
        add("hand_" + name, g_, hs.get("material", "gold"), bevel=0.02)
        if name != "seconds":
            f0, f1 = tr["hand_lume"][name]
            lw = hs["lume_half_width"][name]
            add("lume_" + name, Geo().prism([rot(x, y, deg) for x, y in rect(0, (f0 + f1) / 2 * L, 2 * lw, (f1 - f0) * L)],
                                           z + th + hs["ridge"] * 0.4, z + th + hs["ridge"] + hs["lume_height"]), hs.get("lume_material", "lume"))
    hub_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, hs["z"]["minute"] + th), (hub_r * 0.55, hs["z"]["seconds"] + th + 0.1), (0, hs["z"]["seconds"] + th + 0.1)], segs=48),
        hs.get("material", "gold"), smooth=True)

    # ---- crown on the 3 o'clock axis: fluted cylinder plus a plain cap ----
    c, cw = cfg["crown"], tr["crown"]
    rad, r_from, r_to, r_fl = cw["radius_mm"], rg["bezel_out"] - 0.3, cw["x_mm"][1], c["fluted_to_mm"]
    star = [((rad if i % 2 == 0 else rad - c["flute_depth"]) * math.cos(math.pi * i / c["teeth"]),
             (rad if i % 2 == 0 else rad - c["flute_depth"]) * math.sin(math.pi * i / c["teeth"])) for i in range(c["teeth"] * 2)]
    m = Matrix(((0, -1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_4x4()
    m.translation = (0, cw["centre_y_mm"], c["z"])
    add("crown", Geo().prism(star, r_from, r_fl, m), "steel_photo", bevel=0.15)
    cap = [(0, r_fl), (rad - 0.1, r_fl), (rad * c["cap_radius_fraction"], r_to - 0.3), (rad * c["cap_radius_fraction"] * 0.6, r_to), (0, r_to)]
    add("crown_cap", Geo().lathe(cap, segs=48, m=m), "steel_photo", smooth=True)

    # ---- bracelet at the photo's own row joints and polished pieces (top and bottom measured separately), flat ----
    br = cfg["bracelet"]
    gap, za = br["gap"], ds * br["z0"]
    links, chans, back = Geo(), Geo(), Geo()
    box = curl(1e6, 1.0, 0.0)  # no bend: a plain box
    c0, c1 = br["channel_x_mm"]
    rows = 0
    for sy, key in ((1, "top"), (-1, "bottom")):
        for k, (a_, b_) in enumerate(br["rows_mm"][key]):
            y0, y1 = a_ + (gap / 2 if k else 0), b_ - gap / 2
            w = half(sy * (y0 + y1) / 2) - 0.1
            ys_ = [y0 + k * (y1 - y0) / max(1, round((y1 - y0) / 0.25)) for k in range(max(1, round((y1 - y0) / 0.25)) + 1)]
            ys_ = [sy * v for v in ys_]  # rows follow the photo's rounded outer edges
            slab(links, [(half(y) - 0.1, y) for y in ys_] + [(-half(y) + 0.1, y) for y in reversed(ys_)], za, lambda x, y: ds * br["z_outer"])
            box(back, -(w - 0.3), w - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
            rows += 1
        for a_, b_ in br["channel_pieces_mm"][key]:
            for x0, x1 in ((c0, c1), (-c1, -c0)):
                box(chans, x0, x1, a_, b_, za, ds * br["z_channel"], sy)
    add("bracelet_links", links, "steel_photo", bevel=br["bevel"])
    add("bracelet_channels", chans, "steel_photo", bevel=0.05)
    add("bracelet_backing", back, "steel_gap")

    out = {"diameter": round(2 * max(abs(p[1]) for p in tr["silhouette_y_left_right_mm"] if abs(p[0]) < 3), 3), "lug_to_lug": round(tt + tb, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "bracelet_rows": rows, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}


def _on_axis(x, y, deg):
    """1 on the radial centre line through angle deg (the ridge), 0 elsewhere."""
    a = math.radians(deg)
    return 1.0 if abs(x * math.cos(a) - y * math.sin(a)) < 1e-4 else 0.0
