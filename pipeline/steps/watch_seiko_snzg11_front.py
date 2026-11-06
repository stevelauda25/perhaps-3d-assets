"""watch_seiko_snzg11_front: build the Seiko 5 SNZG11J1 as a flat-backed front relief (like the other GLBs in models/watches/).

Params: spec (config/watches/seiko-snzg11j1.json). Same frame, pose, 2.5D depth scale, glass and curl as watch_seiko_front
(SNK607K1), whose helpers it reuses. This model differs in the parts: matte (bead-blasted) case with a wide flat bezel, all
dial print in the dial map (no applied parts), sword hour and minute hands with lume inlays, a seconds needle with a red
arrowhead and red tip, and a nylon NATO strap textured from the photo (strap atlas from pipeline/seiko_snzg11_dial.py),
rolled under with the house 7 mm curl. Rebuild with --force after regenerating the maps (they are not in the fingerprint).
"""
import json
import math

import bmesh
import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    scene = bpy.context.scene
    coll = bpy.data.collections.new("WATCH | Seiko 5 SNZG11J1 front relief")
    scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    d, st = cfg["dial"], cfg["strap"]
    mats["dial"] = photo_material("dial_photo", ROOT / cfg["dial_map"], d["roughness"])
    mats["strap"] = photo_material("strap_photo", ROOT / st["map"], st["roughness"])

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"])
    pose.scale = (0.001,) * 3
    ds = cfg["pose"]["depth_scale"]

    def add(name, geo, mat, bevel=None, flat_depth=True):
        me = geo.mesh(P + name, True if bevel else None) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if bevel:
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if flat_depth:
            o.scale = (1, 1, ds)
        return o

    # ---- case (wide flat bezel), black gasket ring, crystal ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), c["material"])
    gk = cfg["gasket"]
    add("gasket", Geo().lathe([(gk["r_in"], gk["z0"]), (gk["r_out"], gk["z0"]), (gk["r_out"], gk["z1"]), (gk["r_in"], gk["z1"])], segs=192), "gasket_black")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial: photo map (all print, track, logo, day-date) on a planar UV ----
    me = Geo().lathe([(0, d["z"]), (tr["crystal_ring"]["radius_mm"], d["z"])], segs=192).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    uv = me.uv_layers.new(name="UVMap")
    H = tr["crystal_ring"]["radius_mm"]
    for loop in me.loops:
        x, y, _ = me.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
    add("dial", me, "dial")

    # ---- hands at the photo's time ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    turn = lambda poly, deg: [rot(x, y, deg) for x, y in poly]
    for name in ("hour", "minute"):
        h, s = t[name], hs[name]
        L, hw, deg, z, pt = h["length_mm"], h["half_width_mm"], h["angle_deg"], hs["z"][name], hs["point_mm"]
        add("hand_" + name, Geo().prism(turn([(-hw, 0), (hw, 0), (hw, L - pt), (0, L), (-hw, L - pt)], deg), z, z + th), "hand_steel", bevel=0.03)
        li, a = hw - hs["frame"], s["lume_from"]
        lume = [(-li, a), (li, a), (li, L - pt), (0, L - hs["frame"] * 2.2), (-li, L - pt)]
        add("hand_%s_lume" % name, Geo().prism(turn(lume, deg), z + th, z + th + 0.03), "lume")
        add("hand_%s_collet" % name, Geo().lathe([(0, z), (s["collet_r"], z), (s["collet_r"], z + th), (0, z + th)], segs=48), "hand_steel")
    h, s = t["seconds"], hs["seconds"]
    L, deg, z, nw = h["length_mm"], h["angle_deg"], hs["z"]["seconds"], s["half_width"]
    a0, a1 = h["arrow_from_to_mm"]
    add("hand_seconds", Geo().prism(turn([(-nw, -s["tail"]), (nw, -s["tail"]), (nw, a0), (-nw, a0)], deg), z, z + th), "hand_steel")
    red = Geo().prism(turn([(-s["arrow_half_width"], a0), (s["arrow_half_width"], a0), (0, a1)], deg), z, z + th)
    red.prism(turn([(-nw, a0), (nw, a0), (nw, L - 0.15), (0, L), (-nw, L - 0.15)], deg), z, z + th)
    add("hand_seconds_red", red, "seconds_red")
    hb = hs["hub"]
    add("hub", Geo().lathe([(0, d["z"]), (hb["radius"], d["z"]), (hb["radius"], z), (0, z)], segs=48), "hand_steel")
    zc = z + th
    add("hub_cap", Geo().lathe([(0, zc), (hb["cap_radius"], zc), (hb["cap_radius"], zc + 0.12), (hb["cap_radius"] * 0.6, zc + 0.2), (0, zc + 0.2)], segs=48), "gasket_black")

    # ---- crown: neck + fluted cylinder on a radial axis at the traced angle (3 o'clock) ----
    cw = cfg["crown"]
    a = math.radians(math.degrees(math.atan2(*tr["crown_box"]["centre_mm"])) % 360)
    rr = lambda i: cw["radius"] if i % 2 == 0 else cw["radius"] - cw["flute_depth"]
    star = [(rr(i) * math.cos(math.pi * i / cw["teeth"]), rr(i) * math.sin(math.pi * i / cw["teeth"])) for i in range(cw["teeth"] * 2)]
    u, dr = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
    m = Matrix((u, (0, 0, 1), dr)).transposed().to_4x4()
    m.translation = (0, 0, cw["z"])
    add("crown", Geo().prism(star, cw["r_from"], cw["r_to"], m), cw["material"], bevel=0.15)
    nk = cw["neck"]
    add("crown_neck", Geo().lathe([(0, nk["r_from"]), (nk["radius"], nk["r_from"]), (nk["radius"], cw["r_from"]), (0, cw["r_from"])], segs=48, m=m), cw["material"])

    # ---- lugs from the traced silhouette (left/right and top/bottom averaged: the photo is turned slightly) ----
    lg = cfg["lug"]
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}

    def half(y):
        ys = [sil[k] for k in (round(y, 2), round(-y, 2)) if k in sil]
        return sum((p[2] - p[1]) / 2 for p in ys) / len(ys)

    tip, inner = tr["lug_tip_mm"]["mean"], tr["lug_inner_x_mm"]
    # the outer edge is straight in the photo: least-squares line through the traced edge, the case circle inside it
    fy = [k * 0.25 for k in range(int(lg["fit_from_y"] * 4), int((tip - 0.6) * 4) + 1)]
    fx = [half(y) for y in fy]
    my_, mx_ = sum(fy) / len(fy), sum(fx) / len(fx)
    k_ = sum((y - my_) * (x - mx_) for y, x in zip(fy, fx)) / sum((y - my_) ** 2 for y in fy)
    rc = max(r for r, _ in c["profile_rz"])
    line = lambda y: mx_ + k_ * (y - my_)
    y0 = next(y / 20 for y in range(int(rc * 20) - 1, 0, -1) if line(y / 20) <= math.sqrt(rc * rc - (y / 20) ** 2))  # line meets the case
    # inner side: up the lug gap, then an arc just outside the bezel's inner edge (never shows through the crystal) down to y0
    ri = lg["inner_arc_r"]
    a_in, a_out = math.atan2(math.sqrt(ri * ri - inner * inner), inner), math.atan2(y0, math.sqrt(ri * ri - y0 * y0))
    arc = [(ri * math.cos(a_in + (a_out - a_in) * k / 24), ri * math.sin(a_in + (a_out - a_in) * k / 24)) for k in range(25)]
    steps = [y0 + k * 0.25 for k in range(int((tip - y0) / 0.25) + 1)]
    outline = [(inner, tip)] + arc + [(line(y), y) for y in steps]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * max(abs(y) - y0, 0) / (tip - y0)
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, lg["material"], bevel=lg["bevel"])

    # ---- NATO strap: one band per side, photo atlas, straight to the lug tips then the house curl ----
    lay = json.loads((ROOT / st["map"]).with_suffix(".json").read_text())
    hw, za, zb, ch = st["half_width"], ds * st["z0"], ds * st["z1"], st["edge_chamfer"]
    zm, R, bend_y = (za + zb) / 2, st["bend_radius"], tip + st.get("bend_after_tip", 0.0)
    end_y = bend_y + R * st["arc_over_radius"]

    def bend(s, z):
        if s <= bend_y:
            return s, z
        a_, r_ = (s - bend_y) / R, R + z - zm
        return bend_y + r_ * math.sin(a_), zm - R + r_ * math.cos(a_)

    def v_of(s, side):
        """Atlas v for a point s mm along the strap; mirrored outside the photographed stretch."""
        L_, ts, rc_ = lay[side], tr["lug_tip_mm"][side], tr["case"]["radius_mm"]
        s = rc_ + (s - rc_) * (ts - rc_) / (tip - rc_) if s <= tip else s - tip + ts  # the photo's own case edge and lug tip
        a_, n = L_["s_from_mm"], L_["s_to_mm"] - L_["s_from_mm"]
        k = (s - a_) % (2 * n)
        f = (k if k <= n else 2 * n - k) / n  # 0 at s_from, 1 at s_to
        ft = lay["top_fraction"]
        return 1 - ft * (1 - f) if side == "top" else (1 - ft) * (1 - f)

    ring = [(-hw, za + ch), (-hw + ch, za), (hw - ch, za), (hw, za + ch), (hw, zb - ch), (hw - ch, zb), (-hw + ch, zb), (-hw, zb - ch)]
    cuts = [st["from_y"] + k * 0.4 for k in range(int((end_y - st["from_y"]) / 0.4) + 1)] + [end_y]
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    for side, sy in (("top", 1), ("bottom", -1)):
        rings = []
        for s in cuts:
            row = []
            for x, z in ring:
                y, z_ = bend(s, z)
                vert = bm.verts.new((x, sy * y, z_))
                row.append((vert, ((x + hw) / (2 * hw), v_of(s, side))))
            rings.append(row)
        faces = [[rings[k][i], rings[k][(i + 1) % 8], rings[k + 1][(i + 1) % 8], rings[k + 1][i]] for k in range(len(cuts) - 1) for i in range(8)]
        faces += [rings[0], rings[-1][::-1]]
        for f in faces:
            face = bm.faces.new([v for v, _ in f])
            face.smooth = True
            for loop, (_, uv_) in zip(face.loops, f):
                loop[uvl].uv = uv_
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(P + "strap")
    bm.to_mesh(me)
    bm.free()
    add("strap", me, "strap", flat_depth=False)

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "lug_to_lug": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    assert hw < inner, "strap wider than the lug gap"
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    y_end, z_end = bend(end_y, zm)
    return {"measured_mm": out, "lug_tip_y_mm": tip, "strap_front_end_mm": round(y_end, 2), "strap_drop_mm": round(zm - z_end, 2),
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
