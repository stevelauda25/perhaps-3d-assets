"""watch_seiko_snkk22: build the Seiko 5 SNKK22K1 (gold tone, black dial) as a flat-backed front relief, like watch_seiko_snkl50.

Params: spec (config/watches/seiko-snkk22k1.json). Same frame as watch_seiko_snkl50: mm, origin = hand pivot, dial faces +z,
back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, bracelet built at final depth with
the smooth curl. Differences: applied gold frames with a cream lume insert (wide at 6 and 9, two bars at 12, none at 3), a raised
gold day-date frame, straight baton hour and minute hands with lume and broad square tails, a needle seconds hand with a plain
tail. SEIKO and the 5 shield stay in the dial map (pipeline/seiko_snkk22_dial.py); the material keys keep the steel names, their
colours are gold. Rebuild with --force after regenerating the dial map.
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    coll = bpy.data.collections.new("WATCH | Seiko 5 SNKK22K1 front relief")
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

    # ---- dial + rehaut, photo map on a planar UV ----
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

    # ---- raised gold day-date frame; applied gold frames with a lume insert: wide at 6 and 9, two bars at 12, none at 3 ----
    fr, box = cfg["daydate_frame"], tr["daydate_frame"]
    (fx, fy), (fw, fh), wl = box["centre_mm"], box["size_mm"], fr["wall"]
    g = Geo()
    for cx_, cy_, w_, h_ in ((fx, fy + fh / 2 - wl / 2, fw, wl), (fx, fy - fh / 2 + wl / 2, fw, wl),
                             (fx - fw / 2 + wl / 2, fy, wl, fh - 2 * wl), (fx + fw / 2 - wl / 2, fy, wl, fh - 2 * wl)):
        g.prism(rect(cx_, cy_, w_, h_), d["z"], d["z"] + fr["height"])
    add("daydate_frame", g, fr["material"])
    ix, ti = cfg["indices"], tr["indices"]
    z0, top = d["z"], d["z"] + ix["height"]
    r0, r1, le = ti["inner_mm"], ti["outer_mm"], ix["lume_inset_end"]
    frames, lume = Geo(), Geo()
    for hour in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12):
        if hour == 12:
            bw = (ti["wide_mm"]["12"] - ix["gap_12"]) / 2
            lw = sum(b - a for a, b in ti["wide_lume_mm"]["12"]) / 2
            bars = [(sx * (bw + ix["gap_12"]) / 2, bw, lw) for sx in (-1, 1)]
        else:
            k = str(hour)
            bars = [(0, ti["wide_mm"].get(k, ti["width_mm"]), ti["wide_lume_mm"].get(k, ti["lume_width_mm"]))]
        for bx, bw, lw in bars:
            frames.prism([rot(x, y, hour * 30) for x, y in rect(bx, (r0 + r1) / 2, bw, r1 - r0)], z0, top)
            lume.prism([rot(x, y, hour * 30) for x, y in rect(bx, (r0 + r1) / 2, lw, r1 - r0 - 2 * le)], top, top + ix["lume_height"])
    add("indices", frames, "steel_polished", bevel=0.04)
    add("indices_lume", lume, "lume")

    # ---- hands at the photo's time: faceted straight batons with lume and broad square tails, needle seconds ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    on_axis = lambda x, y, deg: 1.0 if abs(x * math.cos(math.radians(deg)) - y * math.sin(math.radians(deg))) < 1e-4 else 0.0

    def faceted(name, half, deg, z, mat="steel_polished"):
        g_ = Geo()
        for sx in (1, -1):
            slab(g_, [rot(sx * x, y, deg) for x, y in half], z, lambda x, y: z + th + hs["ridge"] * on_axis(x, y, deg))
        add(name, g_, mat, bevel=0.02)

    for name in ("hour", "minute"):
        h = t[name]
        L, tail, hw, tw, deg, z = h["length_mm"], h["tail_mm"], h["half_width_mm"], h["broad_tail_half_width_mm"], h["angle_deg"], hs["z"][name]
        faceted("hand_" + name, [(0, -tail), (tw, -tail), (tw, -0.3), (hw, 0.3), (hw, L), (0, L)], deg, z)
        a, b = h["lume_from_to_mm"]
        add("hand_%s_lume" % name, Geo().prism([rot(x, y, deg) for x, y in rect(0, (a + b) / 2, 2 * (hw - hs["lume_border"]), b - a)],
                                               z + th, z + th + 0.03), "lume")
    h = t["seconds"]
    L, tail, deg, z = h["length_mm"], h["tail_mm"], h["angle_deg"], hs["z"]["seconds"]
    nw, cw = h["half_width_mm"], h["tail_half_width_mm"]
    add("hand_seconds", Geo().prism([rot(x, y, deg) for x, y in
                                     [(nw, 0), (nw, L - 0.3), (0, L), (-nw, L - 0.3), (-nw, 0), (-cw, -tail), (cw, -tail)]],
                                    z, z + th), "steel_polished", bevel=0.02)
    hub_r, cap_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, z), (0, z)], segs=48), "steel_polished")
    zc, ch = z + th, hs["hub"]["cap_height"]
    add("hub_cap", Geo().lathe([(0, zc), (hub_r, zc), (hub_r, zc + ch * 0.6), (hub_r * 0.8, zc + ch), (0, zc + ch)], segs=48), "steel_polished")
    add("hub_hole", Geo().lathe([(0, zc + ch), (cap_r, zc + ch), (cap_r, zc + ch + 0.01), (0, zc + ch + 0.01)], segs=32), "gasket_black")

    # ---- crown: fluted cylinder on a radial axis at the traced angle ----
    cw = cfg["crown"]
    a = math.radians(math.degrees(math.atan2(*tr["crown_box"]["centre_mm"])) % 360)
    star = [((cw["radius"] if i % 2 == 0 else cw["radius"] - cw["flute_depth"]) * math.cos(math.pi * i / cw["teeth"]),
             (cw["radius"] if i % 2 == 0 else cw["radius"] - cw["flute_depth"]) * math.sin(math.pi * i / cw["teeth"])) for i in range(cw["teeth"] * 2)]
    m = Matrix(((math.cos(a), -math.sin(a), 0), (0, 0, 1), (math.sin(a), math.cos(a), 0))).transposed().to_4x4()
    m.translation = (0, 0, cw["z"])
    add("crown", Geo().prism(star, cw["r_from"], cw["r_to"], m), "steel_polished", bevel=0.15)

    # ---- lugs from the traced silhouette (left/right and top/bottom averaged) ----
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}

    def half(y):
        ys = [sil[k] for k in (round(y, 2), round(-y, 2)) if k in sil]
        return sum((p[2] - p[1]) / 2 for p in ys) / len(ys)

    lg = cfg["lug"]
    tip = tr["lug_tip_mm"]["mean"]
    steps = [lg["from_y"] + k * 0.25 for k in range(int((tip - lg["from_y"]) / 0.25) + 1)]
    outline = [(lg["inner_x"], lg["from_y"])] + [(half(y), y) for y in steps] + [(lg["inner_x"], tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * (abs(y) - lg["from_y"]) / (tip - lg["from_y"])
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_polished", bevel=lg["bevel"])

    # ---- solid end link between the lugs, then three columns of links ----
    br, el = cfg["bracelet"], cfg["end_link"]
    sil_max = min(max(sil), -min(sil)) - 0.25
    hw_at = lambda y: half(round(min(max(y, tip), sil_max) * 4) / 4)
    g = Geo()
    for sy in (1, -1):
        g.prism(rect(0, sy * (el["from_y"] + tip) / 2, 2 * lg["inner_x"], tip - el["from_y"]), 0.0, el["top_z"])  # solid end link
    add("end_links", g, "steel_brushed", bevel=el["bevel"], polished_bevel=True)
    zm = ds * (br["z0"] + br["z1"]) / 2
    box = curl(br["bend_y"], br["bend_radius"], zm)  # links bend with the curve (approved on SUR419P1)
    za, zb = ds * br["z0"], ds * br["z1"]

    groups, back = {}, Geo()
    rows = 0
    for sy in (1, -1):
        y0 = tip + br["gap"]
        while y0 < br["end_y"] - 0.5:  # backing plate per row, under every column
            y1 = min(y0 + br["pitch"], br["end_y"])
            hb = hw_at((y0 + y1) / 2) - 0.3
            box(back, -hb, hb, y0, y1, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
            y0 = y1
            rows += 1
        for f0, f1, phase, mat in br["columns"]:
            g = groups.setdefault(mat, Geo())
            y0 = tip + br["gap"] - phase * br["pitch"]
            while y0 < br["end_y"] - 0.5:
                a_, b_ = max(y0, tip + br["gap"]), min(y0 + br["pitch"] - br["gap"], br["end_y"])
                if b_ - a_ > 0.5:
                    ym = (a_ + b_) / 2
                    x0, x1 = f0 * hw_at(ym) + (br["gap"] / 2 if f0 else 0), f1 * hw_at(ym) - br["gap"] / 2
                    if f0:
                        box(g, x0, x1, a_, b_, za, zb, sy)
                        box(g, -x1, -x0, a_, b_, za, zb, sy)
                    else:
                        box(g, -x1, x1, a_, b_, za, zb, sy)
                y0 += br["pitch"]
    for mat, g in groups.items():
        add("bracelet_links_" + mat.split("_")[1], g, mat, bevel=br["bevel"], polished_bevel=mat != "steel_polished")
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    near = sorted(p[2] - p[1] for y, p in sil.items() if tip + 0.5 <= abs(y) <= tip + 3)  # same rows as the trace check
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "bracelet_next_to_case": round(near[len(near) // 2], 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "bracelet_rows": rows,
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
