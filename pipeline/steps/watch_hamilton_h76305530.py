"""watch_hamilton_h76305530: build the Hamilton H76305530 (Khaki Aviation Pilot Auto 39 mm, black dial, brown leather strap)
as a flat-backed front relief.

Params: spec (config/watches/hamilton-h76305530.json). Same frame, pose, 2.5D depth scale, materials and strap curl as
watch_orient_ra_ac0f06l10b, whose lug, crown and strap methods it follows. Parts from the photo: a brushed round case with a
wide flat bezel and a polished inner bevel down to the chapter ring; skeleton sword hands (polished outline, lume body, open
tip on the hour hand and open root on the minute hand, polished paddle tails); a seconds needle with a lume arrow and a
polished ring on its tail; a large fluted crown; brushed lugs with polished edges and a 20 mm strap with the house curl. Photo
maps: the dial with its chapter ring (hands removed) and the strap leather resampled row by row, each side from its own photo
strap (pipeline/hamilton_h76305530_dial.py). Rebuild with --force after regenerating the maps (not part of the fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    dm = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    sm = json.loads((ROOT / cfg["strap_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | " + cfg["model"] + " front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    d, st = cfg["dial"], cfg["strap"]
    mats["dial"] = photo_material("dial_photo", ROOT / cfg["dial_map"], d["roughness"])
    mats["strap_leather"] = photo_material("strap_photo", ROOT / cfg["strap_map"], st["roughness"])
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

    def add(name, geo, mat, bevel=None, smooth=None, uv_of=None, polished_bevel=False):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured and not uv_of:  # planar UV in mm / tile, lines along model Y
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
        if not name.startswith("strap"):
            o.scale = (1, 1, ds)
        return o

    # ---- brushed case and flat bezel, polished inner bevel down to the chapter ring, crystal ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), "steel_brushed", smooth=True)
    bv = c["bevel_rz"]
    add("case_bevel", Geo().lathe([tuple(p) for p in bv], segs=192), "steel_polished", smooth=True)
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial + chapter ring sloping up to the crystal, photo map on a planar UV about the hand pivot ----
    H = dm["half_size_mm"]
    me = Geo().lathe([(0, d["z"]), (tr["rings_mm"]["dial"], d["z"]), (d["rehaut_r"], d["rehaut_z"])], segs=192).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    add("dial", me, "dial", uv_of=lambda x, y, z: (0.5 + x / (2 * H), 0.5 + y / (2 * H)))

    # ---- hands at the photo's time: polished outline plate with the skeleton window as a hole, lume body, paddle tail ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    k = tr["hand_outline_mm"]

    def loop(pairs, deg):
        return [list(rot(v, r, deg)) for r, v in pairs] + [list(rot(-v, r, deg)) for r, v in pairs[::-1]]

    def half_at(prof, r):
        for (ra, va), (rb, vb) in zip(prof, prof[1:]):
            if ra <= r <= rb:
                return va + (vb - va) * (r - ra) / (rb - ra)
        return 0.0

    for name in ("hour", "minute"):
        h, z = t[name], hs["z"][name]
        deg, prof, wnd = h["angle_deg"], h["outline_mm"], h["window_mm"]
        hole = loop(wnd[:-1] + [[wnd[-1][0], 0.001]], deg)
        add("hand_" + name, plate([{"outer": loop(prof[:-1] + [[prof[-1][0], 0.001]], deg), "holes": [hole]}], z, z + th, P + "hand_" + name),
            "steel_polished", bevel=0.02)
        l0, l1 = h["lume_mm"]
        rs = [l0] + [r for r, _ in prof if l0 < r < l1] + [l1]
        add("hand_%s_lume" % name, Geo().prism([tuple(p) for p in loop([[r, max(half_at(prof, r) - k, 0.02)] for r in rs], deg)], z + th, z + th + 0.05), "lume")
        tl, tw = h["tail_mm"]
        add("hand_%s_tail" % name, Geo().prism([rot(x, y, deg) for x, y in [(-tw, 0.0), (tw, 0.0), (tw, -tl + tw), (tw * 0.7, -tl), (-tw * 0.7, -tl), (-tw, -tl + tw)]], z, z + th),
            "steel_polished", bevel=0.03)
    ring_r, collar_r, cap_r = tr["hub_radius_mm"]
    zh = hs["z"]["hour"]
    add("hand_hour_ring", Geo().lathe([(0, zh), (ring_r, zh), (ring_r, zh + th), (0, zh + th)], segs=64), "steel_polished", bevel=0.02)
    zm_ = hs["z"]["minute"]
    add("hub_collar", Geo().lathe([(0, d["z"]), (collar_r, d["z"]), (collar_r, zm_ + th), (0, zm_ + th)], segs=64), "hand_dark")

    h = t["seconds"]  # polished needle, lume arrow with a polished edge, polished ring on the tail
    L, tail, deg, z = h["length_mm"], h["tail_mm"], h["angle_deg"], hs["z"]["seconds"]
    nw = h["rod_half_mm"]  # the polished rod; half_width_mm is the zone cut from the dial map (rod plus its glow)
    a0, aw = h["arrow_mm"]
    ro, ri = h["ring_mm"]
    add("hand_seconds", Geo().prism([rot(x, y, deg) for x, y in [(-nw, -tail + ri), (nw, -tail + ri), (nw, a0), (-nw, a0)]], z, z + th), "steel_polished", bevel=0.02)
    add("hand_seconds_arrow", Geo().prism([rot(x, y, deg) for x, y in [(-aw, a0), (aw, a0), (0, L)]], z, z + th), "steel_polished", bevel=0.02)
    add("hand_seconds_lume", Geo().prism([rot(x, y, deg) for x, y in [(-aw + k, a0 + k), (aw - k, a0 + k), (0, L - 2.2 * k)]], z + th, z + th + 0.04), "lume")
    ring = [list(rot(ro * math.sin(2 * math.pi * i / 48), -tail + ro * math.cos(2 * math.pi * i / 48), deg)) for i in range(48)]
    hole = [list(rot(ri * math.sin(2 * math.pi * i / 48), -tail + ri * math.cos(2 * math.pi * i / 48), deg)) for i in range(48)]
    add("hand_seconds_ring", plate([{"outer": ring, "holes": [hole]}], z, z + th, P + "hand_seconds_ring"), "steel_polished", bevel=0.02)
    zc = z + th
    add("hub_cap", Geo().lathe([(0, zm_ + th), (cap_r, zm_ + th), (cap_r, zc + 0.1), (cap_r * 0.6, zc + 0.18), (0, zc + 0.18)], segs=48), "steel_polished")

    # ---- crown on the 3 o'clock axis: neck, fluted body, rounded end cap ----
    cw_ = cfg["crown"]
    R0, teeth = tr["crown"]["radius_mm"], tr["crown"]["teeth"]
    star = [((R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.cos(math.pi * i / teeth),
             (R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.sin(math.pi * i / teeth)) for i in range(teeth * 2)]
    m = Matrix(((0, -1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_4x4()  # local z along +x, local y up
    m.translation = (0.0, 0.0, cw_["z"])
    r1, r2 = cw_["r_from"], tr["crown"]["to_mm"] - cw_["cap"]
    add("crown_neck", Geo().lathe([(0, c["profile_rz"][2][0] - 1.0), (R0 * 0.55, c["profile_rz"][2][0] - 1.0), (R0 * 0.55, r1 + 0.1), (0, r1 + 0.1)], segs=48, m=m),
        "steel_polished", smooth=True)
    add("crown", Geo().prism(star, r1, r2, m), "steel_polished", bevel=0.12)
    cap = [(0, r2)] + [(R0 * 0.95 * math.cos(a), r2 + cw_["cap"] * math.sin(a)) for a in (i * math.pi / 2 / 6 for i in range(7))]
    add("crown_cap", Geo().lathe(cap[:-1] + [(0, r2 + cw_["cap"])], segs=48, m=m), "steel_polished", smooth=True)

    # ---- lugs: outline by depth from the tip (top and bottom averaged), mirrored to all four, brushed top, polished edge ----
    lg, tl = cfg["lug"], tr["lug"]
    tip, xi = tl["tip_mm"], tl["inner_x_mm"]
    R_case = c["profile_rz"][2][0]
    outer = [(w, tip - dd) for dd, w in tl["half_width_by_depth_mm"] if math.hypot(w, tip - dd) > R_case - lg["into_case"]]
    outer = [(lg["tip_outer_x"], tip)] + outer
    last = outer[-1]
    poly = [(xi, tip)] + outer + [(xi, last[1])]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * min(1.0, max(0.0, (abs(y) - lg["slope_from_y"]) / (tip - lg["slope_from_y"])))
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in poly], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

    # ---- leather strap: straight between the lugs, house curl from the tips; each side samples its own photo strap, lug
    #      tips aligned, folded back and forth over its flat leather ----
    hw = xi - st["edge_inset"]
    zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], tip + st["bend_after_tip"]
    box = curl(bend_y, R, zm)
    g = Geo()
    for sy in (1, -1):
        box(g, -hw, hw, st["start_y"], bend_y + R * st["arc_over_radius"], ds * st["z0"], ds * st["z1"], sy)
    Sp, n_rows = sm["scale_px_per_mm"], sm["size_px"][1]
    sides = {}
    for key, tip_px, half_u in (("top", sm["lug_tips_px"][0], 0.0), ("bottom", sm["lug_tips_px"][1], 0.5)):
        rows = sm["rows_px"][key]
        sides[key] = (tip + abs(rows[0] - tip_px) / Sp, tip + abs(rows[-1] - tip_px) / Sp, len(rows), half_u)

    def strap_uv(x, y, z):
        lo, hi, n, half_u = sides["top" if y > 0 else "bottom"]
        u = min(max((x + hw) / (2 * hw), st["uv_inset"]), 1 - st["uv_inset"])  # side walls take the strap's own edge pixels
        s = abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
        k_, w = divmod(s - lo, hi - lo)  # under the case and lugs the strip is folded, not clamped
        sp = lo + w if int(k_) % 2 == 0 else hi - w
        row = (sp - lo) / (hi - lo) * (n - 1)
        return half_u + 0.5 * u, 1 - (row + 0.5) / n_rows
    add("strap", g, "strap_leather", bevel=st["bevel"], uv_of=strap_uv)

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "lug_to_lug": round(2 * tip, 3), "strap_width": round(2 * hw, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
