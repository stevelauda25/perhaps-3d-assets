"""watch_seiko_snke61: build the Seiko 5 SNKE61K1 (steel, navy dial, lume batons and hands) as a flat-backed front relief.

Params: spec (config/watches/seiko-snke61k1.json). Same frame and house values as watch_seiko_snk623: mm, origin = dial centre,
dial faces +z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, bracelet built at
final depth with the smooth curl. Differences (from the photo): applied steel batons with a lume insert at 1, 2, 4, 5, 7, 8,
10, 11; the printed 12, 9, 6 and the day-date window stay in the dial map; steel leaf hour and minute hands with a lume insert;
a steel seconds needle with an orange tip and a lume disc on its tail; short brushed lugs outside the bracelet and a
three-column end link from under the case to the lug tips; outer links from the lug tips, centre links half a row later.
Rebuild with --force after regenerating the dial map.
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
    coll = bpy.data.collections.new("WATCH | %s front relief" % cfg["model"])
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    d = cfg["dial"]
    mats["dial"] = photo_material("dial_photo", ROOT / cfg["dial_map"], d["roughness"])
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
    ds = cfg["pose"].get("depth_scale", 1.0)

    def add(name, geo, mat, bevel=None, polished_bevel=False):
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

    # ---- case, gasket, crystal ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), c["material"])
    gk = cfg["gasket"]
    add("gasket", Geo().lathe([(gk["r_in"], gk["z0"]), (gk["r_out"], gk["z0"]), (gk["r_out"], gk["z1"]), (gk["r_in"], gk["z1"])], segs=192), "gasket_black")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial + grey rehaut, photo map on a planar UV ----
    me = Geo().lathe([(0, d["z"]), (d["texture_edge_r"], d["z"]), (d["rehaut_r"], d["rehaut_z"])], segs=192).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    uv, H = me.uv_layers.new(name="UVMap"), d["map_half_mm"]
    for loop in me.loops:
        x, y, _ = me.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
    add("dial", me, "dial")

    # ---- applied steel batons with a lume insert ----
    ix, ti = cfg["indices"], tr["indices"]
    z0, top = d["z"], d["z"] + ix["height"]
    r0, r1, hw = ti["inner_mm"], ti["outer_mm"], ti["width_mm"] / 2
    li = ix["lume_inset"]
    batons, lume = Geo(), Geo()
    for hour in ti["hours"]:
        batons.prism([rot(x, y, hour * 30) for x, y in [(-hw, r0), (hw, r0), (hw, r1), (-hw, r1)]], z0, top)
        lume.prism([rot(x, y, hour * 30) for x, y in [(-hw + li, r0 + li), (hw - li, r0 + li), (hw - li, r1 - li), (-hw + li, r1 - li)]], top, top + ix["lume_height"])
    add("indices", batons, ix["material"], bevel=0.04)
    add("indices_lume", lume, "lume")

    # ---- hands at the photo's time, on the dial centre: steel leaf hands with a lume insert, seconds needle with a lume disc ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]

    def disc(r, za, zb, x, y, segs=32):
        return Geo().lathe([(0, za), (r, za), (r, zb), (0, zb)], segs=segs, m=Matrix.Translation((x, y, 0)))

    for name in ("hour", "minute"):
        h = t[name]
        L, deg, z = h["length_mm"], h["angle_deg"], hs["z"][name]
        hw_, rw, wy = h["half_width_mm"], h["root_half_width_mm"], h["widest_at"] * L
        add("hand_" + name, Geo().prism([rot(x, y, deg) for x, y in [(-rw, -0.8), (rw, -0.8), (hw_, wy), (0, L), (-hw_, wy)]], z, z + th), hs["material"], bevel=0.03)
        a, b = h["lume_from_to_mm"]
        lw = lambda y: hs["lume_half_width"] * hw_ * min(1.0, (L - y) / (L - wy), 1.0 if y >= wy else 0.6 + 0.4 * y / wy)  # follows the leaf
        insert = [(lw(y), y) for y in (a, wy, b)] + [(-lw(y), y) for y in (b, wy, a)]
        add("hand_%s_lume" % name, Geo().prism([rot(x, y, deg) for x, y in insert], z + th, z + th + 0.03), "lume")
    h = t["seconds"]
    L, deg, z, nw = h["length_mm"], h["angle_deg"], hs["z"]["seconds"], h["half_width_mm"]
    tip_from, tail, ta = h["tip_colour_from_mm"], h["tail_mm"], h["tail_angle_deg"]
    g = Geo().prism([rot(x, y, deg) for x, y in rect(0, tip_from / 2, 2 * nw, tip_from)], z, z + th)
    g.prism([rot(x, y, ta) for x, y in rect(0, tail / 2, 2 * h["tail_half_width_mm"], tail)], z, z + th)
    add("hand_seconds", g, hs["material"], bevel=0.02)
    add("hand_seconds_tip", Geo().prism([rot(x, y, deg) for x, y in [(-nw, tip_from), (nw, tip_from), (nw, L - 0.2), (0, L), (-nw, L - 0.2)]], z, z + th), "seconds_tip")
    tx, ty = rot(0, tail, ta)
    rl, rs = h["tail_disc_radius_mm"]
    add("hand_seconds_disc", disc(rs, z, z + th, tx, ty), hs["material"], bevel=0.03)
    add("hand_seconds_disc_lume", disc(rl, z + th, z + th + hs["seconds"]["disc_lume_z"], tx, ty), "lume")
    cap_r, hole_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (cap_r, d["z"]), (cap_r, z), (0, z)], segs=48), hs["material"])
    zc, ch = z + th, hs["hub"]["cap_height"]
    add("hub_cap", Geo().lathe([(0, zc), (cap_r, zc), (cap_r, zc + ch * 0.6), (cap_r * 0.8, zc + ch), (0, zc + ch)], segs=48), hs["material"])
    add("hub_hole", Geo().lathe([(0, zc + ch), (hole_r, zc + ch), (hole_r, zc + ch + 0.01), (0, zc + ch + 0.01)], segs=32), "gasket_black")

    # ---- crown: fluted cylinder on a radial axis at the traced angle ----
    cw_ = cfg["crown"]
    a = math.radians(math.degrees(math.atan2(*tr["crown_box"]["centre_mm"])) % 360)
    star = [((cw_["radius"] if i % 2 == 0 else cw_["radius"] - cw_["flute_depth"]) * math.cos(math.pi * i / cw_["teeth"]),
             (cw_["radius"] if i % 2 == 0 else cw_["radius"] - cw_["flute_depth"]) * math.sin(math.pi * i / cw_["teeth"])) for i in range(cw_["teeth"] * 2)]
    m = Matrix(((math.cos(a), -math.sin(a), 0), (0, 0, 1), (math.sin(a), math.cos(a), 0))).transposed().to_4x4()
    m.translation = (0, 0, cw_["z"])
    add("crown", Geo().prism(star, cw_["r_from"], cw_["r_to"], m), cw_["material"], bevel=0.15)

    # ---- lugs outside the bracelet, outline from the traced silhouette (left/right and top/bottom averaged) ----
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}

    def half_w(y):
        ys = [sil[k] for k in (round(y, 2), round(-y, 2)) if k in sil]
        return sum((p[2] - p[1]) / 2 for p in ys) / len(ys)

    lg, br = cfg["lug"], cfg["bracelet"]
    tip = tr["lug_tip_mm"]["mean"]
    bhw = tr["bracelet_half_width_mm"]
    split = tr["bracelet_centre_half"] * bhw  # centre column half width
    inner = bhw + br["gap"] / 2
    from_y = tr["lug_from_y_mm"]
    steps = [from_y + k * 0.25 for k in range(int((tip - from_y) / 0.25) + 1)]
    outline = [(inner, from_y)] + [(max(half_w(y), inner + 0.3), y) for y in steps] + [(inner, tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * max(abs(y) - lg["slope_from_y"], 0) / (tip - lg["slope_from_y"])
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

    # ---- bracelet: end link from under the case to the lug tips, then outer links from the tips and centre links half a row later ----
    zm = ds * (br["z0"] + br["z1"]) / 2
    box = curl(tip, br["bend_radius"], zm)  # links bend with the curve (approved on SUR419P1)
    za, zb = ds * br["z0"], ds * br["z1"]
    end_y = tip + br["bend_radius"] * 2.2
    centre_from = tr["bracelet_centre_first_joint_mm"] - br["pitch"]
    groups, back, rows = {}, Geo(), 0
    for sy in (1, -1):
        y0 = lg["end_link_from_y"]
        while y0 < end_y - 0.5:  # backing plate per row, under every column
            y1 = min(tip if y0 < tip else y0 + br["pitch"], end_y)
            box(back, -(bhw - 0.3), bhw - 0.3, y0, y1, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
            y0 = y1
            rows += 1
        for f0, f1, mat in br["columns"]:
            g = groups.setdefault(mat, Geo())
            x0, x1 = f0 * bhw + (br["gap"] / 2 if f0 else 0), f1 * bhw - br["gap"] / 2
            spans = [(lg["end_link_from_y"], tip - br["gap"])]  # end link
            y0 = tip + br["gap"] if f0 else centre_from + br["gap"]
            while y0 < end_y - 0.5:
                spans.append((max(y0, tip + br["gap"]), min(y0 + br["pitch"] - br["gap"], end_y)))
                y0 += br["pitch"]
            for a_, b_ in spans:
                if b_ - a_ > 0.5:
                    if f0:
                        box(g, x0, x1, a_, b_, za, zb, sy)
                        box(g, -x1, -x0, a_, b_, za, zb, sy)
                    else:
                        box(g, -x1, x1, a_, b_, za, zb, sy)
    for mat, g in groups.items():
        add("bracelet_links_" + mat.split("_")[0], g, mat, bevel=br["bevel"], polished_bevel=mat == "steel_brushed")
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "bracelet_width": round(2 * bhw, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    assert split < bhw and centre_from < tip + br["pitch"], "bracelet layout"
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "centre_first_joint_y_mm": tr["bracelet_centre_first_joint_mm"], "lug_to_lug_mm": round(2 * tip, 2),
            "end_y_mm": round(end_y, 2), "bracelet_rows": rows, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
