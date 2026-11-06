"""watch_seiko_sfk001: build the Seiko Prospex SFK001J1 (Sumo solar GMT, aqua wave dial, steel bracelet) as a flat-backed
front relief.

Params: spec (config/watches/seiko-sfk001j1.json). Same frame as watch_seiko_spb335: mm, origin = dial centre, dial faces
+z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, bracelet built at final
depth with the house curl. Parts: the Sumo case as one brushed plate from the photo outline with lugs either side of the
bracelet, a polished scalloped bezel ring with the photo's 60-minute insert, the wave dial, 24-hour flange and date from one
photo map (pipeline/seiko_sfk001_dial.py, hands removed), applied polished indices with lume (dots, trapezoids at 12, 6
and 9, a short bar at 3), polished hour, minute and seconds hands with lume, an orange GMT arrow hand, a fluted crown at
110 deg and a three-column bracelet: outer links from the lug tips, centre links 2 mm nearer the case. Rebuild with --force
after regenerating the photo map.
"""
import json
import math

import bpy
import numpy as np
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled
from pipeline.steps.watch_speedmaster import Geo, ROOT, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    pm = json.loads((ROOT / cfg["photo_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Seiko Prospex SFK001J1 front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    for key, rough in cfg["photo_roughness"].items():  # one image, two surfaces
        mats[key] = photo_material(key, ROOT / cfg["photo_map"], rough)
    textured = cfg.get("steel_textures", {})
    for key, tx in textured.items():  # brushed lines as a tangent-space normal map (plain image link, kept by the GLB)
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
    H = pm["half_mm"]
    photo_uv = lambda x, y: (0.5 + x / (2 * H), 0.5 + y / (2 * H))

    def add(name, geo, mat, bevel=None, polished_bevel=False, uv_of=None):
        me = geo.mesh(P + name, True if bevel else None) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured:  # planar UV, lines along the bracelet (model Y)
            uv, tile = me.uv_layers.new(name="UVMap"), textured[mat]["tile_mm"]
            for loop in me.loops:
                x, y, _ = me.vertices[loop.vertex_index].co
                uv.data[loop.index].uv = (y / tile, -x / tile)
        if uv_of:
            uv = me.uv_layers.new(name="UVMap")
            for loop in me.loops:
                uv.data[loop.index].uv = uv_of(*me.vertices[loop.vertex_index].co)
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

    circle = lambda r, n=192, cx=0.0, cy=0.0: [(cx + r * math.sin(2 * math.pi * k / n), cy + r * math.cos(2 * math.pi * k / n)) for k in range(n)]
    rg, notch, inner_x = tr["rings_mm"], tr["notch_mm"], tr["lug_inner_x_mm"]
    tip = tr["lug_tip_mm"]["mean"]
    bo_x, bo_y = tr["bezel_offset_mm"]
    boff = tr["bracelet_offset_mm"]
    sides = {round(p[0], 2): p[1:] for p in tr["silhouette_y_left_right_mm"]}
    q = lambda y: round(round(y * 4) / 4, 2)
    half = lambda y: min((sides[q(y)][0] + sides[q(y)][1]) / 2, sides[q(y)][0] + boff)  # mean edge; the left edge past the lugs (bracelet wall on the right)
    edge0 = lambda y: (half(y) + half(-y)) / 2  # top and bottom averaged
    edge = lambda y: sum(edge0(y + k * 0.25) for k in range(-4, 5)) / 9  # 2 mm running mean: the pixel silhouette is jagged

    # ---- Sumo case: one plate with lugs either side of the bracelet, open in the middle for the dial ----
    c = cfg["case"]
    ys = [tip - k * 0.25 for k in range(int(2 * tip / 0.25) + 1)]
    right = [(inner_x, notch), (inner_x, tip)] + [(edge(y), y) for y in ys] + [(inner_x, -tip), (inner_x, -notch)]
    outline = right + [(-x, -y) for x, y in right]
    add("case", plate([{"outer": outline, "holes": [circle(c["opening_r"])]}], 0.0, c["top_z"], P + "case"), "steel_brushed",
        bevel=c["bevel"], polished_bevel=True)

    # ---- polished scalloped bezel ring, photo-mapped insert (mapped from its own centre in the photo), polished lip, crystal ----
    bz = cfg["bezel"]
    n, depth = tr["teeth_count"], bz["scallop_depth"]
    # rounded lobes with a notch between them: r = tip - depth (1 - sin(pi f)), f = 0..1 across one scallop
    star = [(lambda a, f: ((rg["teeth_tip"] - depth * (1 - math.sin(math.pi * f))) * math.sin(a),
                           (rg["teeth_tip"] - depth * (1 - math.sin(math.pi * f))) * math.cos(a)))(2 * math.pi * k / (8 * n), (k % 8) / 8)
            for k in range(8 * n)]
    add("bezel_ring", plate([{"outer": star, "holes": [circle(bz["ring_inner_r"])]}], bz["z0"], bz["ring_top_z"], P + "bezel_ring"), "steel_polished", bevel=0.12)
    ri, ro = rg["insert_inner"], rg["insert_outer"]
    prof = [(ri, bz["z0"]), (ro, bz["z0"]), (ro, bz["insert_top_z"][1]), (ri, bz["insert_top_z"][0]), (ri, bz["z0"])]
    add("bezel_insert", Geo().lathe(prof, segs=192).mesh(P + "bezel_insert", True), "bezel_insert",
        uv_of=lambda x, y, z: photo_uv(x + bo_x, y + bo_y))
    (l0, l1), lz = bz["lip"]["r"], bz["lip"]["z1"]
    add("bezel_lip", Geo().lathe([(l0, bz["z0"]), (l1, bz["z0"]), (l1, lz), (l0, lz), (l0, bz["z0"])], segs=192), "steel_polished")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["r"], cr["z0"]), (cr["r"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- wave dial and sloped 24-hour flange, photo map ----
    d = cfg["dial"]
    me = upward(Geo().lathe([(0, d["z"]), (rg["dial_edge"], d["z"]), (d["flange_r"], d["flange_z"])], segs=192).mesh(P + "dial", True))
    add("dial", me, "dial", uv_of=lambda x, y, z: photo_uv(x, y))

    # ---- applied indices: polished frames with lume ----
    ix, ti = cfg["indices"], tr["indices"]
    z0, z1 = d["z"], d["z"] + ix["height"]
    frames, lume = Geo(), Geo()
    for hr in range(1, 13):
        if str(hr) in ti["shapes_mm"]:
            sh = ti["shapes_mm"][str(hr)]
            frames.prism([rot(x, y, hr * 30) for x, y in sh["outline"]], z0, z1)
            lume.prism([rot(x, y, hr * 30) for x, y in sh["lume"]], z1, z1 + ix["lume_height"])
        else:
            cx, cy = rot(0, ti["dot_r_mm"], hr * 30)
            frames.prism(circle(ti["dot_radius_mm"], 48, cx, cy), z0, z1)
            lume.prism(circle(ti["dot_lume_radius_mm"], 48, cx, cy), z1, z1 + ix["lume_height"])
    add("indices", frames, "steel_polished", bevel=0.05)
    add("index_lume", lume, "lume")

    # ---- hands at the photo's time (traced outlines, already posed about the pivot) ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    lh = hs["lume_height"]
    for name in ("gmt", "hour", "minute"):
        z = hs["z"][name]
        add("hand_" + name, Geo().prism([tuple(p) for p in t[name]["outline_mm"]], z, z + th), "gmt_orange" if name == "gmt" else "steel_polished", bevel=0.03)
        g = Geo()
        for lp in t[name]["lume_mm"]:
            g.prism([tuple(p) for p in lp], z + th, z + th + lh)
        add("hand_%s_lume" % name, g, "lume")
    sc, z = t["seconds"], hs["z"]["seconds"]
    cx, cy = sc["disc_centre_mm"]
    g = Geo().prism([tuple(p) for p in sc["outline_mm"]], z, z + th).prism(circle(sc["disc_radius_mm"], 48, cx, cy), z, z + th)
    add("hand_seconds", g, "steel_polished", bevel=0.02)
    add("hand_seconds_lume", Geo().prism(circle(sc["disc_lume_radius_mm"], 48, cx, cy), z + th, z + th + lh), "lume")
    hub_r, cap_r = tr["hub_radius_mm"]
    zc, ch = z + th, hs["hub_cap_height"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, hs["z"]["minute"] + th), (0, hs["z"]["minute"] + th)], segs=48), "steel_polished")
    add("hub_cap", Geo().lathe([(0, zc), (cap_r, zc), (cap_r, zc + ch * 0.6), (cap_r * 0.75, zc + ch), (0, zc + ch)], segs=48), "steel_polished")

    # ---- crown: fluted cylinder on a radial axis at the traced angle (about the bezel centre) ----
    cw, tc = cfg["crown"], tr["crown"]
    a = math.radians(tc["angle_deg"])
    R0 = tc["radius_mm"]
    star = [((R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.cos(math.pi * i / cw["teeth"]),
             (R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.sin(math.pi * i / cw["teeth"])) for i in range(cw["teeth"] * 2)]
    m = Matrix(((math.cos(a), -math.sin(a), 0), (0, 0, 1), (math.sin(a), math.cos(a), 0))).transposed().to_4x4()
    m.translation = (0, 0, cw["z"])
    add("crown", Geo().prism(star, cw["r_from"], tc["r_from_to_mm"][1], m), "steel_polished", bevel=0.2)

    # ---- three columns with the house curl: outer links from the lug tips, centre links nearer the case ----
    br, el = cfg["bracelet"], cfg["end_link"]
    fc = tr["bracelet_centre_fraction"]
    pitch, gap = tr["bracelet_pitch_mm"], br["gap"]
    outer0 = tip
    centre0 = tip + tr["bracelet_centre_joint_shift_mm"]
    sides_b = [sorted((abs(y), h) for y, h in tr["bracelet_half_y_mm"] if (y > 0) == top) for top in (True, False)]
    hw_at = lambda s: min(sum(np.interp(s, [p[0] for p in sd], [p[1] for p in sd]) for sd in sides_b) / 2, inner_x)  # ends held flat

    def columns(hw):
        """[(x0, x1, kind)] for one row."""
        return [(-fc * hw, fc * hw, "centre"), (fc * hw + gap, hw, "outer"), (-hw, -(fc * hw + gap), "outer")]

    zm = ds * (br["z0"] + br["z1"]) / 2
    box = curl(tip + br["bend_after_tip"], br["bend_radius"], zm)
    za, zb = ds * br["z0"], ds * br["z1"]
    links, ends, back = Geo(), Geo(), Geo()
    rows = 0
    for sy in (1, -1):
        for x0, x1, kind in columns(inner_x):
            box(ends, x0, x1, el["from_y"], (outer0 if kind == "outer" else centre0) - gap, 0.0, ds * el["top_z"], sy)
        for kind, start in (("outer", outer0), ("centre", centre0)):
            y0 = start
            while y0 < br["end_y"] - 0.5:
                y1 = min(y0 + pitch - gap, br["end_y"])
                hw = hw_at((y0 + y1) / 2)
                for x0, x1, k in columns(hw):
                    if k == kind:
                        box(links, x0, x1, y0, y1, za, zb, sy)
                if kind == "outer":
                    box(back, -(hw - 0.3), hw - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                y0 = y1 + gap
    add("bracelet_end_links", ends, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_links", links, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(edge(y / 4) for y in range(-20, 21)), 3), "lug_width": round(2 * hw_at(tip + 1.0), 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.5, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "bracelet_rows": rows,
            "bracelet_end_y_mm": br["end_y"], "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
