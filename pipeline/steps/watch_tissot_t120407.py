"""watch_tissot_t120407: build the Tissot T120.407.17.041.00 (Seastar 1000 Powermatic 80, 43 mm, blue gradient dial, black
ceramic insert, black rubber strap) as a flat-backed front relief.

Params: spec (config/watches/tissot-t120.407.17.041.00.json). Same frame, pose, 2.5D depth scale, materials and curl as
watch_tissot_t120607 (bezel, indices, crown) and watch_bulova_96b431 (rubber strap). Parts from the official render: a polished
inner bezel lip, a black ceramic insert with the traced silver prints as raised inlays, a steel bezel ring with a coin edge;
applied indices with a polished frame and lume (round dots, a triangle at 12, bars at 3 and 9, a short bar at 6), placed about
the dial centre; broad baton hour and minute hands with lume panels and pointed tips, their tails below the hub as one traced
plate, a polished seconds needle with a lume dot in a ring and a T-shaped counterweight; a fluted crown in one crown guard;
brushed lugs from the silhouette; the rubber strap with the house curl, the render's taper and the strap photo map. Maps from
pipeline/tissot_t120407_dial.py; rebuild with --force after regenerating them (they are not part of the stage fingerprint).
"""
import json
import math

import bpy
import numpy as np
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rot
from pipeline.steps.watch_tissot_t120607 import inset


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    coll = bpy.data.collections.new("WATCH | %s front relief" % cfg["model"])
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    maps = {}
    for key, pm in cfg["photo_maps"].items():  # dial and strap
        mats[key] = photo_material(key, ROOT / pm["image"], pm["roughness"])
        maps[key] = json.loads((ROOT / pm["image"]).with_suffix(".json").read_text())
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
    H = maps["dial"]["half_size_mm"]
    dial_uv = lambda x, y, z: (0.5 + x / (2 * H), 0.5 + y / (2 * H))  # planar about the pivot

    def add(name, geo, mat, bevel=None, polished_bevel=False, uv_of=None, smooth=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured:  # planar UV in mm / tile, lines along the 12-6 axis (model Y)
            uv, tile = me.uv_layers.new(name="UVMap"), textured[mat]["tile_mm"]
            for loop in me.loops:
                x, y, _ = me.vertices[loop.vertex_index].co
                uv.data[loop.index].uv = (y / tile, -x / tile)
        if mat in maps:
            f = uv_of or dial_uv
            uv = me.uv_layers.new(name="UVMap")
            for loop in me.loops:
                uv.data[loop.index].uv = f(*me.vertices[loop.vertex_index].co)
        if bevel:
            if polished_bevel:
                me.materials.append(mats["steel_polished"])
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            if polished_bevel:
                m.material = 1
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        elif smooth:
            for poly in me.polygons:
                poly.use_smooth = True
        if not name.startswith("strap"):
            o.scale = (1, 1, ds)
        return o

    circle = lambda r, n=192, cx=0.0, cy=0.0: [(cx + r * math.sin(2 * math.pi * k / n), cy + r * math.cos(2 * math.pi * k / n)) for k in range(n)]
    bx, by = tr["dial_centre_mm"]
    rg = tr["bezel_rings_mm"]
    centred = Matrix.Translation((bx, by, 0))

    # ---- case under the bezel, crystal ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192, m=centred), "steel_polished")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (rg["lip_in"], cr["z0"]), (rg["lip_in"], cr["z1"]), (0, cr["z1"])], segs=192, m=centred), "crystal")

    # ---- bezel: polished inner lip, black ceramic insert with silver prints, steel ring with a coin edge ----
    bz = cfg["bezel"]
    ri, ro = rg["insert_in"], rg["insert_out"]
    add("bezel_lip", Geo().lathe([(rg["lip_in"], bz["lip_z"]), (ri, bz["insert_z"]), (ri, bz["z0"]), (rg["lip_in"], bz["z0"])], segs=192, m=centred),
        "steel_polished")
    add("insert", Geo().lathe([(ri, bz["z0"]), (ro, bz["z0"]), (ro, bz["insert_z"]), (ri, bz["insert_z"])], segs=240, m=centred), "insert_ceramic")
    add("insert_prints", plate(tr["insert_prints"], bz["insert_z"] - 0.05, bz["insert_z"] + bz["print_raise"], P + "insert_prints"), "print_silver")
    pip = tr["insert_pip_mm"]
    add("insert_pip", Geo().lathe([(0, bz["insert_z"]), (pip["radius"], bz["insert_z"]), (pip["radius"], bz["insert_z"] + bz["print_raise"] + 0.05),
                                   (0, bz["insert_z"] + bz["print_raise"] + 0.05)], segs=48, m=Matrix.Translation((*pip["centre"], 0))), "lume")
    n, depth, tip_r = tr["bezel_notches"]["count"], bz["scallop_depth"], rg["rim_out"]
    notch = bz["notch_fraction"]
    u = lambda f: 1.0 if abs(2 * f - 1) < notch else 0.0  # square teeth
    star = [(lambda a, f: (bx + (tip_r - depth * u(f)) * math.sin(a), by + (tip_r - depth * u(f)) * math.cos(a)))(2 * math.pi * (k + 0.5) / (12 * n), (k % 12 + 0.5) / 12)
            for k in range(12 * n)]
    add("bezel_rim", Geo().lathe([(ro - 0.05, bz["z0"]), (tip_r - depth, bz["z0"]), (tip_r - depth, bz["rim_z"]), (ro - 0.05, bz["rim_z"])], segs=384, m=centred),
        "steel_polished", bevel=bz["rim_bevel"])
    add("bezel_coin_edge", plate([{"outer": star, "holes": [circle(tip_r - depth - 0.05, 384, bx, by)]}], bz["z0"] + bz["scallop_z"], bz["rim_z"] - 0.1,
                                 P + "bezel_coin_edge"), "steel_polished", bevel=bz["rim_bevel"])

    # ---- dial + flange, photo map ----
    d = cfg["dial"]
    me = Geo().lathe([(0, d["z"]), (rg["dial_out"], d["z"]), (rg["lip_in"] + 0.05, d["rehaut_z"])], segs=192, m=centred).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    add("dial", me, "dial")

    # ---- applied indices about the dial centre: polished frame, recessed lume ----
    ix, ti = cfg["indices"], tr["indices"]
    fw, z0, z1, turn = ti["frame_mm"], d["z"], d["z"] + ix["height"], ti["turn_deg"]
    shapes, lume = [], Geo()
    lr = ti["dot_lume_r_mm"]
    for x, y in ti["dots_mm"]:
        shapes.append({"outer": [list(p) for p in circle(lr + fw, 64, x, y)], "holes": [[list(p) for p in circle(lr, 64, x, y)][::-1]]})
        lume.prism(circle(lr, 64, x, y), z0, z1 - ix["lume_recess"])
    polys = [(0, [(-ti["triangle_half_mm"], ti["triangle_r_mm"][1]), (0, ti["triangle_r_mm"][0]), (ti["triangle_half_mm"], ti["triangle_r_mm"][1])])]
    for hr, rk, wk in ((3, "bar_r_mm", "bar_half_mm"), (9, "bar_r_mm", "bar_half_mm"), (6, "bar6_r_mm", "bar6_half_mm")):
        (r0, r1), w = ti[rk], ti[wk]
        polys.append((hr, [(-w, r0), (w, r0), (w, r1), (-w, r1)]))
    for hr, lp in polys:
        outer = [(bx + p[0], by + p[1]) for p in (rot(x, y, hr * 30 + turn) for x, y in inset(lp, -fw))]
        inner = [(bx + p[0], by + p[1]) for p in (rot(x, y, hr * 30 + turn) for x, y in lp)]
        shapes.append({"outer": [list(p) for p in outer], "holes": [[list(p) for p in inner]]})
        lume.prism(inner, z0, z1 - ix["lume_recess"])
    add("indices", plate(shapes, z0, z1, P + "indices"), "steel_polished")
    add("index_lume", lume, "lume")

    # ---- hands at the render's time ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]

    def hand(name, poly, deg, z, mat, h=th, bevel=None):
        add(name, Geo().prism([rot(x, y, deg) for x, y in poly], z, z + h), mat, bevel=bevel)

    for name in ("hour", "minute"):  # broad baton, pointed tip, lume panel inside a polished frame
        h, z = t[name], hs["z"][name]
        deg, L, sh, hw = h["angle_deg"], h["tip"], h["shoulder"], h["half"]
        hand("hand_" + name, [(-hw, 0.0), (hw, 0.0), (hw, sh), (0, L), (-hw, sh)], deg, z, "steel_polished", bevel=0.03)
        l0, l1, lw = h["lume"]
        hand("hand_%s_lume" % name, [(-lw, l0), (lw, l0), (lw, l1 - lw * (L - sh) / hw), (0, l1), (-lw, l1 - lw * (L - sh) / hw)], deg, z + th, "lume", hs["lume"])
    zt = hs["z"]["hour"]
    add("hand_tails", Geo().prism([tuple(p) for p in tr["tails_mm"]], zt, zt + th), "steel_polished", bevel=0.03)

    h, z = t["seconds"], hs["z"]["seconds"]
    deg, nw = h["angle_deg"], h["half"]
    hand("hand_seconds", [(-nw, 0.0), (nw, 0.0), (nw, h["tip"]), (-nw, h["tip"])], deg, z, "steel_polished", bevel=0.01)
    hand("hand_seconds_counterweight", [(x, y) for x, y in h["counterweight"]], deg + 180, z, "steel_polished", bevel=0.02)
    m = Matrix.Translation((*rot(0, h["ring_r"], deg), 0))
    dl, dr = h["ring"]
    add("hand_seconds_ring", Geo().lathe([(0, z), (dr, z), (dr, z + th), (0, z + th)], segs=48, m=m), "steel_polished", bevel=0.02)
    add("hand_seconds_lume", Geo().lathe([(0, z + th), (dl, z + th), (dl, z + th + hs["lume"]), (0, z + th + hs["lume"])], segs=48, m=m), "lume")
    r0, r1 = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (r0, d["z"]), (r0, z), (0, z)], segs=48), "steel_polished", smooth=True)
    zc = z + th
    add("hub_cap", Geo().lathe([(0, zc), (r1, zc), (r1, zc + 0.1), (r1 * 0.6, zc + 0.18), (0, zc + 0.18)], segs=48), "steel_polished", smooth=True)

    # ---- crown: collar and fluted cylinder on the 3 o'clock axis, one crown guard ----
    cw_ = cfg["crown"]
    cb = tr["crown_box"]["x0_y0_x1_y1_mm"]
    teeth, R0 = tr["crown_teeth"], (cb[1] - cb[3]) / 2
    star = [((R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.cos(math.pi * i / teeth),
             (R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.sin(math.pi * i / teeth)) for i in range(teeth * 2)]
    m = Matrix(((0, -1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_4x4()  # local z along +x, local y up
    m.translation = (0.0, tr["crown_box"]["centre_mm"][1], cw_["z"])
    add("crown_collar", Geo().lathe([(0, cw_["collar"][0]), (cw_["collar_r"], cw_["collar"][0]), (cw_["collar_r"], cb[0] + 0.3), (0, cb[0] + 0.3)],
                                    segs=48, m=m), "steel_polished", smooth=True)
    add("crown", Geo().prism(star, cb[0], cb[2] - cw_["end"], m), "steel_polished", bevel=0.12)
    add("crown_end", Geo().lathe([(0, cb[2] - cw_["end"]), (R0 - 0.1, cb[2] - cw_["end"]), (R0 - 0.4, cb[2] - cw_["end"] * 0.3), (R0 - 0.9, cb[2]), (0, cb[2])],
                                 segs=64, m=m), "steel_polished", smooth=True)
    add("crown_guard", Geo().prism([tuple(p) for p in tr["crown_guard_mm"]], 0.0, cfg["crown_guard"]["top_z"]), "steel_polished",
        bevel=cfg["crown_guard"]["bevel"])

    # ---- case flanks and lugs from the traced silhouette (left edge, top/bottom averaged): brushed top, polished chamfer ----
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}

    def half(y):  # left edge only: the crown and guard widen the right side
        ys = [sil[k_] for k_ in (round(y, 2), round(-y, 2)) if k_ in sil]
        return sum(-p[1] for p in ys) / len(ys)

    lg = cfg["lug"]
    tip = tr["lug_tip_mm"]["mean"]
    xi = tr["lug"]["inner_x_mm"]
    steps = [lg["from_y"] + k_ * 0.25 for k_ in range(int((tip - lg["from_y"]) / 0.25) + 1)]
    outline = [(xi, lg["from_y"])] + [(half(y) - lg["inside"], y) for y in steps] + [(xi, tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * (abs(y) - lg["from_y"]) / (tip - lg["from_y"])
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

    # ---- rubber strap: house curl from the lug tips, the render's taper, the strap rows (tips aligned) ----
    st, sm = cfg["strap"], maps["strap"]
    zm, R = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"]
    bend_y = tip + st["bend_after_tip"]
    end_y = bend_y + R * st["arc_over_radius"]
    hw0 = xi + st["side_extra"]
    taper = tr["strap"]["half_width_by_s_mm"]
    hw = lambda s: min(hw0, float(np.interp(s - tip, [q[0] for q in taper], [q[1] for q in taper])))
    box = curl(bend_y, R, zm)
    g = Geo()
    for sy in (1, -1):
        box(g, -hw0, hw0, st["from_y"], end_y, ds * st["z0"], ds * st["z1"], sy)
    s_of = lambda y, z: abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
    g.v = [(x * hw(s_of(y, z)) / hw0, y, z) for x, y, z in g.v]  # taper: every vertex moved in to the width at its strap length
    tips_photo = [tr["lug_tip_mm"]["top"], tr["lug_tip_mm"]["bottom"]]
    rows_h = sm["size_px"][1]

    def strap_uv(x, y, z):
        top_side = y > 0
        side = sm["top"] if top_side else sm["bottom"]
        s = s_of(y, z)
        sp = s - tip + tips_photo[0 if top_side else 1]
        i = (sp - side["first_s_mm"]) * sm["rows_per_mm"]
        i = min(max(i, 0.0), 2 * side["rows"] - 1.0)
        if i > side["rows"] - 1:  # past the render's edge (rolled under, out of the front view): fold back
            i = 2 * (side["rows"] - 1) - i
        row = i + (0 if top_side else sm["top"]["rows"])
        u = min(max((x / hw(s) + 1) / 2, st["uv_inset"]), 1 - st["uv_inset"])  # side walls take the strap's own edge pixels
        return (u, 1 - (row + 0.5) / rows_h)
    add("strap", g, "strap", uv_of=strap_uv, smooth=True)

    # ---- checks against the anchors ----
    out = {"case_width": round(2 * rg["rim_out"], 3), "lug_width": round(2 * xi, 3), "lug_to_lug": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.5, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "strap_end_y_mm": round(end_y, 2), "strap_half_width_at_end_mm": round(hw(end_y), 2),
            "insert_prints": len(tr["insert_prints"]), "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
