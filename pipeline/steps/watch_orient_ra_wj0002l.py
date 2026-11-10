"""watch_orient_ra_wj0002l: build the Orient RA-WJ0002L (Mako solar, blue sunburst dial, khaki bezel, steel bracelet) as a flat-backed front relief.

Params: spec (config/watches/orient-ra-wj0002l.json). Same frame, pose, 2.5D depth scale, materials, lugs, end links and
three-column bracelet curl as watch_orient_ra_ac0q16n. Parts from the photo: a round case whose flank shows outside the bezel,
a polished coin-edge bezel rim with 60 round dimples, the khaki insert with its print (photo map), a black ring at the crystal
edge, applied polished frames with lume at 1 2 4 5 7 8 10 11, applied polished 12, 9 and 6 traced from the photo, a polished
date frame, hour and minute hands as polished frames with a black inside and a lume inlay, a polished seconds needle with an
orange tip and bulb and a dark counterweight, a fluted crown with a collar. The dial (sunburst, minute track, prints, date) and
the insert are one photo map from pipeline/orient_ra_wj0002l_dial.py. Rebuild with --force after regenerating the map.
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def inset(poly, k):
    """Shrink a convex polygon by k (mm) along each edge's inward normal."""
    from mathutils import Vector, geometry as mg
    nn = len(poly)
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))
    s = 1 if area > 0 else -1
    lines = []
    for i in range(nn):
        (ax, ay), (bx, by) = poly[i], poly[(i + 1) % nn]
        ex, ey = bx - ax, by - ay
        ln = math.hypot(ex, ey)
        nx, ny = -s * ey / ln, s * ex / ln
        lines.append(((ax + k * nx, ay + k * ny), (bx + k * nx, by + k * ny)))
    out = []
    for i in range(nn):
        (p1, p2), (p3, p4) = lines[i - 1], lines[i]
        hit = mg.intersect_line_line_2d(Vector(p1), Vector(p2), Vector(p3), Vector(p4))
        if hit is None:  # parallel neighbours: extend the lines
            d1, d2 = Vector(p2) - Vector(p1), Vector(p4) - Vector(p3)
            t_ = ((p3[0] - p1[0]) * d2.y - (p3[1] - p1[1]) * d2.x) / (d1.x * d2.y - d1.y * d2.x)
            hit = Vector(p1) + d1 * t_
        out.append((hit.x, hit.y))
    return out


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
        if mat in textured:  # planar UV in mm / tile, lines along the bracelet (model Y)
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

    H = dm["half_size_mm"]

    def photo_mesh(name, geo):  # planar UV on the dial map, centred on the hand pivot
        me = geo.mesh(P + name, True)
        uv = me.uv_layers.new(name="UVMap")
        for loop in me.loops:
            x, y, _ = me.vertices[loop.vertex_index].co
            uv.data[loop.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
        return me

    circle = lambda r, n=192, cx=0.0, cy=0.0: [(cx + r * math.sin(2 * math.pi * k / n), cy + r * math.cos(2 * math.pi * k / n)) for k in range(n)]
    rg = tr["bezel_rings_mm"]

    # ---- case (flank shows outside the bezel), crystal ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), "steel_polished")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (rg["crystal"], cr["z0"]), (rg["crystal"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- bezel: coin-edge rim with round dimples, photo-mapped khaki insert, black ring at the crystal edge ----
    bz = cfg["bezel"]
    n, depth, tip_r = tr["bezel_notches"]["count"], bz["dimple_depth"], rg["rim_out"]
    star = [(lambda a, f: ((tip_r - depth * (1 - math.sin(math.pi * f)) ** 2) * math.sin(a),
                           (tip_r - depth * (1 - math.sin(math.pi * f)) ** 2) * math.cos(a)))(2 * math.pi * k / (8 * n), (k % 8) / 8)
            for k in range(8 * n)]  # rounded dimples between full lobes
    add("bezel_rim", plate([{"outer": star, "holes": [circle(rg["insert_out"] - 0.05)]}], bz["z0"], bz["rim_z"], P + "bezel_rim"),
        "steel_polished", bevel=bz["rim_bevel"])
    ri, ro = rg["insert_in"], rg["insert_out"]
    add("bezel_insert", photo_mesh("bezel_insert", Geo().lathe([(ri, bz["z0"]), (ro, bz["z0"]), (ro, bz["insert_z"][1]), (ri, bz["insert_z"][0])],
                                                              segs=192)), "dial")
    add("bezel_inner", Geo().lathe([(rg["crystal"] - 0.1, d["rehaut_z"]), (ri + 0.02, d["rehaut_z"]), (ri + 0.02, bz["insert_z"][0] - 0.02),
                                    (rg["crystal"] - 0.1, bz["insert_z"][0] - 0.02)], segs=192), "gasket_black")

    # ---- dial + rehaut, photo map ----
    me = Geo().lathe([(0, d["z"]), (rg["dial"], d["z"]), (rg["crystal"], d["rehaut_z"])], segs=192).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    uv = me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        x, y, _ = me.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
    add("dial", me, "dial")

    # ---- applied polished frames with recessed lume, applied numerals, polished date frame ----
    ix, ti = cfg["indices"], tr["indices"]
    fw, z0, z1 = ti["frame_mm"], d["z"], d["z"] + ix["height"]
    shapes, lume = [], Geo()
    r0, r1, bw = ti["inner_mm"], ti["outer_mm"], ti["width_mm"]
    for hr in (1, 2, 4, 5, 7, 8, 10, 11):
        poly = [rot(x, y, hr * 30) for x, y in rect(0, (r0 + r1) / 2, bw, r1 - r0)]
        hole = inset(poly, fw)
        shapes.append({"outer": [list(p) for p in poly], "holes": [[list(p) for p in hole]]})
        lume.prism(hole, z0, z1 - ix["lume_recess"])
    dx0, dy0, dx1, dy1 = tr["date_window"]["x0_y0_x1_y1_mm"]
    outer = [(dx0, dy0), (dx1, dy0), (dx1, dy1), (dx0, dy1)]
    shapes.append({"outer": [list(p) for p in outer], "holes": [[list(p) for p in inset(outer, ix["date_frame"])]]})
    add("indices", plate(shapes, z0, z1, P + "indices"), "steel_polished")
    add("index_lume", lume, "lume")
    add("numerals", plate(tr["numerals"], z0, z0 + ix["numeral_height"], P + "numerals"), "steel_polished", bevel=ix["numeral_bevel"])

    # ---- hands at the photo's time ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    k = hs["outline"]

    def hand(name, poly, deg, z, mat, h=th):
        add(name, Geo().prism([rot(x, y, deg) for x, y in poly], z, z + h), mat, bevel=0.02 if mat == "steel_polished" else None)

    for name in ("hour", "minute"):  # polished frame, black inside, lume inlay
        h = t[name]
        (a0, w0), (a1, w1) = h["outline_mm"]
        L, deg, z = h["length_mm"], h["angle_deg"], hs["z"][name]
        frame = [(-w0, a0), (w0, a0), (w1, a1), (0, L), (-w1, a1)]
        hand("hand_" + name, frame, deg, z, "steel_polished")
        hand("hand_%s_dark" % name, inset(frame, k), deg, z + th, "hand_dark", 0.06)
        (l0, lw0), (l1, lw1), (l2, _) = h["lume_mm"]
        hand("hand_%s_lume" % name, [(-lw0, l0), (lw0, l0), (lw1, l1), (0, l2), (-lw1, l1)], deg, z + th, "lume", 0.1)

    h = t["seconds"]  # polished needle, orange bulb and tip, dark counterweight with a polished rim
    L, tail, deg, z = h["length_mm"], h["tail_mm"], h["angle_deg"], hs["z"]["seconds"]
    nw, cw, ob, br_ = h["half_width_mm"], h["tail_half_width_mm"], h["orange_from_mm"], h["bulb_radius_mm"]
    hand("hand_seconds", [(-nw, -tail + 0.5), (nw, -tail + 0.5), (nw, ob), (-nw, ob)], deg, z, "steel_polished")
    hand("hand_seconds_tail", [(-cw, -tail), (cw, -tail), (cw * 0.7, -0.8), (-cw * 0.7, -0.8)], deg, z, "steel_polished")
    hand("hand_seconds_tail_fill", inset([(-cw, -tail), (cw, -tail), (cw * 0.7, -0.8), (-cw * 0.7, -0.8)], k * 0.8), deg, z + th, "hand_dark", 0.06)
    hand("hand_seconds_tip", [(-nw * 1.3, ob), (nw * 1.3, ob), (nw * 0.6, L), (-nw * 0.6, L)], deg, z, "seconds_orange")
    hand("hand_seconds_bulb", [(br_ * math.sin(2 * math.pi * i / 24), ob + br_ * math.cos(2 * math.pi * i / 24)) for i in range(24)][::-1],
         deg, z, "seconds_orange")
    collar_r, cap_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (collar_r, d["z"]), (collar_r, hs["z"]["hour"] + th), (0, hs["z"]["hour"] + th)], segs=64), "steel_polished")
    add("hub_post", Geo().lathe([(0, d["z"]), (cap_r * 1.5, d["z"]), (cap_r * 1.5, z), (0, z)], segs=48), "hand_dark")
    zc = z + th
    add("hub_cap", Geo().lathe([(0, zc), (cap_r, zc), (cap_r, zc + 0.1), (cap_r * 0.6, zc + 0.18), (0, zc + 0.18)], segs=48), "steel_polished")

    # ---- crown: smooth collar and fluted cylinder on a radial axis at the traced angle (3 o'clock) ----
    cw_, cc = cfg["crown"], tr["crown_collar_mm"]
    a = math.radians(math.degrees(math.atan2(*tr["crown_box"]["centre_mm"])) % 360)
    rr = tr["crown_box"]["size_mm"][1] / 2
    star = [((rr if i % 2 == 0 else rr - cw_["flute_depth"]) * math.cos(math.pi * i / cw_["teeth"]),
             (rr if i % 2 == 0 else rr - cw_["flute_depth"]) * math.sin(math.pi * i / cw_["teeth"])) for i in range(cw_["teeth"] * 2)]
    u, dr = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
    m = Matrix((u, (0, 0, 1), dr)).transposed().to_4x4()
    m.translation = (0, 0, cw_["z"])
    add("crown_collar", Geo().lathe([(0, cc["from"] - 0.6), (cc["radius"], cc["from"] - 0.6), (cc["radius"], cc["to"]), (0, cc["to"])], segs=48, m=m),
        "steel_polished", bevel=0.1)
    x1 = tr["crown_box"]["x0_y0_x1_y1_mm"][2]
    add("crown", Geo().prism(star, cc["to"], x1, m), "steel_polished", bevel=0.15)

    # ---- lugs from the traced silhouette (left/right and top/bottom averaged): brushed top, polished chamfer ----
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}

    def half(y):
        ys = [sil[k_] for k_ in (round(y, 2), round(-y, 2)) if k_ in sil]
        return sum((p[2] - p[1]) / 2 for p in ys) / len(ys)

    lg = cfg["lug"]
    tip = tr["lug_tip_mm"]["mean"]
    steps = [lg["from_y"] + k_ * 0.25 for k_ in range(int((tip - lg["from_y"]) / 0.25) + 1)]
    outline = [(lg["inner_x"], lg["from_y"])] + [(half(y), y) for y in steps] + [(lg["inner_x"], tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * (abs(y) - lg["from_y"]) / (tip - lg["from_y"])
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

    # ---- three-column bracelet: brushed outer and centre links, centre joints `shift` nearer the case ----
    br, el = cfg["bracelet"], cfg["end_link"]
    ch, shift, gap = tr["bracelet_centre_half_mm"], tr["bracelet_centre_joint_shift_mm"], br["gap"]
    sil_max = min(max(sil), -min(sil)) - 0.25
    hw_at = lambda y: min(half(round(min(max(y, tip + 1.0), sil_max) * 4) / 4), el["half_width"])
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
    pitch = tr["bracelet_pitch_mm"]
    links, back = Geo(), Geo()
    rows = 0
    za, zb = ds * br["z0"], ds * br["z1"]
    for sy in (1, -1):
        for kind, start in (("outer", tip), ("centre", tip - shift)):
            y0 = start
            while y0 < br["end_y"] - 0.5:
                y1 = min(y0 + pitch - gap, br["end_y"])
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
    out = {"diameter": round(2 * c["profile_rz"][3][0], 3), "lug_to_lug": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "bracelet_rows": rows, "numeral_shapes": len(tr["numerals"]),
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
