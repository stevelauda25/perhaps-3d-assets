"""watch_seiko_spb335: build the Seiko Prospex SPB335J1 (black coated case, black dial, rubber strap) as a flat-backed front relief.

Params: spec (config/watches/seiko-spb335j1.json). Same frame as watch_seiko_srpg18: mm, origin = hand pivot, dial faces +z,
back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, strap built at final depth with
the house curl. Differences: an asymmetric cushion case (bulges on the crown side, left and right edges traced separately),
a black coin-edge bezel with the photo's 60-minute insert, black index frames with mint lume (double plate at 12), broad
baton hands with lume, a black seconds hand with a lume plate and red dot, and a rubber strap textured from the photo.
One photo map (pipeline/seiko_spb335_dial.py) serves the dial, the bezel insert and the strap. Rebuild with --force after
regenerating it.
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    pm = json.loads((ROOT / cfg["photo_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Seiko Prospex SPB335J1 front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    for key, rough in cfg["photo_roughness"].items():  # one image, three surfaces
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
    ds = cfg["pose"].get("depth_scale", 1.0)
    photo_uv = lambda x, y: (0.5 + x / (2 * pm["half_w_mm"]), 0.5 + (y - pm["centre_y_mm"]) / (2 * pm["half_h_mm"]))

    def add(name, geo, mat, bevel=None, polished_bevel=False, uv_of=None):  # polished_bevel: material name for the rounded edges
        me = geo.mesh(P + name, True if bevel else None) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured:  # planar UV, lines along the strap axis (model Y)
            uv, tile = me.uv_layers.new(name="UVMap"), textured[mat]["tile_mm"]
            for loop in me.loops:
                x, y, _ = me.vertices[loop.vertex_index].co
                uv.data[loop.index].uv = (y / tile, -x / tile)
        if uv_of:  # photo map: uv_of(x, y, z) -> map coordinates
            uv = me.uv_layers.new(name="UVMap")
            for loop in me.loops:
                uv.data[loop.index].uv = uv_of(*me.vertices[loop.vertex_index].co)
        if bevel:
            if polished_bevel:
                me.materials.append(mats[polished_bevel])
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            if polished_bevel:
                m.material = 1
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if not name.startswith("strap"):
            o.scale = (1, 1, ds)
        return o

    def upward(me):
        if me.polygons[0].normal.z < 0:
            for poly in me.polygons:
                poly.flip()
            me.update()
        return me

    rg, notch, inner_x = tr["rings_mm"], tr["notch_mm"], tr["horn_inner_x_mm"]
    tip = tr["horn_tip_mm"]["mean"]
    sides = {round(p[0], 2): p[1:] for p in tr["silhouette_y_left_right_mm"]}
    q = lambda y: round(round(y * 4) / 4, 2)
    edge = lambda y, k: (sides[q(y)][k] + sides[q(-y)][k]) / 2  # k 0 left, 1 right (crown rows interpolated); top and bottom averaged
    strap_half = {round(y, 2): h for y, h in tr["strap_half_y_mm"]}

    # ---- turtle case: one plate with horns either side of the strap, open in the middle for the dial ----
    c = cfg["case"]
    ys = [tip - k * 0.25 for k in range(int(2 * tip / 0.25) + 1)]
    right = [(inner_x, notch), (inner_x, tip)] + [(edge(y, 1), y) for y in ys] + [(inner_x, -tip), (inner_x, -notch)]
    left = [(-inner_x, -notch), (-inner_x, -tip)] + [(-edge(y, 0), y) for y in reversed(ys)] + [(-inner_x, tip), (-inner_x, notch)]
    outline = right + left
    opening = [(c["opening_r"] * math.sin(2 * math.pi * k / 192), c["opening_r"] * math.cos(2 * math.pi * k / 192)) for k in range(192)]
    add("case", plate([{"outer": outline, "holes": [opening]}], 0.0, c["top_z"], P + "case"), "case_brushed", bevel=c["bevel"], polished_bevel="black_polished")

    # dark lug wells between the horns: the strap is narrower than the gap, so the background would show through
    g = Geo()
    for sy in (1, -1):
        g.prism([(-inner_x, sy * (notch - 0.5)), (inner_x, sy * (notch - 0.5)), (inner_x, sy * tip), (-inner_x, sy * tip)], 0.0, c["lug_well_z"])
    add("lug_wells", g, "gasket_black")

    # ---- coin-edge bezel ring, photo-mapped compass insert, dark ring at the crystal edge, crystal ----
    bz = cfg["bezel"]
    n = tr["teeth_count"]
    star = [((rg["teeth_tip"] if i % 2 == 0 else rg["teeth_root"]) * math.sin(math.pi * i / n),
             (rg["teeth_tip"] if i % 2 == 0 else rg["teeth_root"]) * math.cos(math.pi * i / n)) for i in range(2 * n)]
    hole = [(bz["ring_inner_r"] * math.sin(2 * math.pi * k / 192), bz["ring_inner_r"] * math.cos(2 * math.pi * k / 192)) for k in range(192)]
    add("bezel_ring", plate([{"outer": star, "holes": [hole]}], bz["z0"], bz["ring_top_z"], P + "bezel_ring"), "black_polished", bevel=0.08)
    ri, ro = rg["insert_inner"], rg["insert_outer"]
    prof = [(ri, bz["z0"]), (ro, bz["z0"]), (ro, bz["insert_top_z"][1]), (ri, bz["insert_top_z"][0]), (ri, bz["z0"])]
    add("bezel_insert", Geo().lathe(prof, segs=192).mesh(P + "bezel_insert", True), "bezel_insert",
        uv_of=lambda x, y, z: photo_uv(x, y))
    gk = cfg["gasket"]
    add("gasket", Geo().lathe([(rg["crystal_edge"] - 0.1, gk["z0"]), (ri + 0.05, gk["z0"]), (ri + 0.05, gk["z1"]), (rg["crystal_edge"] - 0.1, gk["z1"]),
                               (rg["crystal_edge"] - 0.1, gk["z0"])], segs=192), "gasket_black")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (rg["crystal_edge"], cr["z0"]), (rg["crystal_edge"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial and sloped minute-track flange, photo map ----
    d = cfg["dial"]
    me = upward(Geo().lathe([(0, d["z"]), (rg["dial_edge"], d["z"]), (rg["flange_outer"], d["flange_z"])], segs=192).mesh(P + "dial", True))
    add("dial", me, "dial", uv_of=lambda x, y, z: photo_uv(x, y))

    # ---- applied indices: black frames with lume; a double plate pointed toward the centre at 12 ----
    ix, ti = cfg["indices"], tr["indices"]
    z0, z1 = d["z"], d["z"] + ix["height"]
    frames, lume = Geo(), Geo()
    for hr in range(1, 13):
        sh = ti["shapes_mm"]["12" if hr == 12 else "cardinal" if hr % 3 == 0 else "bar"]
        frames.prism([rot(x, y, hr * 30) for x, y in sh["outline"]], z0, z1)
        if hr == 12:  # split the pointed lume in two at the centre bar
            (px, py), (bx, by), (cx, cy) = sh["lume"][0], sh["lume"][1], sh["lume"][2]
            bw = ti["bar_12_half_width_mm"]
            yb = py + (by - py) * (bw - px) / (bx - px)  # where the V edge crosses x = bw
            right_half = [(bw, yb), (bx, by), (cx, cy), (bw, cy)]
            halves = [right_half, [(-x, y) for x, y in reversed(right_half)]]
        else:
            halves = [sh["lume"]]
        for lp in halves:
            lume.prism([rot(x, y, hr * 30) for x, y in lp], z1, z1 + ix["lume_height"])
    add("indices", frames, "black_polished", bevel=0.04)
    add("index_lume", lume, "lume")

    # ---- hands at the photo's time (traced outlines, already posed): rose gold with lume ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute"):
        z = hs["z"][name]
        add("hand_" + name, Geo().prism([tuple(p) for p in t[name]["outline_mm"]], z, z + th), "steel_polished", bevel=0.03)
        g = Geo()
        for lp in t[name]["lume_mm"]:
            g.prism([tuple(p) for p in lp], z + th, z + th + 0.03)
        add("hand_%s_lume" % name, g, "lume")
    sc, z = t["seconds"], hs["z"]["seconds"]
    add("hand_seconds", Geo().prism([tuple(p) for p in sc["outline_mm"]], z, z + th), "seconds_black", bevel=0.02)
    add("hand_seconds_lume", Geo().prism([tuple(p) for p in sc["lume_mm"][0]], z + th, z + th + 0.05), "lume")
    cx, cy = sc["dot_centre_mm"]
    add("hand_seconds_dot", Geo().lathe([(0, z + th), (sc["dot_radius_mm"], z + th), (sc["dot_radius_mm"], z + th + 0.06), (0, z + th + 0.06)],
                                        segs=32, m=Matrix.Translation((cx, cy, 0))), "seconds_red")
    hub_r, cap_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, z + th), (0, z + th)], segs=48), "seconds_black")
    zc, ch = z + th, hs["hub"]["cap_height"]
    add("hub_cap", Geo().lathe([(0, zc), (cap_r, zc), (cap_r, zc + ch * 0.6), (cap_r * 0.75, zc + ch), (0, zc + ch)], segs=48), "steel_polished")

    # ---- crown: fluted cylinder on a radial axis at the traced angle ----
    cw, tc = cfg["crown"], tr["crown"]
    a = math.radians(tc["angle_deg"])
    R0 = tc["radius_mm"]
    star = [((R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.cos(math.pi * i / cw["teeth"]),
             (R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.sin(math.pi * i / cw["teeth"])) for i in range(cw["teeth"] * 2)]
    m = Matrix(((math.cos(a), -math.sin(a), 0), (0, 0, 1), (math.sin(a), math.cos(a), 0))).transposed().to_4x4()
    m.translation = (0, 0, cw["z"])
    add("crown", Geo().prism(star, *tc["r_from_to_mm"], m), "black_polished", bevel=0.15)

    # ---- rubber strap: the photo's own strap (wave texture) along its length, house curl from the horn tips ----
    st = cfg["strap"]
    s_max = min(max(strap_half), -min(strap_half)) - 0.25
    hw_at = lambda s: (lambda y: (strap_half[y] + strap_half[-y]) / 2)(q(min(max(s, tip + 1.0), s_max)))  # clamped where the horns hide it
    off = tr["strap_offset_mm"]  # the photo's strap sits right of the pivot (taken from the crown side)
    zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], tip + st["bend_after_tip"]
    s_of = lambda y, z: abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
    box = curl(bend_y, R, zm)
    g = Geo()
    for sy in (1, -1):
        box(g, -1.0, 1.0, notch - st["under_case"], st["end_y"], ds * st["z0"], ds * st["z1"], sy)
    g.v = [(x * hw_at(s_of(y, z)), y, z) for x, y, z in g.v]  # unit width scaled to the traced taper
    add("strap", g, "strap_rubber", bevel=st["bevel"],
        uv_of=lambda x, y, z: photo_uv(x + off, math.copysign(s_of(y, z), y)))

    # ---- checks against the anchors ----
    out = {"diameter": round(max(edge(y / 4, 0) + edge(y / 4, 1) for y in range(-20, 21)), 3), "strap_next_to_case": round(2 * hw_at(tip + 1.5), 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "horn_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "strap_end_y_mm": st["end_y"],
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
