"""watch_hamilton_h82405130: build the Hamilton H82405130 (Khaki Navy Scuba Auto 40 mm, black dial, red aluminium insert,
steel bracelet) as a flat-backed front relief.

Params: spec (config/watches/hamilton-h82405130.json). Same frame, pose, 2.5D depth scale, materials and bracelet curl as
watch_orient_ra_aa0818l19b. Parts from the photo: a steel coin-edge bezel with rounded scallops around a red aluminium insert
with the traced white prints as raised inlays; applied indices with a polished frame and recessed lume (trapezoids at 12 3 6 9,
bars elsewhere); tapered baton hour and minute hands (polished outline, lume, black-filled tails, a black slot near the
minute hand's root); a black seconds needle with a polished edge, red frame around a white lume teardrop and a red pointer;
a fluted crown; brushed lugs and a three-column bracelet whose centre links are shorter than the outer ones. The dial
(13-24 numerals, minute track, logo, prints, date) is the photo map from pipeline/hamilton_h82405130_dial.py. Rebuild with
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
    coll = bpy.data.collections.new("WATCH | Hamilton H82405130 front relief")
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

    # ---- bezel: polished inner lip, red aluminium insert with white prints, coin-edge steel ring ----
    bz = cfg["bezel"]
    centred = Matrix.Translation((bx, by, 0))
    ri, ro = rg["insert_in"], rg["insert_out"]
    add("bezel_lip", Geo().lathe([(rg["lip_in"], bz["lip_z"]), (ri, bz["insert_z"]), (ri, bz["z0"]), (rg["lip_in"], bz["z0"])], segs=192, m=centred),
        "steel_polished")
    add("insert", Geo().lathe([(ri, bz["z0"]), (ro, bz["z0"]), (ro, bz["insert_z"]), (ri, bz["insert_z"])], segs=240, m=centred), "insert_red")
    add("insert_prints", plate(tr["insert_prints"], bz["insert_z"] - 0.05, bz["insert_z"] + bz["print_raise"], P + "insert_prints"), "print_white")
    n, depth, tip_r, zs = tr["bezel_notches"]["count"], bz["scallop_depth"], rg["rim_out"], bz["rim_z"] - bz["scallop_z"]
    # smooth outer edge; the top layer has n U-shaped scallops open to the outside, rounded toward the dial
    u = lambda f: (1 - (2 * f - 1) ** 2) ** 0.5
    star = [(lambda a, f: (bx + (tip_r - depth * u(f)) * math.sin(a), by + (tip_r - depth * u(f)) * math.cos(a)))(2 * math.pi * k / (12 * n), (k % 12) / 12)
            for k in range(12 * n)]
    add("bezel_rim", Geo().lathe([(ro - 0.05, bz["z0"]), (tip_r, bz["z0"]), (tip_r, zs), (ro - 0.05, zs)], segs=384, m=centred),
        "steel_polished", bevel=bz["rim_bevel"])
    add("bezel_rim_top", plate([{"outer": star, "holes": [circle(ro - 0.05, 192, bx, by)]}], zs - 0.05, bz["rim_z"], P + "bezel_rim_top"),
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

    # ---- applied indices: polished frame, recessed lume; trapezoids (wide end out) at 12 3 6 9, bars elsewhere ----
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
    for hr in range(12):
        if hr % 3 == 0:
            (r0, r1), (w0, w1) = ti["wedge_r_mm"], ti["wedge_half_mm"]
        else:
            (r0, r1), w0 = ti["bar_r_mm"], ti["bar_half_mm"]
            w1 = w0
        lp = [(-w0, r0), (w0, r0), (w1, r1), (-w1, r1)]  # the traced lume; the frame sits outside it
        outer = [rot(x, y, hr * 30) for x, y in inset(lp, -fw)]
        inner = [rot(x, y, hr * 30) for x, y in lp]
        shapes.append({"outer": [list(p) for p in outer], "holes": [[list(p) for p in inner]]})
        lume.prism(inner, z0, z1 - ix["lume_recess"])
    add("indices", plate(shapes, z0, z1, P + "indices"), "steel_polished")
    add("index_lume", lume, "lume")

    # ---- hands at the photo's time ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]

    def hand(name, poly, deg, z, mat, h=th):
        add(name, Geo().prism([rot(x, y, deg) for x, y in poly], z, z + h), mat, bevel=0.02 if mat == "steel_polished" else None)

    k = tr["hand_outline_mm"]
    for name in ("hour", "minute"):  # tapered baton: polished outline, lume; tail outlined, filled black
        h = t[name]
        L, (ra, wa), wt, deg, z = h["length_mm"], h["root_mm"], h["tip_half_mm"], h["angle_deg"], hs["z"][name]
        tl, t0, t1 = h["tail_mm"]
        body = [(-wa, 0.0), (wa, 0.0), (wa, ra), (wt, L - wt * hs[name + "_tip_round"]), (0, L), (-wt, L - wt * hs[name + "_tip_round"]), (-wa, ra)]
        hand("hand_" + name, body, deg, z, "steel_polished")
        hand("hand_%s_lume" % name, inset([(-wa, ra), (wa, ra)] + body[3:6], k), deg, z + th, "lume", 0.05)
        tail = [(-t1, -tl), (t1, -tl), (t0, 0.0), (-t0, 0.0)]
        hand("hand_%s_tail" % name, tail, deg, z, "steel_polished")
        hand("hand_%s_tail_fill" % name, inset(tail, k), deg, z + th, "hand_dark", 0.04)
        if "slot_mm" in h:  # black slot over the left half near the root (photo)
            s0, s1 = h["slot_mm"]
            hand("hand_%s_slot" % name, [(-wa + k, s0), (-0.02, s0), (-0.02, s1), (-wa + k + (wa - wt) * (s1 - ra) / (L - ra), s1)], deg, z + th + 0.05, "hand_dark", 0.02)
    ring_r = hs["hour_ring_r"]
    add("hand_hour_ring", Geo().lathe([(0, hs["z"]["hour"]), (ring_r, hs["z"]["hour"]), (ring_r, hs["z"]["hour"] + th), (0, hs["z"]["hour"] + th)], segs=64),
        "steel_polished", bevel=0.02)
    add("hand_hour_ring_fill", Geo().lathe([(0, hs["z"]["hour"] + th), (ring_r - k, hs["z"]["hour"] + th), (ring_r - k, hs["z"]["hour"] + th + 0.03),
                                            (0, hs["z"]["hour"] + th + 0.03)], segs=64), "hand_dark")

    h = t["seconds"]  # black needle with a polished edge, red frame around a white lume teardrop, red pointer
    L, tail, deg, z = h["length_mm"], h["tail_mm"], h["angle_deg"], hs["z"]["seconds"]
    nw = h["half_width_mm"]
    a0, aw0, a1, aw1 = h["arrow_mm"]
    l0, lw, l1 = h["lume_mm"]
    pw = h["pointer_half_mm"]
    needle = [(-nw, -tail), (nw, -tail), (nw, a0), (-nw, a0)]
    hand("hand_seconds", needle, deg, z, "steel_polished")
    hand("hand_seconds_fill", inset(needle, k * 0.7), deg, z + th, "hand_dark", 0.03)
    arrow = [(-aw0, a0), (aw0, a0), (aw1, a1), (pw, a1 + 0.3), (pw * 0.6, L), (-pw * 0.6, L), (-pw, a1 + 0.3), (-aw1, a1)]
    hand("hand_seconds_arrow", arrow, deg, z, "seconds_red")
    hand("hand_seconds_lume", [(-lw, l0), (lw, l0), (lw * 0.55, l0 + 0.55 * (l1 - l0)), (0, l1), (-lw * 0.55, l0 + 0.55 * (l1 - l0))], deg, z + th, "lume", 0.03)
    collar_r, cap_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (collar_r, d["z"]), (collar_r, hs["z"]["minute"] + th), (0, hs["z"]["minute"] + th)], segs=64), "steel_polished")
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

    def half(y):  # left edge only: the crown widens the right side at 3 o'clock
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
    pitches = tr["bracelet_pitch_mm"]  # outer and centre links differ in the photo
    links, back = Geo(), Geo()
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
                        bent_box(links, x0, x1, y0, y1, za, zb, sy)
                    bent_box(back, -(hw_ - 0.3), hw_ - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                else:
                    bent_box(links, -ch, ch, y0, y1, za, zb + ds * br["centre_raise"], sy)
                y0 = y1 + gap
    add("bracelet_links", links, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(half(k_ * 0.25) for k_ in range(13)), 3), "lug_to_lug": round(2 * tip, 3)}  # case flanks
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "bracelet_rows": rows, "insert_prints": len(tr["insert_prints"]),
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
