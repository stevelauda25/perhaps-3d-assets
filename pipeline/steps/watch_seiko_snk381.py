"""watch_seiko_snk381: build the Seiko 5 SNK381K1 as a flat-backed front relief, like watch_seiko_front (SNK607K1).

Params: spec (config/watches/seiko-snk381k1-v1.json). Same frame as watch_seiko_front: mm, origin = hand pivot, dial faces +z,
back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, bracelet built at final depth.
Differences from the SNK607K1: the applied numerals stay in the dial map (pipeline/seiko_snk381_dial.py), leaf-shaped hour and
minute hands, a dark seconds hand with a lume disc on its tail, a black hub cap, and a five-column bracelet whose mid links sit
half a row off. Rebuild with --force after regenerating the dial map (it is not part of the stage fingerprint).
shortcut: case/dial/crown/lug code mirrors watch_seiko_front.run; fold both into one config-driven step once the SNK607K1 work settles.
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, photo_material, plate, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    coll = bpy.data.collections.new("WATCH | Seiko 5 SNK381K1 front relief")
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

    # ---- day-date frame, applied 5 shield, hour dots ----
    fr, box = cfg["daydate_frame"], tr["daydate_frame"]
    (fx, fy), (fw, fh), wl = box["centre_mm"], box["size_mm"], fr["wall"]
    g = Geo()
    for cx_, cy_, w_, h_ in ((fx, fy + fh / 2 - wl / 2, fw, wl), (fx, fy - fh / 2 + wl / 2, fw, wl),
                             (fx - fw / 2 + wl / 2, fy, wl, fh - 2 * wl), (fx + fw / 2 - wl / 2, fy, wl, fh - 2 * wl)):
        g.prism(rect(cx_, cy_, w_, h_), d["z"], d["z"] + fr["height"])
    add("daydate_frame", g, "steel_polished")
    lg_ = cfg["logo"]
    add("logo_5_shield", plate(tr["logo_5_shield_shapes"], d["z"], d["z"] + lg_["shield_height"], P + "logo_5_shield"), "steel_polished")
    g = Geo()
    for dot in tr["lume_dots"].values():
        x, y = rot(0, dot["radius_mm"], dot["angle_deg"])
        g.lathe([(0, d["z"]), (lg_["lume_dot_radius"], d["z"]), (lg_["lume_dot_radius"], d["z"] + 0.05), (0, d["z"] + 0.05)], segs=24, m=Matrix.Translation((x, y, 0)))
    add("lume_dots", g, "lume")

    # ---- hands at the photo's time: leaf hour and minute hands, seconds with a lume disc on its tail ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]

    def disc(r, z0, z1, x, y, segs=32):
        return Geo().lathe([(0, z0), (r, z0), (r, z1), (0, z1)], segs=segs, m=Matrix.Translation((x, y, 0)))

    for name in ("hour", "minute"):
        L, s, deg, z0 = t[name]["length_mm"], hs[name], t[name]["angle_deg"], hs["z"][name]
        hw, rw, wy = s["half_width"], s["root_half_width"], s["widest_at"] * L
        add("hand_" + name, Geo().prism([rot(x, y, deg) for x, y in [(-rw, -1.0), (rw, -1.0), (hw, wy), (0, L), (-hw, wy)]], z0, z0 + th), "steel_polished", bevel=0.03)
        a, b = t[name]["lume_from_to_mm"]
        lw = lambda y: s["lume_half_width"] * min(1.0, (L - y) / (L - wy), 1.0 if y >= wy else 0.6 + 0.4 * y / wy)  # follows the leaf
        lume = [(lw(y), y) for y in (a, wy, b)] + [(-lw(y), y) for y in (b, wy, a)]
        add("hand_%s_lume" % name, Geo().prism([rot(x, y, deg) for x, y in lume], z0 + th, z0 + th + 0.03), "lume")
    s, z0 = hs["seconds"], hs["z"]["seconds"]
    L, tail = t["seconds"]["length_mm"], t["seconds"]["tail_mm"]
    rl, rr_ = t["seconds"]["tail_disc_radius_mm"]
    g = Geo().prism([rot(x, y, t["seconds"]["angle_deg"]) for x, y in rect(0, L / 2, 2 * s["half_width"], L)], z0, z0 + th)
    g.prism([rot(x, y, t["seconds"]["tail_angle_deg"]) for x, y in rect(0, tail / 2, 2.5 * s["half_width"], tail)], z0, z0 + th)
    tx, ty = rot(0, tail, t["seconds"]["tail_angle_deg"])
    add("hand_seconds", g, "hand_dark", bevel=0.03)
    add("hand_seconds_disc", disc(rr_, z0, z0 + th, tx, ty), "steel_polished", bevel=0.03)
    add("hand_seconds_disc_lume", disc(rl, z0 + th, z0 + th + s["disc_lume_z"], tx, ty), "lume")
    hub_r, cap_r = t["hub_radius_mm"][1], t["hub_radius_mm"][0]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, z0), (0, z0)], segs=48), "steel_polished")
    zc, ch = z0 + th, hs["hub"]["cap_height"]
    add("hub_cap", Geo().lathe([(0, zc), (cap_r, zc), (cap_r, zc + ch * 0.6), (cap_r * 0.6, zc + ch), (0, zc + ch)], segs=48), "gasket_black")

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
    tip = next(y / 4 for y in range(64, 160) if half(y / 4) < lg["inner_x"] + 0.35)
    steps = [lg["from_y"] + k * 0.25 for k in range(int((tip - lg["from_y"]) / 0.25) + 1)]
    outline = [(lg["inner_x"], lg["from_y"])] + [(half(y), y) for y in steps] + [(lg["inner_x"], tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * (abs(y) - lg["from_y"]) / (tip - lg["from_y"])
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

    # ---- solid end link between the lugs, then five columns of links ----
    br, el = cfg["bracelet"], cfg["end_link"]
    sil_max = min(max(sil), -min(sil)) - 0.25
    hw_at = lambda y: half(round(min(max(y, tip), sil_max) * 4) / 4)
    g = Geo()
    for sy in (1, -1):
        g.prism(rect(0, sy * (el["from_y"] + tip) / 2, 2 * lg["inner_x"], tip - el["from_y"]), 0.0, el["top_z"])
    add("end_links", g, "steel_brushed", bevel=el["bevel"], polished_bevel=True)
    zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]

    def place(s, sy):
        """Rigid placement of a link centred at distance s along the bracelet: straight to bend_y, then rolled back over radius R."""
        over = s - br["bend_y"]
        if over <= 0:
            return Matrix.Translation((0, sy * s, zm))
        a_ = over / R
        return Matrix.Translation((0, sy * (br["bend_y"] + R * math.sin(a_)), zm - R * (1 - math.cos(a_)))) @ Matrix.Rotation(-sy * a_, 4, "X")

    groups, back = {}, Geo()
    rows = 0
    for sy in (1, -1):
        y0 = tip + br["gap"]
        while y0 < br["end_y"] - 0.5:  # backing plate per row, under every column
            y1 = min(y0 + br["pitch"], br["end_y"])
            ym = (y0 + y1) / 2
            back.prism(rect(0, 0, 2 * (hw_at(ym) - 0.3), y1 - y0), ds * br["backing_z"][0] - zm, ds * br["backing_z"][1] - zm, place(ym, sy))
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
                    for sx in ((1, -1) if f0 else (1,)):
                        cx = sx * (x0 + x1) / 2 if f0 else 0
                        w = (x1 - x0) if f0 else 2 * x1
                        g.prism(rect(cx, 0, w, b_ - a_), ds * br["z0"] - zm, ds * br["z1"] - zm, place(ym, sy))
                y0 += br["pitch"]
    for mat, g in groups.items():
        add("bracelet_links_" + mat.split("_")[1], g, mat, bevel=br["bevel"], polished_bevel=mat != "steel_polished")
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    near = sorted(p[2] - p[1] for y, p in sil.items() if 22 <= abs(y) <= 24)
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "bracelet_next_to_case": round(near[len(near) // 2], 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "bracelet_rows": rows,
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
