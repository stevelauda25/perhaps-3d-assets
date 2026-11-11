"""watch_tissot_t1204102205101: build the Tissot T120.410.22.051.01 (Seastar 1000 40 mm quartz, black dial, rose gold PVD
bezel and centre links) as a flat-backed front relief.

Params: spec (config/watches/tissot-t120.410.22.051.01.json). Same frame, pose, 2.5D depth scale, materials and bracelet curl
as watch_tissot_t120607. Parts from the photo: a polished inner lip, a black insert with the traced rose gold prints as raised
inlays, a rose gold bezel ring with a coin edge; applied indices with a rose gold frame and lume (round dots, a triangle at 12,
bars at 3 and 9); rose gold baton hour and minute hands with lume and blunt points, a rose gold seconds needle with a lume dot
and a counterweight cross bar; a fluted steel crown between two crown guards; brushed steel lugs and a three-column bracelet
(steel outer links, rose gold centre links). The dial (sunray, prints, date, rehaut minute track) is the photo map from
pipeline/tissot_t1204102205101_dial.py. Rebuild with --force after regenerating the map (it is not part of the stage
fingerprint).
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
    dm = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Tissot T120.410.22.051.01 front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    d = cfg["dial"]
    mats["dial"] = photo_material("dial_photo", ROOT / cfg["dial_map"], d["roughness"])
    textured = cfg.get("brushed_textures", {})
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

    def add(name, geo, mat, bevel=None, bevel_mat=None, smooth=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured:  # planar UV in mm / tile, lines along the bracelet (model Y)
            uv, tile = me.uv_layers.new(name="UVMap"), textured[mat]["tile_mm"]
            for loop in me.loops:
                x, y, _ = me.vertices[loop.vertex_index].co
                uv.data[loop.index].uv = (y / tile, -x / tile)
        if bevel:
            if bevel_mat:
                me.materials.append(mats[bevel_mat])
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            if bevel_mat:
                m.material = 1
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if not name.startswith("bracelet"):
            o.scale = (1, 1, ds)
        return o

    circle = lambda r, n=192, cx=0.0, cy=0.0: [(cx + r * math.sin(2 * math.pi * k / n), cy + r * math.cos(2 * math.pi * k / n)) for k in range(n)]
    bx, by = tr["bezel_offset_mm"]
    rg = tr["bezel_rings_mm"]

    # ---- case under the bezel, crystal ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), "steel_polished")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- bezel: polished inner lip, black insert with rose gold prints, rose gold ring with a coin edge ----
    bz = cfg["bezel"]
    centred = Matrix.Translation((bx, by, 0))
    ri, ro = rg["insert_in"], rg["insert_out"]
    add("bezel_lip", Geo().lathe([(rg["lip_in"], bz["lip_z"]), (ri, bz["insert_z"]), (ri, bz["z0"]), (rg["lip_in"], bz["z0"])], segs=192, m=centred),
        "steel_polished")
    add("insert", Geo().lathe([(ri, bz["z0"]), (ro, bz["z0"]), (ro, bz["insert_z"]), (ri, bz["insert_z"])], segs=240, m=centred), "insert_black")
    add("insert_prints", plate(tr["insert_prints"], bz["insert_z"] - 0.05, bz["insert_z"] + bz["print_raise"], P + "insert_prints"), "print_gold")
    n, depth, tip_r = tr["bezel_notches"]["count"], bz["scallop_depth"], rg["rim_out"]
    notch = bz["notch_fraction"]
    u = lambda f: max(0.0, 1 - ((2 * f - 1) / notch) ** 2) ** 0.5
    star = [(lambda a, f: (bx + (tip_r - depth * u(f)) * math.sin(a), by + (tip_r - depth * u(f)) * math.cos(a)))(2 * math.pi * k / (12 * n), (k % 12) / 12)
            for k in range(12 * n)]
    add("bezel_rim", Geo().lathe([(ro - 0.05, bz["z0"]), (tip_r - depth, bz["z0"]), (tip_r - depth, bz["rim_z"]), (ro - 0.05, bz["rim_z"])], segs=384, m=centred),
        "gold_polished", bevel=bz["rim_bevel"])
    add("bezel_coin_edge", plate([{"outer": star, "holes": [circle(tip_r - depth - 0.05, 384, bx, by)]}], bz["z0"] + bz["scallop_z"], bz["rim_z"] - 0.1,
                                 P + "bezel_coin_edge"), "gold_polished", bevel=bz["rim_bevel"])

    # ---- dial + rehaut, photo map on a planar UV ----
    me = Geo().lathe([(0, d["z"]), (d["flat_r"], d["z"]), (d["rehaut_r"], d["rehaut_z"])], segs=192).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    uv = me.uv_layers.new(name="UVMap")
    H = dm["half_size_mm"]
    for loop in me.loops:
        x, y, _ = me.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
    add("dial", me, "dial")

    # ---- applied indices: rose gold frame, recessed lume; round dots, triangle at 12, bars at 3 and 9 ----
    ix, ti = cfg["indices"], tr["indices"]
    fw, z0, z1, turn = ti["frame_mm"], d["z"], d["z"] + ix["height"], ti["turn_deg"]
    shapes, lume = [], Geo()
    lr = ti["dot_lume_r_mm"]
    for x, y in ti["dots_mm"]:
        shapes.append({"outer": [list(p) for p in circle(lr + fw, 64, x, y)], "holes": [[list(p) for p in circle(lr, 64, x, y)][::-1]]})
        lume.prism(circle(lr, 64, x, y), z0, z1 - ix["lume_recess"])
    polys = [(0, [(-ti["triangle_half_mm"], ti["triangle_r_mm"][1]), (0, ti["triangle_r_mm"][0]), (ti["triangle_half_mm"], ti["triangle_r_mm"][1])])]
    for hr in (3, 9):
        (r0, r1), w = ti["bar_r_mm"], ti["bar_half_mm"]
        polys.append((hr, [(-w, r0), (w, r0), (w, r1), (-w, r1)]))
    for hr, lp in polys:
        outer = [rot(x, y, hr * 30 + turn) for x, y in inset(lp, -fw)]
        inner = [rot(x, y, hr * 30 + turn) for x, y in lp]
        shapes.append({"outer": [list(p) for p in outer], "holes": [[list(p) for p in inner]]})
        lume.prism(inner, z0, z1 - ix["lume_recess"])
    add("indices", plate(shapes, z0, z1, P + "indices"), "gold_polished")
    add("index_lume", lume, "lume")

    # ---- hands at the photo's time, rose gold ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]

    def hand(name, poly, deg, z, mat="gold_polished", h=th):
        add(name, Geo().prism([rot(x, y, deg) for x, y in poly], z, z + h), mat, bevel=0.02 if mat == "gold_polished" else None)

    def baton(name, h, z, lume_cut):
        """Baton with a blunt point, lume inlay on top and a stepped tail behind the hub."""
        deg, L, sh, hw = h["angle_deg"], h["tip"], h["shoulder"], h["half"]
        r0, r1, w0, w1 = h["tail"]
        hand(name, [(-w1, -r1), (w1, -r1), (w1, -r0), (w0, -r0), (hw, 0.0), (hw, sh), (0, L), (-hw, sh), (-hw, 0.0), (-w0, -r0), (-w1, -r0)], deg, z)
        l0, l1, lw = h["lume"]
        s1 = sh - (hw - lw) * lume_cut
        hand(name + "_lume", [(-lw, l0), (lw, l0), (lw, s1), (0, l1), (-lw, s1)], deg, z + th, "lume", 0.04)

    baton("hand_hour", t["hour"], hs["z"]["hour"], 0.6)
    baton("hand_minute", t["minute"], hs["z"]["minute"], 0.4)

    # seconds: needle with a pointed tip, lume dot in a ring at the index radius, counterweight shaft and cross bar
    h, z = t["seconds"], hs["z"]["seconds"]
    deg, nw = h["angle_deg"], h["half"]
    s0, sw = h["shaft"]
    b0, b1, bw = h["bar"]
    hand("hand_seconds", [(-nw, 0.0), (nw, 0.0), (nw, h["tip"] - 0.5), (0, h["tip"]), (-nw, h["tip"] - 0.5)], deg, z)
    hand("hand_seconds_tail", [(-bw, -b1), (bw, -b1), (bw, -b0), (sw, -b0), (sw, 0.3), (-sw, 0.3), (-sw, -b0), (-bw, -b0)], deg, z)
    dl, dfr = h["dot"]
    m = Matrix.Translation((*rot(0, h["dot_r"], deg), 0))
    add("hand_seconds_ring", Geo().lathe([(0, z), (dfr, z), (dfr, z + th), (0, z + th)], segs=48, m=m), "gold_polished", bevel=0.02)
    add("hand_seconds_lume", Geo().lathe([(0, z + th), (dl, z + th), (dl, z + th + 0.04), (0, z + th + 0.04)], segs=48, m=m), "lume")
    hub_r, cap_r = tr["hub_radius_mm"]
    add("hub_boss", Geo().lathe([(0, hs["z"]["minute"]), (hub_r, hs["z"]["minute"]), (hub_r, hs["z"]["minute"] + th), (0, hs["z"]["minute"] + th)], segs=48),
        "gold_polished", bevel=0.02)
    add("hub_post", Geo().lathe([(0, d["z"]), (cap_r * 1.4, d["z"]), (cap_r * 1.4, z), (0, z)], segs=48), "gold_polished")
    zc = z + th
    add("hub_cap", Geo().lathe([(0, zc), (cap_r, zc), (cap_r, zc + 0.1), (cap_r * 0.6, zc + 0.18), (0, zc + 0.18)], segs=48), "gold_polished")

    # ---- crown: smooth collar and fluted cylinder on a radial axis at the traced angle (3 o'clock), two crown guards ----
    cw_ = cfg["crown"]
    a = math.radians(math.degrees(math.atan2(*tr["crown_box"]["centre_mm"])) % 360)
    teeth = tr["crown_teeth"]
    star = [((cw_["radius"] if i % 2 == 0 else cw_["radius"] - cw_["flute_depth"]) * math.cos(math.pi * i / teeth),
             (cw_["radius"] if i % 2 == 0 else cw_["radius"] - cw_["flute_depth"]) * math.sin(math.pi * i / teeth)) for i in range(teeth * 2)]
    u_, dr_ = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
    m = Matrix((u_, (0, 0, 1), dr_)).transposed().to_4x4()
    m.translation = (0, 0, cw_["z"])
    add("crown_collar", Geo().lathe([(0, cw_["collar"][0]), (cw_["collar_r"], cw_["collar"][0]), (cw_["collar_r"], cw_["collar"][1]),
                                     (0, cw_["collar"][1])], segs=48, m=m), "steel_polished", bevel=0.1)
    add("crown", Geo().prism(star, cw_["collar"][1], cw_["r_to"], m), "steel_polished", bevel=0.15)
    g = Geo()
    for gp in tr["crown_guards_mm"]:
        g.prism([tuple(p) for p in gp], 0.0, cfg["crown_guard"]["top_z"])
    add("crown_guards", g, "steel_brushed", bevel=cfg["crown_guard"]["bevel"], bevel_mat="steel_polished")

    # ---- case flanks and lugs from the traced silhouette (left edge, top/bottom averaged): brushed top, polished chamfer ----
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}

    def half(y):  # left edge only: the crown and guards widen the right side at 3 o'clock
        ys = [sil[k_] for k_ in (round(y, 2), round(-y, 2)) if k_ in sil]
        return sum(-p[1] for p in ys) / len(ys)

    lg = cfg["lug"]
    tip = tr["lug_tip_mm"]["mean"]
    steps = [lg["from_y"] + k_ * 0.25 for k_ in range(int((tip - lg["from_y"]) / 0.25) + 1)]
    outline = [(lg["inner_x"], lg["from_y"])] + [(half(y), y) for y in steps] + [(lg["inner_x"], tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * (abs(y) - lg["from_y"]) / (tip - lg["from_y"])
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], bevel_mat="steel_polished")

    # ---- three-column bracelet: brushed steel outer links, rose gold centre links (joints `shift` nearer the case) ----
    br, el = cfg["bracelet"], cfg["end_link"]
    ch, shift, gap = tr["bracelet_centre_half_mm"], tr["bracelet_centre_joint_shift_mm"], br["gap"]
    sil_max = min(max(sil), -min(sil)) - 0.25
    hw_at = lambda y: min(half(round(min(max(y, tip + 1.0), sil_max) * 4) / 4), el["half_width"])
    end_o, end_c = Geo(), Geo()
    for sy in (1, -1):
        M = Matrix.Translation((0, sy * (el["from_y"] + tip) / 2, 0))
        for sx in (1, -1):
            end_o.prism(rect(sx * (ch + gap + el["half_width"]) / 2, 0, el["half_width"] - ch - gap, tip - el["from_y"]), 0.0, el["top_z"], M)
        y1 = tip - shift - gap
        end_c.prism(rect(0, sy * (el["from_y"] + y1) / 2, 2 * ch, y1 - el["from_y"]), 0.0, el["top_z"])
    add("end_links", end_o, "steel_brushed", bevel=el["bevel"], bevel_mat="steel_polished")
    add("end_links_centre", end_c, "gold_brushed", bevel=el["bevel"], bevel_mat="gold_polished")

    zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]
    bent_box = curl(tip + br.get("bend_after_tip", 0.0), R, zm)
    pitches = tr["bracelet_pitch_mm"]
    outer, centre, back = Geo(), Geo(), Geo()
    rows = 0
    za, zb = ds * br["z0"], ds * br["z1"]
    for sy in (1, -1):
        for kind, start in (("outer", tip), ("centre", tip - shift)):
            y0 = start
            pitch = pitches[kind]
            while y0 < br["end_y"] - 0.5:
                y1 = min(y0 + pitch - gap, br["end_y"])
                hw_ = hw_at((y0 + y1) / 2)
                if kind == "outer":
                    for sx in (1, -1):
                        x0, x1 = sorted((sx * (ch + gap), sx * hw_))
                        bent_box(outer, x0, x1, y0, y1, za, zb, sy)
                    bent_box(back, -(hw_ - 0.3), hw_ - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                else:
                    bent_box(centre, -ch, ch, y0, y1, za, zb + ds * br["centre_raise"], sy)
                y0 = y1 + gap
    add("bracelet_links", outer, "steel_brushed", bevel=br["bevel"], bevel_mat="steel_polished")
    add("bracelet_centre_links", centre, "gold_brushed", bevel=br["bevel"], bevel_mat="gold_polished")
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(half(k_ * 0.25) for k_ in range(13)), 3), "lug_to_lug": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "bracelet_rows": rows, "insert_prints": len(tr["insert_prints"]),
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
