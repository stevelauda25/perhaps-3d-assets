"""watch_orient_re_au0601b: build the Orient Star RE-AU0601B (Diver 1964 2nd edition, black dial, black insert, five-link
bracelet) as a flat-backed front relief.

Params: spec (config/watches/orient-re-au0601b.json). Same frame, pose, 2.5D depth scale, materials and bracelet curl as
watch_orient_ra_aa0818l19b. Parts from the photo: a steel bezel with a fine coin edge around a black insert with the traced white
prints as raised inlays and a lume pip in the 12 triangle; applied polished-rim lume dots, bars at 6 and 9, a trapezoid at 12
and a square at 3 beside a polished date frame; a lollipop hour hand (lume disc in a polished ring, short tip), a sword minute
hand with a lume blade, a seconds needle with a lume disc and a small counterweight disc, a power reserve hand on its own hub at
12; a fluted crown; lugs from the photo silhouette and a five-column bracelet (brushed 1 3 5, polished 2 4 with their joints
further out). The dial (gloss black, minute track, logo, power reserve print, date) is the photo map from
pipeline/orient_re_au0601b_dial.py. Rebuild with --force after regenerating the map (it is not part of the stage fingerprint).
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
    coll = bpy.data.collections.new("WATCH | Orient RE-AU0601B front relief")
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

    # ---- bezel: polished inner lip, black insert with white prints and a lume pip, coin-edge steel ring ----
    bz = cfg["bezel"]
    centred = Matrix.Translation((bx, by, 0))
    ri, ro = rg["insert_in"], rg["insert_out"]
    add("bezel_lip", Geo().lathe([(rg["lip_in"], bz["lip_z"]), (ri, bz["insert_z"]), (ri, bz["z0"]), (rg["lip_in"], bz["z0"])], segs=192, m=centred),
        "steel_polished")
    add("insert", Geo().lathe([(ri, bz["z0"]), (ro, bz["z0"]), (ro, bz["insert_z"]), (ri, bz["insert_z"])], segs=192, m=centred), "insert_black")
    pip = tr["pip_mm"]
    near_pip = lambda lp: math.dist([sum(v) / len(lp) for v in zip(*lp)], pip["centre"]) < 2 * pip["ring_r"]
    prints = [dict(sh, holes=[hl for hl in sh["holes"] if not near_pip(hl)]) for sh in tr["insert_prints"]]  # the pip sits on a solid triangle
    add("insert_prints", plate(prints, bz["insert_z"] - 0.05, bz["insert_z"] + bz["print_raise"], P + "insert_prints"), "print_white")
    pz = bz["insert_z"] + bz["print_raise"]
    pm = Matrix.Translation((*pip["centre"], 0))
    add("pip_ring", Geo().lathe([(0, bz["insert_z"]), (pip["ring_r"], bz["insert_z"]), (pip["ring_r"], pz + 0.15), (pip["lume_r"], pz + 0.15),
                                 (pip["lume_r"], pz), (0, pz)], segs=48, m=pm), "steel_polished")
    add("pip_lume", Geo().lathe([(0, pz), (pip["lume_r"], pz), (pip["lume_r"], pz + 0.12), (0, pz + 0.12)], segs=48, m=pm), "lume")
    n, depth, tip_r = tr["bezel_notches"]["count"], bz["slot_depth"], rg["rim_out"]
    star = [(lambda a, f: (bx + (tip_r - depth * (1 - math.sin(math.pi * f)) ** bz["slot_power"]) * math.sin(a),
                           by + (tip_r - depth * (1 - math.sin(math.pi * f)) ** bz["slot_power"]) * math.cos(a)))(2 * math.pi * k / (6 * n), (k % 6) / 6)
            for k in range(6 * n)]  # coin edge: flat-topped teeth, narrow slots
    add("bezel_rim", plate([{"outer": star, "holes": [circle(ro - 0.05, 192, bx, by)]}], bz["z0"], bz["rim_z"], P + "bezel_rim"),
        "steel_polished", bevel=bz["rim_bevel"])

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
    dr, dro, drl = ti["dot_r_mm"], ti["dot_ring_mm"], ti["dot_lume_mm"]
    rings, dots = Geo(), Geo()
    for hr in (1, 2, 4, 5, 7, 8, 10, 11):  # polished cup with a lume disc
        m_ = Matrix.Translation((dr * math.sin(math.radians(hr * 30)), dr * math.cos(math.radians(hr * 30)), 0))
        rings.lathe([(drl, z0), (dro, z0), (dro, z1 - 0.06), (dro - 0.08, z1), (drl, z1)], segs=48, m=m_)
        dots.lathe([(0, z0), (drl, z0), (drl, z1 - ix["lume_recess"]), (0, z1 - ix["lume_recess"])], segs=48, m=m_)
    add("index_rings", rings, "steel_polished", smooth=True)
    add("index_dots", dots, "lume", smooth=True)
    b0, b1, bw = ti["bar_inner_mm"], ti["bar_outer_mm"], ti["bar_width_mm"]
    t12 = ti["trapezoid_12"]
    sq = ti["square_3"]["x0_y0_x1_y1_mm"]
    polys = [[rot(x, y, hr * 30) for x, y in rect(0, (b0 + b1) / 2, bw, b1 - b0)] for hr in (6, 9)]
    polys.append([(t12["x_mm"] - t12["top_half_mm"], t12["top_r_mm"]), (t12["x_mm"] - t12["bottom_half_mm"], t12["bottom_r_mm"]),
                  (t12["x_mm"] + t12["bottom_half_mm"], t12["bottom_r_mm"]), (t12["x_mm"] + t12["top_half_mm"], t12["top_r_mm"])])
    polys.append([(sq[0], sq[1]), (sq[2], sq[1]), (sq[2], sq[3]), (sq[0], sq[3])])
    for poly in polys:
        shapes.append({"outer": [list(p) for p in poly], "holes": [[list(p) for p in inset(poly, fw)]]})
        lume.prism(inset(poly, fw), z0, z1 - ix["lume_recess"])
    add("indices", plate(shapes, z0, z1, P + "indices"), "steel_polished")
    add("index_lume", lume, "lume")
    dx0, dy0, dx1, dy1 = tr["date_window"]["x0_y0_x1_y1_mm"]
    ix0, iy0, ix1, iy1 = tr["date_inner"]["x0_y0_x1_y1_mm"]
    add("date_frame", plate([{"outer": [[dx0, dy0], [dx1, dy0], [dx1, dy1], [dx0, dy1]], "holes": [[[ix0, iy0], [ix1, iy0], [ix1, iy1], [ix0, iy1]]]}],
                            z0, z1, P + "date_frame"), "steel_polished")

    # ---- hands at the photo's time ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]

    def hand(name, poly, deg, z, mat, h=th):
        add(name, Geo().prism([rot(x, y, deg) for x, y in poly], z, z + h), mat, bevel=0.02 if mat == "steel_polished" else None)

    k = hs["outline"]
    disc = lambda r, c, n_=40: [(c[0] + r * math.cos(2 * math.pi * i / n_), c[1] + r * math.sin(2 * math.pi * i / n_)) for i in range(n_)]

    h = t["hour"]  # lollipop: stem with lume, lume disc in a polished ring, short pointed tip
    L, dc, (rr, rl), deg, z = h["length_mm"], h["disc_at_mm"], h["disc_r_mm"], h["angle_deg"], hs["z"]["hour"]
    sw = hs["hour_stem_half_width"]
    hand("hand_hour", [(-sw, -0.8), (sw, -0.8), (sw, dc), (-sw, dc)], deg, z, "steel_polished")
    hand("hand_hour_disc", disc(rr, (0, dc), 64), deg, z, "steel_polished")
    hand("hand_hour_tip", [(-hs["hour_tip_half_width"], dc + rr * 0.8), (hs["hour_tip_half_width"], dc + rr * 0.8), (0, L)], deg, z, "steel_polished")
    hand("hand_hour_lume", disc(rl, (0, dc), 64), deg, z + th, "lume", 0.05)
    hand("hand_hour_stem_lume", [(-sw + k, 1.2), (sw - k, 1.2), (sw - k, dc - rl + 0.05), (-sw + k, dc - rl + 0.05)], deg, z + th, "lume", 0.05)

    h = t["minute"]  # sword: polished outline, lume blade
    L, am, deg, z = h["length_mm"], h["widest_at_mm"], h["angle_deg"], hs["z"]["minute"]
    w0, w1 = hs["minute_root_half_width"], hs["minute_max_half_width"]
    leaf = lambda a: w0 + (w1 - w0) * a / am if a < am else w1 * (L - a) / (L - am)
    hand("hand_minute", [(-w0, -0.8), (w0, -0.8), (w1, am), (0, L), (-w1, am)], deg, z, "steel_polished")
    l0, l1 = h["lume_mm"]
    q = hs["minute_lume_inset"]
    hand("hand_minute_lume", [(-leaf(l0) + q, l0), (leaf(l0) - q, l0), (w1 - q, am), (leaf(l1) - q, l1), (-leaf(l1) + q, l1), (-w1 + q, am)],
         deg, z + th, "lume", 0.05)

    h = t["seconds"]  # polished needle, lume disc in a ring, small polished counterweight disc
    L, tail, deg, z = h["length_mm"], h["tail_mm"], h["angle_deg"], hs["z"]["seconds"]
    nw = h["half_width_mm"]
    hand("hand_seconds", [(-nw, -tail), (nw, -tail), (nw * 0.6, L), (-nw * 0.6, L)], deg, z, "steel_polished")
    hand("hand_seconds_disc", disc(h["disc_r_mm"], (0, h["disc_at_mm"]), 48), deg, z, "steel_polished")
    hand("hand_seconds_lume", disc(h["disc_r_mm"] - k, (0, h["disc_at_mm"]), 48), deg, z + th, "lume", 0.05)
    hand("hand_seconds_tail", disc(h["tail_disc_r_mm"], (0, -tail), 32), deg, z, "steel_polished")

    h = t["power_reserve"]  # tapered polished hand on its own hub
    pc_, prd = h["centre_mm"], h["angle_deg"]
    zp = d["z"] + hs["pr_z"]
    add("pr_hand", Geo().prism([(pc_[0] + x, pc_[1] + y) for x, y in (rot(x, y, prd) for x, y in
                                ((-h["half_width_mm"], 0), (h["half_width_mm"], 0), (0.04, h["length_mm"]), (-0.04, h["length_mm"])))], zp, zp + th),
        "steel_polished", bevel=0.02)
    pm_ = Matrix.Translation((*pc_, 0))
    add("pr_hub", Geo().lathe([(0, d["z"]), (h["hub_r_mm"], d["z"]), (h["hub_r_mm"], zp + th + 0.05), (0, zp + th + 0.05)], segs=48, m=pm_), "steel_polished")
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

    # ---- case flanks and lugs from the traced silhouette (left edge, top/bottom averaged): brushed top, polished chamfer ----
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}

    def half(y):  # half the width (the photo sits a little off-centre to the pivot); left edge only where the crown is
        ys = [sil[k_] for k_ in (round(y, 2), round(-y, 2)) if k_ in sil]
        return sum((-p[1] if abs(y) < cfg["crown_zone_mm"] else (p[2] - p[1]) / 2) for p in ys) / len(ys)

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

    # ---- five-column bracelet: brushed 1 3 5 from the lug tips, polished 2 4 with their first joint `shift` further out ----
    br, el = cfg["bracelet"], cfg["end_link"]
    fo, fc = tr["bracelet_column_fractions"]  # joint |x| / half width: outer|polished, polished|centre
    shift, gap = tr["bracelet_polished_joint_shift_mm"], br["gap"]
    sil_max = min(max(sil), -min(sil)) - 0.25
    hw_at = lambda y: min(half(round(min(max(y, tip + 1.0), sil_max) * 4) / 4), el["half_width"])
    end = Geo()
    for sy in (1, -1):
        end.prism(rect(0, sy * (el["from_y"] + tip) / 2, 2 * el["half_width"], tip - el["from_y"]), 0.0, el["top_z"])
    add("end_links", end, "steel_brushed", bevel=el["bevel"], polished_bevel=True)

    zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]
    bent_box = curl(tip + br.get("bend_after_tip", 0.0), R, zm)
    pitch = tr["bracelet_pitch_mm"]
    brushed, polished, back = Geo(), Geo(), Geo()
    rows = 0
    za, zb = ds * br["z0"], ds * br["z1"]
    for sy in (1, -1):
        for kind, first in (("brushed", pitch - gap), ("polished", shift - gap)):
            y0, y1 = tip, tip + first
            while y0 < br["end_y"] - 0.5:
                y1 = min(y1, br["end_y"])
                hw_ = hw_at((y0 + y1) / 2)
                if kind == "brushed":
                    for sx in (1, -1):
                        x0, x1 = sorted((sx * (fo * hw_ + gap / 2), sx * hw_))
                        bent_box(brushed, x0, x1, y0, y1, za, zb, sy)
                    bent_box(brushed, -(fc * hw_ - gap / 2), fc * hw_ - gap / 2, y0, y1, za, zb, sy)
                    bent_box(back, -(hw_ - 0.3), hw_ - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                else:
                    for sx in (1, -1):
                        x0, x1 = sorted((sx * (fc * hw_ + gap / 2), sx * (fo * hw_ - gap / 2)))
                        bent_box(polished, x0, x1, y0, y1, za, zb + ds * br["polished_raise"], sy)
                y0 = y1 + gap
                y1 = y0 + pitch - gap
    add("bracelet_links", brushed, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_polished", polished, "steel_polished", bevel=br["bevel"])
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * tip_r, 3), "lug_to_lug": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "bracelet_rows": rows, "insert_prints": len(tr["insert_prints"]),
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
