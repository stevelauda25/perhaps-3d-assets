"""watch_bulova_98a329: build the Bulova 98A329 (Lunar Pilot Timascus, 43.5 mm chronograph, blue Timascus dial, steel
bracelet) as a flat-backed front relief.

Params: spec (config/watches/bulova-98a329.json). Same frame, pose, 2.5D depth scale, materials and bracelet curl as
watch_hamilton_h82405130. Parts from the photo: a blue anodised bezel ring around a black groove; applied white bar indices in
a polished frame (wide at 3 6 9, long at 12) and applied white numerals traced from the photo; white lume batons in a polished
frame for the hour and minute; a white chrono needle with a lozenge; black subdial needles with black hubs; a fluted crown at 3,
two blue paddle pushers at 2 and 4; a cushion case and lug horns as one slab from the silhouette and a three-column bracelet.
The dial, subdials, minute track flange and tachymeter ring are the photo map from pipeline/bulova_98a329_dial.py. Rebuild with
--force after regenerating the map (it is not part of the stage fingerprint).
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

    def add(name, geo, mat, bevel=None, polished_bevel=False, smooth=None, uv_of=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured and not uv_of:  # planar UV in mm / tile, lines along the bracelet (model Y)
            tile = textured[mat]["tile_mm"]
            uv_of = lambda x, y, z: (y / tile, -x / tile)
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

    bx, by = tr["bezel_offset_mm"]
    rg = tr["bezel_rings_mm"]
    centred = Matrix.Translation((bx, by, 0))

    # ---- case under the bezel, crystal ----
    add("case", Geo().lathe([tuple(p) for p in cfg["case"]["profile_rz"]], segs=192, m=centred), "steel_polished", smooth=True)
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192, m=centred), "crystal")

    # ---- blue anodised bezel ring (rounded top) and the black groove inside it ----
    bz = cfg["bezel"]
    gi, go, ro = rg["tach_out"], rg["groove_out"], rg["bezel_out"]
    add("bezel", Geo().lathe([(go, bz["z0"]), (ro, bz["z0"]), (ro, bz["outer_z"]), (bz["crown_r"], bz["top_z"]), (go + 0.25, bz["top_z"]),
                              (go, bz["inner_z"])], segs=240, m=centred), "bezel_blue", smooth=True)
    add("groove", Geo().lathe([(gi - 0.05, bz["z0"]), (go + 0.02, bz["z0"]), (go + 0.02, bz["groove_z"]), (gi - 0.05, bz["groove_z"])], segs=192, m=centred),
        "gasket_black")

    # ---- dial, minute track flange and tachymeter ring: one surface with the photo map on a planar UV about the hand pivot ----
    me = Geo().lathe([(0, d["z"]), (rg["dial_out"], d["z"]), (rg["flange_out"], d["flange_z"]), (rg["flange_out"] + 0.05, d["tach_z"]),
                      (gi, d["tach_z"])], segs=240, m=centred).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    H, (ox, oy) = dm["half_size_mm"], dm["centre_offset_mm"]
    add("dial", me, "dial", uv_of=lambda x, y, z: (0.5 + (x - ox) / (2 * H), 0.5 + (y - oy) / (2 * H)))

    # ---- applied indices: polished frame around white lume; numerals: white plates traced from the photo ----
    ix, ti = cfg["indices"], tr["indices"]
    k = tr["hand_outline_mm"]
    z0, z1 = d["z"], d["z"] + ix["height"]
    frames, lume = [], Geo()
    for hr in range(12):
        r0, r1, hw = ti["twelve_mm"] if hr == 0 else ti["wide_bar_mm"] if hr % 3 == 0 else ti["bar_mm"]
        outer = [rot(x, y, hr * 30) for x, y in rect(0, (r0 + r1) / 2, 2 * hw, r1 - r0)]
        inner = [rot(x, y, hr * 30) for x, y in rect(0, (r0 + r1) / 2, 2 * (hw - k), r1 - r0 - 2 * k)]
        frames.append({"outer": [list(p) for p in outer], "holes": [[list(p) for p in inner]]})
        lume.prism(inner, z0, z1 - ix["lume_recess"])
    add("indices", plate(frames, z0, z1, P + "indices"), "steel_polished")
    add("index_lume", lume, "lume")
    shapes = [sh for v in tr["numerals"].values() for sh in v]
    add("numerals", plate(shapes, z0, z0 + cfg["numerals"]["height"], P + "numerals"), "print_white")

    # ---- hands at the photo's time ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]

    def hand(name, poly, deg, z, mat, h=th, c=(0.0, 0.0)):
        add(name, Geo().prism([(lambda p: (p[0] + c[0], p[1] + c[1]))(rot(x, y, deg)) for x, y in poly], z, z + h), mat,
            bevel=0.02 if mat == "steel_polished" else None)

    for name in ("hour", "minute"):  # white lume baton in a polished frame, pointed tip
        h, z = t[name], hs["z"][name]
        L, (w0, w1), pt, deg = h["length_mm"], h["half_mm"], h["point_mm"], h["angle_deg"]
        body = [(-w0, 0.0), (w0, 0.0), (w1, L - pt), (0, L), (-w1, L - pt)]
        hand("hand_" + name, body, deg, z, "steel_polished")
        hand("hand_%s_lume" % name, [(-w0 + k, 0.6), (w0 - k, 0.6), (w1 - k, L - pt), (0, L - 2 * k), (-w1 + k, L - pt)], deg, z + th, "lume", 0.04)
    h = t["chrono"]  # white needle with a lozenge, thin pointer, tail widening to a rounded end
    L, deg, z = h["length_mm"], h["angle_deg"], hs["z"]["chrono"]
    nw, pw, (tl, tw) = h["half_mm"], h["pointer_half_mm"], h["tail_mm"]
    l0, lm, lw, l1 = h["lozenge_mm"]
    tail_end = [(tw * math.sin(a), -tl + tw - tw * math.cos(a)) for a in [math.pi / 2 - math.pi * i / 8 for i in range(9)]]
    needle = [(-nw, 0.0)] + [(-x, y) for x, y in tail_end] + [(nw, 0.0), (nw, l0), (lw, lm), (pw, l1), (pw * 0.7, L), (-pw * 0.7, L), (-pw, l1), (-lw, lm), (-nw, l0)]
    hand("hand_chrono", needle, deg, z, "print_white")
    hub_r, ring_r, pin_r = tr["hub_radius_mm"]
    zt = z + th
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, zt), (0, zt)], segs=64), "print_white")
    add("hub_ring", Geo().lathe([(0, zt), (ring_r, zt), (ring_r, zt + 0.08), (0, zt + 0.08)], segs=64), "steel_polished", bevel=0.02)
    add("hub_pin", Geo().lathe([(0, zt + 0.08), (pin_r, zt + 0.08), (pin_r, zt + 0.14), (0, zt + 0.14)], segs=32), "hand_dark")
    zs = hs["z"]["subdial"]
    for key, sd in tr["subdials"].items():  # black needles on black hubs
        c, L, (w0, w1), hb = sd["centre_mm"], sd["length_mm"], sd["half_mm"], sd["hub_mm"]
        hand("subdial_%s_hand" % key, [(-w0, 0.0), (w0, 0.0), (w1, L), (-w1, L)], sd["angle_deg"], zs, "hand_dark", c=c)
        add("subdial_%s_hub" % key, Geo().lathe([(0, d["z"]), (hb, d["z"]), (hb, zs + th + 0.04), (0, zs + th + 0.04)], segs=48,
                                                m=Matrix.Translation((c[0], c[1], 0))), "hand_dark")
        add("subdial_%s_cap" % key, Geo().lathe([(0, zs + th + 0.04), (hb * 0.35, zs + th + 0.04), (hb * 0.35, zs + th + 0.1), (0, zs + th + 0.1)], segs=32,
                                                m=Matrix.Translation((c[0], c[1], 0))), "steel_polished")

    # ---- fluted crown at 3 on a radial axis ----
    cw_, crn = cfg["crown"], tr["crown"]
    a = math.radians(crn["angle_deg"])
    R0, teeth, depth = crn["radius_mm"], crn["teeth"], cw_["flute_depth"]
    star = [((R0 if i % 2 == 0 else R0 - depth) * math.cos(math.pi * i / teeth), (R0 if i % 2 == 0 else R0 - depth) * math.sin(math.pi * i / teeth))
            for i in range(teeth * 2)]
    u, dr = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
    m = Matrix((u, (0, 0, 1), dr)).transposed().to_4x4()
    m.translation = (0, 0, cw_["z"])
    c0, c1 = crn["collar_mm"]
    add("crown_collar", Geo().lathe([(0, c0), (crn["collar_radius_mm"], c0), (crn["collar_radius_mm"], c1), (0, c1)], segs=48, m=m), "steel_polished", bevel=0.1)
    add("crown", Geo().prism(star, c1, crn["r_mm"][1], m), "steel_polished", bevel=0.2)

    # ---- blue paddle pushers at 2 and 4 (photo outlines; the inner part runs under the case flank) ----
    pu = cfg["pushers"]
    g = Geo()
    for poly in tr["pushers_mm"]:
        g.prism([tuple(p) for p in poly], pu["z0"], pu["z1"])
    add("pushers", g, "pusher_blue", bevel=pu["bevel"])

    # ---- cushion flanks and lug horns: one slab from the silhouette (mean of both halves, lug tip at the listed 25 mm) ----
    lg, tl_ = cfg["lug"], tr["lug"]
    tip, xi = tl_["tip_mm"], tl_["inner_x_mm"]
    prof = [(y, w) for y, w in tr["case_half_width_by_y_mm"] if y <= tip]
    ys_ = tip - lg["shoulder_mm"]  # rounded shoulder: quarter ellipse from the flank at ys_ to the horn's inner edge at the tip
    w_s = next(w for y, w in prof if y >= ys_)
    shoulder = [(xi + (w_s - xi) * math.cos(math.pi / 2 * i / 12), ys_ + lg["shoulder_mm"] * math.sin(math.pi / 2 * i / 12)) for i in range(13)]
    outline = [(xi, 0.0)] + [(w, y) for y, w in prof if y < ys_] + shoulder
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * min(1.0, max(0.0, (abs(y) - lg["slope_from_y"]) / (tip - lg["slope_from_y"])))
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(bx + sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("case_lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

    # ---- three-column bracelet: end links between the lugs, then curled links; centre joints `shift` nearer the case ----
    br, el = cfg["bracelet"], cfg["end_link"]
    ch, shift, gap = tr["bracelet_centre_half_mm"], tr["bracelet_centre_joint_shift_mm"], br["gap"]
    hw0, hw1 = br["half_width"]
    hw_at = lambda y: hw0 + (hw1 - hw0) * min(1.0, max(0.0, (y - tip) / (br["end_y"] - tip)))
    end = Geo()
    for sy in (1, -1):
        M = Matrix.Translation((0, sy * (el["from_y"] + tip) / 2, 0))
        for sx in (1, -1):
            end.prism(rect(sx * (ch + gap + el["half_width"]) / 2, 0, el["half_width"] - ch - gap, tip - el["from_y"]), 0.0, el["top_z"], M)
        y1 = tip - shift - gap
        end.prism(rect(0, sy * (el["from_y"] + y1) / 2, 2 * ch, y1 - el["from_y"]), 0.0, el["top_z"])
    add("end_links", end, "steel_brushed", bevel=el["bevel"], polished_bevel=True)

    zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]
    bent_box = curl(tip + br.get("bend_after_tip", 0.0), R, zm)
    links, back = Geo(), Geo()
    rows = 0
    za, zb = ds * br["z0"], ds * br["z1"]
    for sy in (1, -1):
        for kind, start in (("outer", tip), ("centre", tip - shift)):
            y0 = start
            while y0 < br["end_y"] - 0.5:
                y1 = min(y0 + br["pitch"] - gap, br["end_y"])
                hw_ = hw_at((y0 + y1) / 2)
                if kind == "outer":
                    for sx in (1, -1):
                        x0, x1 = sorted((sx * (ch + gap), sx * hw_))
                        bent_box(links, x0, x1, y0, y1, za, zb, sy)
                    bent_box(back, -(hw_ - 0.3), hw_ - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                else:
                    bent_box(links, -ch, ch, y0, y1, za, zb + ds * br["centre_raise"], sy)
                y0 = y1 + gap
    add("bracelet_links", links, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(w for y, w in prof if y < 3), 3), "lug_to_lug": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "bracelet_rows": rows, "numeral_shapes": len(shapes),
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
