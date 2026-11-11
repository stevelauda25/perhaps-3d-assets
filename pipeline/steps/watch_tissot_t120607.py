"""watch_tissot_t120607: build the Tissot T120.607.11.041.00 (Seastar 2000 Professional 46 mm, blue wave dial, dark ceramic
insert, steel bracelet) as a flat-backed front relief.

Params: spec (config/watches/tissot-t120.607.11.041.00.json). Same frame, pose, 2.5D depth scale, materials and bracelet curl
as watch_hamilton_h82405130. Parts from the photo: a polished inner bezel lip, a dark ceramic insert with the traced white
prints as raised inlays, a steel bezel ring with a coin edge; applied indices with a polished frame and lume (round dots,
a triangle at 12, bars at 3, 9 and 6); a sword hour hand (lume blade, black cross guard and grip, stepped pommel), a baton
minute hand with an arrow tip and a stepped tail, a black seconds needle with a lume dot in a polished ring; a fluted crown
between two crown guards; brushed lugs and a three-column bracelet. The dial (wave relief, gradient, prints, date, flange
minute track) is the photo map from pipeline/tissot_t120607_dial.py. Rebuild with --force after regenerating the map (it is
not part of the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def inset(poly, k):
    """Shrink a convex polygon by k (mm) toward its inside along each edge's normal (k < 0 grows it)."""
    from mathutils import Vector, geometry as mg
    nn = len(poly)
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))
    s = 1 if area > 0 else -1
    lines = []
    for i in range(nn):
        (ax, ay), (bx_, by_) = poly[i], poly[(i + 1) % nn]
        ex, ey = bx_ - ax, by_ - ay
        ln = math.hypot(ex, ey)
        nx, ny = -s * ey / ln, s * ex / ln
        lines.append(((ax + k * nx, ay + k * ny), (bx_ + k * nx, by_ + k * ny)))
    out = []
    for i in range(nn):
        (p1, p2), (p3, p4) = lines[i - 1], lines[i]
        d1, d2 = Vector(p2) - Vector(p1), Vector(p4) - Vector(p3)
        den = d1.x * d2.y - d1.y * d2.x
        if abs(den) < 1e-9:  # parallel neighbours: keep the shifted point
            out.append(p3)
            continue
        t_ = ((p3[0] - p1[0]) * d2.y - (p3[1] - p1[1]) * d2.x) / den
        hit = Vector(p1) + d1 * t_
        out.append((hit.x, hit.y))
    return out


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    dm = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Tissot T120.607.11.041.00 front relief")
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

    # ---- case under the bezel, crystal ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), "steel_polished")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- bezel: polished inner lip, dark ceramic insert with white prints, steel ring with a coin edge ----
    bz = cfg["bezel"]
    centred = Matrix.Translation((bx, by, 0))
    ri, ro = rg["insert_in"], rg["insert_out"]
    add("bezel_lip", Geo().lathe([(rg["lip_in"], bz["lip_z"]), (ri, bz["insert_z"]), (ri, bz["z0"]), (rg["lip_in"], bz["z0"])], segs=192, m=centred),
        "steel_polished")
    add("insert", Geo().lathe([(ri, bz["z0"]), (ro, bz["z0"]), (ro, bz["insert_z"]), (ri, bz["insert_z"])], segs=240, m=centred), "insert_ceramic")
    add("insert_prints", plate(tr["insert_prints"], bz["insert_z"] - 0.05, bz["insert_z"] + bz["print_raise"], P + "insert_prints"), "print_white")
    n, depth, tip_r = tr["bezel_notches"]["count"], bz["scallop_depth"], rg["rim_out"]
    # coin edge: a polished ring inside the notch roots, and a notched band over almost its full height so the teeth show
    # in the silhouette as in the photo
    notch = bz["notch_fraction"]
    u = lambda f: max(0.0, 1 - ((2 * f - 1) / notch) ** 2) ** 0.5
    star = [(lambda a, f: (bx + (tip_r - depth * u(f)) * math.sin(a), by + (tip_r - depth * u(f)) * math.cos(a)))(2 * math.pi * k / (12 * n), (k % 12) / 12)
            for k in range(12 * n)]
    add("bezel_rim", Geo().lathe([(ro - 0.05, bz["z0"]), (tip_r - depth, bz["z0"]), (tip_r - depth, bz["rim_z"]), (ro - 0.05, bz["rim_z"])], segs=384, m=centred),
        "steel_polished", bevel=bz["rim_bevel"])
    add("bezel_coin_edge", plate([{"outer": star, "holes": [circle(tip_r - depth - 0.05, 384, bx, by)]}], bz["z0"] + bz["scallop_z"], bz["rim_z"] - 0.1,
                                 P + "bezel_coin_edge"), "steel_polished", bevel=bz["rim_bevel"])

    # ---- dial + rehaut (flange), photo map on a planar UV ----
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

    # ---- applied indices: polished frame, recessed lume; round dots, triangle at 12, bars at 3 9 6 ----
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
        outer = [rot(x, y, hr * 30 + turn) for x, y in inset(lp, -fw)]
        inner = [rot(x, y, hr * 30 + turn) for x, y in lp]
        shapes.append({"outer": [list(p) for p in outer], "holes": [[list(p) for p in inner]]})
        lume.prism(inner, z0, z1 - ix["lume_recess"])
    add("indices", plate(shapes, z0, z1, P + "indices"), "steel_polished")
    add("index_lume", lume, "lume")

    # ---- hands at the photo's time ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    k = tr["hand_outline_mm"]

    def hand(name, poly, deg, z, mat, h=th):
        add(name, Geo().prism([rot(x, y, deg) for x, y in poly], z, z + h), mat, bevel=0.02 if mat == "steel_polished" else None)

    def outlined(name, poly, deg, z, fill="hand_dark"):  # polished plate with a black top inset by the outline width
        hand(name, poly, deg, z, "steel_polished")
        hand(name + "_fill", inset(poly, k), deg, z + th, fill, 0.03)

    def tail(name, h, deg, z):  # stepped tail behind the hub: wide, then narrow, rounded ends
        r0, r1, w0, w1 = h["tail"]
        outlined(name, [(-w1, -r1), (w1, -r1), (w1, -r0), (w0, -r0), (w0, 0.3), (-w0, 0.3), (-w0, -r0), (-w1, -r0)], deg, z)

    # hour: sword. Body with a polished edge, lume blade, black cross guard and grip, stepped pommel
    h, z = t["hour"], hs["z"]["hour"]
    deg, L, sh, hw = h["angle_deg"], h["tip"], h["shoulder"], h["half"]
    n0, n1, gh = h["neck"]
    body = [(-gh, 0.0), (gh, 0.0), (gh, n0), (hw, n1), (hw, sh), (0, L), (-hw, sh), (-hw, n1), (-gh, n0)]
    outlined("hand_hour", body, deg, z)
    l0, l1, lw = h["lume"]
    hand("hand_hour_lume", [(-lw, l0), (lw, l0), (lw, sh - (hw - lw) * 0.6), (0, l1), (-lw, sh - (hw - lw) * 0.6)], deg, z + th, "lume", 0.05)
    a0, a1, aw = h["lume_low"]
    hand("hand_hour_lume_low", [(-aw, a0), (aw, a0), (aw, a1), (-aw, a1)], deg, z + th, "lume", 0.05)
    hand("hand_hour_grip", [(-h["grip_half"], 0.0), (h["grip_half"], 0.0), (h["grip_half"], h["guard"][0]), (-h["grip_half"], h["guard"][0])],
         deg, z + th, "steel_polished", 0.06)
    hand("hand_hour_grip_fill", inset([(-h["grip_half"], 0.0), (h["grip_half"], 0.0), (h["grip_half"], h["guard"][0]), (-h["grip_half"], h["guard"][0])], k),
         deg, z + th + 0.06, "hand_dark", 0.02)
    g0, g1, gw = h["guard"]
    guard = [(-gw, g0), (gw, g0), (gw, g1), (-gw, g1)]
    hand("hand_hour_guard", guard, deg, z + th, "steel_polished", 0.08)
    hand("hand_hour_guard_fill", inset(guard, k), deg, z + th + 0.08, "hand_dark", 0.02)
    tail("hand_hour_tail", h, deg, z)

    # minute: baton with an arrow tip, polished edge, lume; stepped tail
    h, z = t["minute"], hs["z"]["minute"]
    deg, L, sh, hw = h["angle_deg"], h["tip"], h["shoulder"], h["half"]
    outlined("hand_minute", [(-hw, 0.0), (hw, 0.0), (hw, sh), (0, L), (-hw, sh)], deg, z)
    l0, l1, lw = h["lume"]
    hand("hand_minute_lume", [(-lw, l0), (lw, l0), (lw, sh - (hw - lw) * 0.4), (0, l1), (-lw, sh - (hw - lw) * 0.4)], deg, z + th, "lume", 0.05)
    tail("hand_minute_tail", h, deg, z)
    ring_r = tr["hub_radius_mm"][0]  # the minute hand's root ring, outlined, bulging past the hand's sides
    outlined("hand_minute_ring", [(ring_r * math.sin(2 * math.pi * i / 48), ring_r * math.cos(2 * math.pi * i / 48)) for i in range(48)], 0.0, z)

    # seconds: black needle with a polished edge, lume dot in a polished ring, outlined tip past the dot
    h, z = t["seconds"], hs["z"]["seconds"]
    deg, nw = h["angle_deg"], h["half"]
    dr, (dl, dfr) = h["dot_r"], h["dot"]
    tip, tw = h["tip"]
    hand("hand_seconds", [(-nw, -h["tail"]), (nw, -h["tail"]), (nw, dr), (-nw, dr)], deg, z, "steel_polished")
    hand("hand_seconds_fill", [(-nw * 0.45, -h["tail"] + 0.05), (nw * 0.45, -h["tail"] + 0.05), (nw * 0.45, dr), (-nw * 0.45, dr)], deg, z + th, "hand_dark", 0.02)
    tipp = [(-tw * 0.8, dr), (tw * 0.8, dr), (tw, dr + dfr), (tw * 0.6, tip - 0.1), (0, tip), (-tw * 0.6, tip - 0.1), (-tw, dr + dfr)]
    outlined("hand_seconds_tip", tipp, deg, z)
    m = Matrix.Translation((*rot(0, dr, deg), 0))
    add("hand_seconds_ring", Geo().lathe([(0, z), (dfr, z), (dfr, z + th), (0, z + th)], segs=48, m=m), "steel_polished", bevel=0.02)
    add("hand_seconds_lume", Geo().lathe([(0, z + th), (dl, z + th), (dl, z + th + 0.05), (0, z + th + 0.05)], segs=48, m=m), "lume")
    cap_r = tr["hub_radius_mm"][1]
    add("hub_post", Geo().lathe([(0, d["z"]), (cap_r * 1.5, d["z"]), (cap_r * 1.5, z), (0, z)], segs=48), "hand_dark")
    zc = z + th
    add("hub_cap", Geo().lathe([(0, zc), (cap_r, zc), (cap_r, zc + 0.1), (cap_r * 0.6, zc + 0.18), (0, zc + 0.18)], segs=48), "steel_polished")

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
    add("crown_guards", g, "steel_polished", bevel=cfg["crown_guard"]["bevel"])

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
    pitches = tr["bracelet_pitch_mm"]
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
