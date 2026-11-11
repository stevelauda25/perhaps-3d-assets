"""watch_tissot_t137207: build the Tissot T137.207.11.091.00 (PRX Powermatic 80, 35 mm, green waffle dial, integrated steel
bracelet) as a flat-backed front relief.

Params: spec (config/watches/tissot-t137.207.11.091.00.json). Frame as watch_tissot_t127407: mm, origin = hand pivot, dial
faces +z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, bracelet built at final
depth with the house curl. Parts from the official render: a brushed case whose flanks run straight into the bracelet (one
body from the traced outline, cut square where the first links start); a wide polished bezel; applied polished batons
(double at 12) with a lume inset at the inner end; a polished date frame at 3; faceted baton hands with a lume strip and a
short tail; a thin seconds hand with a counterweight; a fluted crown; an integrated H-link bracelet that tapers, outer pieces
starting with a short link and centre pieces offset by half a link. The dial (waffle, prints, minute track, date disc) is
the photo map from pipeline/tissot_t137207_dial.py. Rebuild with --force after regenerating the map.
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_hamilton_scuba_pioneer import circle
from pipeline.steps.watch_orient_ra_ak0705r10b import ridge
from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    dm = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | " + cfg["model"] + " front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    d = cfg["dial"]
    mats["dial"] = photo_material("dial_photo", ROOT / cfg["dial_map"], d["roughness"])
    textured = cfg.get("steel_textures", {})
    for key, tx in textured.items():  # brushed lines as a tangent-space normal map: a plain image link, so the GLB keeps it
        nodes, links = mats[key].node_tree.nodes, mats[key].node_tree.links
        b = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
        im = bpy.data.images.load(str(ROOT / tx["normal"]), check_existing=True)
        im.colorspace_settings.name = "Non-Color"
        im.pack()
        tex, nm = nodes.new("ShaderNodeTexImage"), nodes.new("ShaderNodeNormalMap")
        tex.image, tex.location, nm.location = im, (-600, -300), (-250, -300)
        nm.inputs["Strength"].default_value = tx["strength"]
        links.new(tex.outputs["Color"], nm.inputs["Color"])
        links.new(nm.outputs["Normal"], b.inputs["Normal"])

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location, pose.scale = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"]), (0.001,) * 3
    ds = cfg["pose"]["depth_scale"]

    def add(name, geo, mat, bevel=None, polished_bevel=False, smooth=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured:  # planar UV in mm / tile; lines along the bracelet (model Y)
            uv, tile = me.uv_layers.new(name="UVMap"), textured[mat]["tile_mm"]
            for loop in me.loops:
                x, y, _ = me.vertices[loop.vertex_index].co
                uv.data[loop.index].uv = (y / tile, -x / tile)
        if bevel:
            if polished_bevel:
                me.materials.append(mats["steel_polished"])
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            if polished_bevel:
                m.material = 1
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if not name.startswith("bracelet"):
            o.scale = (1, 1, ds)
        return o

    def upward(me):
        if me.polygons[0].normal.z < 0:
            for poly in me.polygons:
                poly.flip()
            me.update()
        return me

    rg, c, cr = tr["rings_mm"], cfg["case"], cfg["crystal"]
    tip = tr["lug"]["tip_mm"]

    # ---- case: the traced outline, symmetric about the pivot, cut square at the bracelet ----
    hw = sorted((y, h) for y, h in tr["case_half_width_mm"])
    outline = [(h, y) for y, h in hw[::-1]] + [(-h, y) for y, h in hw]
    add("case", plate([{"outer": outline, "holes": [circle(rg["bezel_in"] - 0.2, 192)]}], 0.0, c["top_z"], P + "case"), "steel_brushed",
        bevel=c["bevel"], polished_bevel=True)

    # ---- wide polished bezel, crystal ----
    bz = cfg["bezel"]
    add("bezel", Geo().lathe([(rg["bezel_out"], c["top_z"] - 0.4), (rg["bezel_out"], bz["outer_z"]), (rg["bezel_out"] - 0.35, bz["top_z"]),
                              (rg["bezel_in"] + 0.25, bz["top_z"]), (rg["bezel_in"], bz["top_z"] - 0.15), (rg["bezel_in"], c["top_z"] - 0.4)], segs=256),
        "steel_polished", smooth=True)
    add("crystal", Geo().lathe([(0, cr["z0"]), (rg["bezel_in"] + 0.02, cr["z0"]), (rg["bezel_in"] + 0.02, cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial flat to the rehaut, photo map on a planar UV about the pivot ----
    me = upward(Geo().lathe([(0, d["z"]), (rg["dial"], d["z"]), (rg["bezel_in"], d["rehaut_z"])], segs=256).mesh(P + "dial", True))
    uv = me.uv_layers.new(name="UVMap")
    H = dm["half_size_mm"]
    for loop_ in me.loops:
        x, y, _ = me.vertices[loop_.vertex_index].co
        uv.data[loop_.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
    add("dial", me, "dial")

    # ---- applied polished batons (double at 12, none at 3) with a lume inset at the inner end; polished date frame ----
    ix, ti = cfg["indices"], tr["index"]
    z0, top = d["z"], d["z"] + ix["height"]
    bars, lume = Geo(), Geo()
    l0, l1 = ti["lume"]
    for hr in range(12):
        if hr == 3:
            continue
        for off, h in (((-ti["double_offset"], ti["double_half"]), (ti["double_offset"], ti["double_half"])) if hr == 0 else ((0.0, ti["half"]),)):
            bars.prism([rot(x, y, hr * 30) for x, y in [(off + h, ti["inner"]), (off + h, ti["outer"]), (off - h, ti["outer"]), (off - h, ti["inner"])]], z0, top)
            lh = min(ti["lume_half"], h - 0.08)
            lume.prism([rot(x, y, hr * 30) for x, y in [(off + lh, l0), (off + lh, l1), (off - lh, l1), (off - lh, l0)]], z0, top + 0.01)
    add("indices", bars, "steel_polished", bevel=ix["bevel"])
    add("indices_lume", lume, "lume")
    fx0, fy0, fx1, fy1 = tr["date_mm"]["frame"]
    ox0, oy0, ox1, oy1 = tr["date_mm"]["opening"]
    sq = lambda a, b, c_, d_: [(a, d_), (c_, d_), (c_, b), (a, b)]
    add("date_frame", plate([{"outer": sq(fx0, fy0, fx1, fy1), "holes": [sq(ox0, oy0, ox1, oy1)]}], z0, z0 + ix["date_height"], P + "date_frame"),
        "steel_polished", bevel=ix["date_bevel"])

    # ---- hands at the render's time: faceted batons with a lume strip, seconds hand with counterweight ----
    hs, t = cfg["hands"], tr["hands"]
    th, ridge_h = hs["thickness"], hs["ridge"]
    for name in ("hour", "minute"):
        h, z = t[name], hs["z"][name]
        st = [(r, w) for r, w in h["outline_mm"]]
        st[0], st[-1] = (st[0][0], 0.0), (st[-1][0], 0.0)
        g = Geo()
        ridge(g, st, z, th + ridge_h, th / (th + ridge_h), h["angle_deg"])
        add("hand_" + name, g, "steel_polished", bevel=0.015)
        a0, a1 = h["lume_mm"]
        lh = h["lume_half_mm"]
        zl = z + th + ridge_h + hs["lume_raise"]
        add("hand_%s_lume" % name, Geo().prism([rot(x, y, h["angle_deg"]) for x, y in [(lh, a0), (lh, a1), (-lh, a1), (-lh, a0)]], z + th * 0.5, zl), "lume")
    h = t["seconds"]
    L, deg, z = h["length_mm"], h["angle_deg"], hs["z"]["seconds"]
    nw, tl, tw = h["half_width_mm"], h["tail_mm"], h["tail_half_mm"]
    add("hand_seconds", Geo().prism([rot(x, y, deg) for x, y in [(-tw * 0.7, -tl), (tw * 0.7, -tl), (tw, -tl + 0.4), (tw, -1.2), (nw * 1.2, 0), (nw, L - 0.3), (0, L),
                                                                  (-nw, L - 0.3), (-nw * 1.2, 0), (-tw, -1.2), (-tw, -tl + 0.4)]], z, z + th),
        "steel_polished", bevel=0.01)
    collar_r, cap_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (collar_r, d["z"]), (collar_r, hs["z"]["minute"] + th), (0, hs["z"]["minute"] + th)], segs=64), "steel_polished", bevel=0.02)
    zc = z + th
    add("hub_cap", Geo().lathe([(0, zc), (cap_r, zc), (cap_r, zc + 0.1), (cap_r * 0.6, zc + 0.16), (0, zc + 0.16)], segs=48), "steel_polished")

    # ---- crown at 3 ----
    cw_, crn = cfg["crown"], tr["crown"]
    a = math.radians(crn["angle_deg"])
    R0, teeth = crn["radius_mm"], crn["teeth"]
    star = [((R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.cos(math.pi * i / teeth), (R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.sin(math.pi * i / teeth))
            for i in range(teeth * 2)]
    u_, dr_ = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
    m = Matrix((u_, (0, 0, 1), dr_)).transposed().to_4x4()
    m.translation = (0, 0, cw_["z"])
    r0, r1 = crn["r_mm"]
    add("crown_collar", Geo().lathe([(0, r0 - 1.0), (R0 * 0.6, r0 - 1.0), (R0 * 0.6, r0 + 0.5), (0, r0 + 0.5)], segs=48, m=m), "steel_polished", bevel=0.08)
    add("crown", Geo().prism(star, r0 + 0.5, r1, m), "steel_polished", bevel=0.12)

    # ---- integrated H-link bracelet: tapering, outer pieces start with a short link, centre pieces half a link off ----
    br, bt = cfg["bracelet"], tr["bracelet"]
    gap, pitch = br["gap"], bt["pitch_mm"]
    half = lambda s: bt["half_at_tip_mm"] - bt["taper_mm_per_mm"] * (s - tip)
    zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]
    bent_box = curl(tip + br.get("bend_after_tip", 0.0), R, zm)
    outer, centre, back = Geo(), Geo(), Geo()
    za, zb = ds * br["z0"], ds * br["z1"]
    rows = 0
    for sy in (1, -1):
        for kind in ("outer", "centre"):
            y0, first = tip + gap, True
            while y0 < br["end_y"] - 0.3:
                y1 = min(y0 + (bt["outer_first_mm"] if first and kind == "outer" else pitch) - gap, br["end_y"])
                first = False
                hm = half((y0 + y1) / 2)
                ch = bt["centre_ratio"] * hm
                if kind == "outer":
                    for sx in (1, -1):
                        x0, x1 = sorted((sx * (ch + gap / 2), sx * hm))
                        bent_box(outer, x0, x1, y0, y1, za, zb, sy)
                    bent_box(back, -(hm - 0.3), hm - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                else:
                    bent_box(centre, -(ch - gap / 2), ch - gap / 2, y0, y1, za, zb + ds * br["centre_raise"], sy)
                y0 = y1 + gap
    add("bracelet_links", outer, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_centre", centre, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"case_width": round(2 * max(h for _, h in hw), 3), "case_length": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "bracelet_rows": rows, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
