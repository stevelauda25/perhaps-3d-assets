"""watch_tissot_t120410: build the Tissot T120.410.11.051.00 (Seastar 1000 Quartz, 40 mm, black dial, black insert, steel
bracelet) as a flat-backed front relief.

Params: spec (config/watches/tissot-t120.410.11.051.00.json). Same frame, pose, 2.5D depth scale, materials and curl as
watch_tissot_t120407 (head) and watch_tissot_t120607 (bracelet). Parts from the official render: a polished inner bezel lip, a
black insert with the traced white prints as raised inlays, a steel bezel ring with a coin edge; applied indices with a
polished frame and lume (round dots, a triangle at 12, bars at 3 and 9) placed about the dial centre, and a polished date
frame at 6; baton hour and minute hands with lume panels and pointed tips, their tails below the hub as one traced plate, a
polished seconds needle with a lume dot in a ring and a T-shaped counterweight; a fluted crown in one crown guard; brushed
lugs from the silhouette; a three-column bracelet (brushed outer links, polished centre links of a shorter pitch) with the
house curl. The dial (print, date, grey flange) is the photo map from pipeline/tissot_t120410_dial.py; rebuild with --force
after regenerating it (it is not part of the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot
from pipeline.steps.watch_tissot_t120607 import inset


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    coll = bpy.data.collections.new("WATCH | %s front relief" % cfg["model"])
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    maps = {}
    for key, pm in cfg["photo_maps"].items():  # dial
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
        if not name.startswith("bracelet"):
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
    add("insert_prints", plate(tr["insert_prints"], bz["insert_z"] - 0.05, bz["insert_z"] + bz["print_raise"], P + "insert_prints"), "print_white")
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
    for hr, rk, wk in ((3, "bar_r_mm", "bar_half_mm"), (9, "bar_r_mm", "bar_half_mm")):
        (r0, r1), w = ti[rk], ti[wk]
        polys.append((hr, [(-w, r0), (w, r0), (w, r1), (-w, r1)]))
    for hr, lp in polys:
        outer = [(bx + p[0], by + p[1]) for p in (rot(x, y, hr * 30 + turn) for x, y in inset(lp, -fw))]
        inner = [(bx + p[0], by + p[1]) for p in (rot(x, y, hr * 30 + turn) for x, y in lp)]
        shapes.append({"outer": [list(p) for p in outer], "holes": [[list(p) for p in inner]]})
        lume.prism(inner, z0, z1 - ix["lume_recess"])
    add("indices", plate(shapes, z0, z1, P + "indices"), "steel_polished")
    add("index_lume", lume, "lume")
    fo, fi = tr["date_frame_mm"]["outer"], tr["date_frame_mm"]["inner"]
    sq = lambda b_: [(b_[0], b_[3]), (b_[2], b_[3]), (b_[2], b_[1]), (b_[0], b_[1])]
    add("date_frame", plate([{"outer": sq(fo), "holes": [sq(fi)[::-1]]}], z0, z0 + ix["date_frame_height"], P + "date_frame"), "steel_polished",
        bevel=0.08)

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
    xi = tr["end_link_half_mm"]
    steps = [lg["from_y"] + k_ * 0.25 for k_ in range(int((tip - lg["from_y"]) / 0.25) + 1)]
    outline = [(xi, lg["from_y"])] + [(half(y) - lg["inside"], y) for y in steps] + [(xi, tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * (abs(y) - lg["from_y"]) / (tip - lg["from_y"])
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

    # ---- three-column bracelet: brushed outer links, polished centre links, centre joints `shift` nearer the case ----
    br, el = cfg["bracelet"], cfg["end_link"]
    ch, shift, gap = tr["bracelet_centre_half_mm"], tr["bracelet_centre_joint_shift_mm"], br["gap"]
    sil_max = min(max(sil), -min(sil)) - 0.25
    hw_at = lambda y: min(half(round(min(max(y, tip + 1.0), sil_max) * 4) / 4), xi)
    end, end_c = Geo(), Geo()
    for sy in (1, -1):
        M = Matrix.Translation((0, sy * (el["from_y"] + tip) / 2, 0))
        for sx in (1, -1):
            end.prism(rect(sx * (ch + gap + xi) / 2, 0, xi - ch - gap, tip - el["from_y"]), 0.0, el["top_z"], M)
        y1 = tip - shift - gap
        end_c.prism(rect(0, sy * (el["from_y"] + y1) / 2, 2 * ch, y1 - el["from_y"]), 0.0, el["top_z"] + br["centre_raise"])
    add("end_links", end, "steel_brushed", bevel=el["bevel"], polished_bevel=True)
    add("end_link_centre", end_c, "steel_polished", bevel=el["bevel"])

    zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]
    end_y = tip + br["bend_after_tip"] + R * br["arc_over_radius"]
    bent_box = curl(tip + br["bend_after_tip"], R, zm)
    pitches = tr["bracelet_pitch_mm"]
    links, centre, back = Geo(), Geo(), Geo()
    rows = 0
    za, zb = ds * br["z0"], ds * br["z1"]
    for sy in (1, -1):
        for kind, start in (("outer", tip), ("centre", tip - shift)):
            y0 = start
            pitch = pitches[kind]
            while y0 < end_y - 0.5:
                y1 = min(y0 + pitch - gap, end_y)
                hw_ = hw_at((y0 + y1) / 2)
                if kind == "outer":
                    for sx in (1, -1):
                        x0, x1 = sorted((sx * (ch + gap), sx * hw_))
                        bent_box(links, x0, x1, y0, y1, za, zb, sy)
                    bent_box(back, -(hw_ - 0.3), hw_ - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                else:
                    bent_box(centre, -ch, ch, y0, y1, za, zb + ds * br["centre_raise"], sy)
                y0 = y1 + gap
    add("bracelet_links", links, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_centre", centre, "steel_polished", bevel=br["bevel"])
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"case_width": round(2 * rg["rim_out"], 3), "end_link_width": round(2 * xi, 3), "lug_to_lug": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.5, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "bracelet_end_y_mm": round(end_y, 2), "bracelet_rows": rows,
            "insert_prints": len(tr["insert_prints"]), "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
