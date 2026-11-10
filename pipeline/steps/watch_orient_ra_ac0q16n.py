"""watch_orient_ra_ac0q16n: build the Orient RA-AC0Q16N (grey fume diver, steel bezel, steel bracelet) as a flat-backed front relief.

Params: spec (config/watches/orient-ra-ac0q16n.json). Same frame, pose, 2.5D depth scale, materials and bracelet curl as
watch_seiko_sur419_front, whose helpers it reuses. Parts from the photo: a steel bezel (polished inner lip, brushed flat top
with the traced black-filled engravings as raised black inlays, coin-edge rim with 72 slots), applied polished frames with
lume (triangle at 12, bars at 6 and 9, trapezoids elsewhere) and a polished date frame, an arrow hour hand (black stem, lume
head), a sword minute hand (black stem, lume blade), a seconds needle with an orange-framed lume triangle and a black
counterweight, a fluted crown, brushed lugs with a polished chamfer and a three-column bracelet whose centre joints sit nearer
the case. The dial (fume sunburst, minute track, prints, date) is the photo map from pipeline/orient_ra_ac0q16n_dial.py.
Rebuild with --force after regenerating the map (it is not part of the stage fingerprint).
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
    coll = bpy.data.collections.new("WATCH | Orient RA-AC0Q16N front relief")
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

    circle = lambda r, n=192, cx=0.0, cy=0.0: [(cx + r * math.sin(2 * math.pi * k / n), cy + r * math.cos(2 * math.pi * k / n)) for k in range(n)]
    bx, by = tr["bezel_offset_mm"]
    rg = tr["bezel_rings_mm"]

    # ---- case under the bezel, crystal, gasket ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), "steel_polished")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- bezel: polished lip, brushed flat top with black inlays, coin-edge rim (rounded lobes between the slots) ----
    bz = cfg["bezel"]
    centred = Matrix.Translation((bx, by, 0))
    l0, l1 = rg["lip_in"], rg["top_in"]
    add("bezel_lip", Geo().lathe([(l0, bz["lip_z"]), (l1, bz["top_z"]), (l1, bz["z0"]), (l0, bz["z0"])], segs=192, m=centred), "steel_polished")
    add("bezel_top", Geo().lathe([(l1, bz["z0"]), (rg["top_out"], bz["z0"]), (rg["top_out"], bz["top_z"]), (l1, bz["top_z"])], segs=192, m=centred),
        "steel_brushed")
    n, depth, tip_r = tr["bezel_notches"]["count"], bz["slot_depth"], bz["rim_r"]
    star = [(lambda a, f: (bx + (tip_r - depth * (1 - math.sin(math.pi * f)) ** 4) * math.sin(a),
                           by + (tip_r - depth * (1 - math.sin(math.pi * f)) ** 4) * math.cos(a)))(2 * math.pi * k / (8 * n), (k % 8) / 8)
            for k in range(8 * n)]  # narrow slots: the power keeps the lobe full and the slot sharp
    add("bezel_rim", plate([{"outer": star, "holes": [circle(rg["top_out"] - 0.05, 192, bx, by)]}], bz["z0"], bz["rim_z"], P + "bezel_rim"),
        "steel_polished", bevel=bz["rim_bevel"])
    add("bezel_inlays", plate(tr["bezel_engravings"], bz["top_z"] - 0.05, bz["top_z"] + bz["inlay_raise"], P + "bezel_inlays"), "bezel_fill")

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

    # ---- applied polished frames with recessed lume; polished date frame ----
    ix, ti = cfg["indices"], tr["indices"]
    fw, z0, z1 = ti["frame_mm"], d["z"], d["z"] + ix["height"]

    def inset(poly, k):
        """Shrink a convex polygon by k (mm) toward its centroid along each edge's normal."""
        from mathutils import Vector, geometry as mg
        nn = len(poly)
        area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))
        s = 1 if area > 0 else -1
        lines = []
        for i in range(nn):
            (ax, ay), (bx_, by_) = poly[i], poly[(i + 1) % nn]
            ex, ey = bx_ - ax, by_ - ay
            ln = math.hypot(ex, ey)
            nx, ny = -s * ey / ln, s * ex / ln  # inward normal
            lines.append(((ax + k * nx, ay + k * ny), (bx_ + k * nx, by_ + k * ny)))
        out = []
        for i in range(nn):
            (p1, p2), (p3, p4) = lines[i - 1], lines[i]
            hit = mg.intersect_line_line_2d(Vector(p1), Vector(p2), Vector(p3), Vector(p4)) or None
            if hit is None:  # parallel neighbours: extend the lines
                d1 = Vector(p2) - Vector(p1)
                d2 = Vector(p4) - Vector(p3)
                den = d1.x * d2.y - d1.y * d2.x
                t_ = ((p3[0] - p1[0]) * d2.y - (p3[1] - p1[1]) * d2.x) / den
                hit = Vector(p1) + d1 * t_
            out.append((hit.x, hit.y))
        return out

    shapes, lume = [], Geo()
    r0, r1 = ti["inner_mm"], ti["outer_mm"]
    for hr in range(1, 13):
        if hr == 3:
            continue
        if hr == 12:
            t12 = ti["triangle_12"]
            poly = [(-t12["half_width_mm"], t12["top_r_mm"]), (0.0, t12["point_r_mm"]), (t12["half_width_mm"], t12["top_r_mm"])]
        elif hr in (6, 9):
            poly = [rot(x, y, hr * 30) for x, y in rect(0, (r0 + r1) / 2, ti["bar_width_mm"], r1 - r0)]
        else:
            w0, w1 = ti["width_inner_mm"] / 2, ti["width_outer_mm"] / 2
            poly = [rot(x, y, hr * 30) for x, y in ((-w0, r0), (w0, r0), (w1, r1), (-w1, r1))]
        hole = inset(poly, fw)
        shapes.append({"outer": [list(p) for p in poly], "holes": [[list(p) for p in hole]]})
        lume.prism(hole, z0, z1 - ix["lume_recess"])
    dw = tr["date_window"]["x0_y0_x1_y1_mm"]
    dx0, dy0, dx1, dy1 = dw
    outer = [(dx0, dy0), (dx1, dy0), (dx1, dy1), (dx0, dy1)]
    shapes.append({"outer": [list(p) for p in outer], "holes": [[list(p) for p in inset(outer, ix["date_frame"])]]})
    add("indices", plate(shapes, z0, z1, P + "indices"), "steel_polished")
    add("index_lume", lume, "lume")

    # ---- hands at the photo's time ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]

    def hand(name, poly, deg, z, mat, h=th):
        add(name, Geo().prism([rot(x, y, deg) for x, y in poly], z, z + h), mat, bevel=0.02 if mat == "steel_polished" else None)

    h = t["hour"]  # arrow: stem, notched head base, black stem fill, lume head
    L, h0, hw, sw, deg, z = h["length_mm"], h["head_from_mm"], h["head_half_width_mm"], hs["hour_stem_half_width"], h["angle_deg"], hs["z"]["hour"]
    notch = h0 + hs["hour_notch"]
    hand("hand_hour", [(-sw, -1.0), (sw, -1.0), (sw, notch), (hw, h0), (0, L), (-hw, h0), (-sw, notch)], deg, z, "steel_polished")
    k = hs["outline"]
    hand("hand_hour_stem", [(-sw + k, 1.0), (sw - k, 1.0), (sw - k, notch - 0.1), (-sw + k, notch - 0.1)], deg, z + th, "hand_dark", 0.05)
    hand("hand_hour_lume", inset([(hw, h0), (0, L), (-hw, h0), (-sw, notch), (sw, notch)], k), deg, z + th, "lume", 0.05)

    h = t["minute"]  # sword: black stem, lume blade
    L, w0, w1, deg, z = h["length_mm"], hs["minute_root_half_width"], hs["minute_max_half_width"], h["angle_deg"], hs["z"]["minute"]
    blade = lambda a: w0 + (w1 - w0) * a / (0.55 * L) if a < 0.55 * L else w1 * (L - a) / (0.45 * L)
    hand("hand_minute", [(-w0, -0.8), (w0, -0.8), (w1, 0.55 * L), (0, L), (-w1, 0.55 * L)], deg, z, "steel_polished")
    a0 = h["lume_from_mm"]
    hand("hand_minute_stem", [(-blade(1.0) + k, 1.0), (blade(1.0) - k, 1.0), (blade(a0) - k, a0 - 0.15), (-blade(a0) + k, a0 - 0.15)], deg, z + th, "hand_dark", 0.05)
    hand("hand_minute_lume", [(-blade(a0) + k, a0), (blade(a0) - k, a0), (w1 - k, 0.55 * L), (0, L - 3 * k), (-w1 + k, 0.55 * L)], deg, z + th, "lume", 0.05)

    h = t["seconds"]  # needle, orange-framed lume triangle, black counterweight with a polished rim
    L, tail, deg, z = h["length_mm"], h["tail_mm"], h["angle_deg"], hs["z"]["seconds"]
    nw, cw = h["half_width_mm"], hs["seconds_tail_half_width"]
    s0, s1, sh = h["lume_mm"]
    hand("hand_seconds", [(-nw, -tail + 0.5), (nw, -tail + 0.5), (nw, s1), (-nw, s1)], deg, z, "steel_polished")
    hand("hand_seconds_tail", [(-cw, -tail), (cw, -tail), (cw * 0.8, -0.8), (-cw * 0.8, -0.8)], deg, z, "steel_polished")
    hand("hand_seconds_tail_fill", [(-cw + k, -tail + k), (cw - k, -tail + k), (cw * 0.8 - k, -1.0), (-cw * 0.8 + k, -1.0)], deg, z + th, "hand_dark", 0.05)
    tri = [(-sh, s1), (0, s0), (sh, s1)]
    hand("hand_seconds_frame", tri, deg, z, "seconds_orange")
    hand("hand_seconds_pointer", [(-0.08, s1 - 0.05), (0.08, s1 - 0.05), (0, L)], deg, z, "seconds_orange")
    hand("hand_seconds_lume", inset(tri, k * 0.7), deg, z + th, "lume", 0.05)
    collar_r, cap_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (collar_r, d["z"]), (collar_r, hs["z"]["hour"] + th), (0, hs["z"]["hour"] + th)], segs=64), "steel_polished")
    add("hub_post", Geo().lathe([(0, d["z"]), (cap_r * 1.5, d["z"]), (cap_r * 1.5, z), (0, z)], segs=48), "hand_dark")
    zc = z + th
    add("hub_cap", Geo().lathe([(0, zc), (cap_r, zc), (cap_r, zc + 0.1), (cap_r * 0.6, zc + 0.18), (0, zc + 0.18)], segs=48), "steel_polished")

    # ---- crown: smooth collar and fluted cylinder on a radial axis at the traced angle (3 o'clock) ----
    cw_ = cfg["crown"]
    a = math.radians(math.degrees(math.atan2(*tr["crown_box"]["centre_mm"])) % 360)
    star = [((cw_["radius"] if i % 2 == 0 else cw_["radius"] - cw_["flute_depth"]) * math.cos(math.pi * i / cw_["teeth"]),
             (cw_["radius"] if i % 2 == 0 else cw_["radius"] - cw_["flute_depth"]) * math.sin(math.pi * i / cw_["teeth"])) for i in range(cw_["teeth"] * 2)]
    u, dr = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
    m = Matrix((u, (0, 0, 1), dr)).transposed().to_4x4()
    m.translation = (0, 0, cw_["z"])
    add("crown_collar", Geo().lathe([(0, cw_["collar"][0]), (cw_["collar_r"], cw_["collar"][0]), (cw_["collar_r"], cw_["collar"][1]),
                                     (0, cw_["collar"][1])], segs=48, m=m), "steel_polished", bevel=0.1)
    add("crown", Geo().prism(star, cw_["collar"][1], cw_["r_to"], m), "steel_polished", bevel=0.15)

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
    out = {"diameter": round(2 * tip_r, 3), "lug_to_lug": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "bracelet_rows": rows, "bezel_inlays": len(tr["bezel_engravings"]),
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
