"""watch_hamilton_h76709530: build the Hamilton H76709530 (Khaki Aviation Pilot Pioneer Mechanical Bronze 43 mm, black dial,
dark brown leather strap) as a flat-backed front relief.

Params: spec (config/watches/hamilton-h76709530.json). Same frame, pose, 2.5D depth scale and strap curl as
watch_hamilton_h77616533; bronze instead of steel (colours from the official render). Parts from the render: a bronze bezel
with a fine scalloped grip edge around a glossy black insert with the beige prints as traced inlays; the case and lugs as one
slab from the silhouette; bronze hour (baton with a lume bulb) and minute hands with lume; a bronze small seconds hand with
its hub; a large fluted crown at 3 and a 20 mm strap with the house curl. Photo maps: the grained dial with numerals, railway
track and small seconds ring (hands removed), and the strap leather (pipeline/hamilton_h76709530_dial.py). Rebuild with
--force after regenerating the maps (not part of the fingerprint).
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
                me.materials.append(mats[cfg.get("bevel_material", "steel_polished")])
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            if polished_bevel:
                m.material = 1
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if not name.startswith("strap"):
            o.scale = (1, 1, ds)
        return o

    # ---- case under the bezel, crystal ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), "bronze_polished", smooth=True)
    rg = tr["bezel_rings_mm"]
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (rg["insert_in"], cr["z0"]), (rg["insert_in"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- bezel: glossy black insert with beige prints, bronze ring with a scalloped grip edge ----
    bz = cfg["bezel"]
    ri, ro = rg["insert_in"], rg["insert_out"]
    add("insert", Geo().lathe([(ri, bz["z0"]), (ro, bz["z0"]), (ro, bz["insert_z"]), (ri, bz["insert_z"])], segs=240), "insert_black")
    add("insert_prints", plate(tr["insert_prints"], bz["insert_z"] - 0.05, bz["insert_z"] + bz["print_raise"], P + "insert_prints"), "print_beige")
    n, depth, tip_r = tr["bezel_notches"]["count"], bz["scallop_depth"], rg["rim_out"]
    u = lambda f_: (1 - (2 * f_ - 1) ** 2) ** 0.5
    star = [(lambda a, f_: ((tip_r - depth * u(f_)) * math.sin(a), (tip_r - depth * u(f_)) * math.cos(a)))(2 * math.pi * k_ / (12 * n), (k_ % 12) / 12)
            for k_ in range(12 * n)]
    ring_in = [((ro - 0.05) * math.sin(2 * math.pi * k_ / 192), (ro - 0.05) * math.cos(2 * math.pi * k_ / 192)) for k_ in range(192)]
    add("bezel_rim", plate([{"outer": [list(p) for p in star], "holes": [[list(p) for p in ring_in]]}], bz["z0"], bz["rim_z"], P + "bezel_rim"),
        "bronze_polished", bevel=bz["rim_bevel"])

    # ---- grained dial with the railway track, photo map on a planar UV about the hand pivot ----
    H = dm["half_size_mm"]
    me = Geo().lathe([(0, d["z"]), (rg["dial"], d["z"]), (ri, d["rehaut_z"])], segs=192).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    add("dial", me, "dial", uv_of=lambda x, y, z: (0.5 + x / (2 * H), 0.5 + y / (2 * H)))

    # ---- hands at the render's time: bronze outline, beige lume ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    k = tr["hand_outline_mm"]

    def loop(pairs, deg, cx=0.0, cy=0.0):
        pts = [rot(v, r, deg) for r, v in pairs] + [rot(-v, r, deg) for r, v in pairs[::-1]]
        return [(x + cx, y + cy) for x, y in pts]

    def half_at(prof, r):
        for (ra, va), (rb, vb) in zip(prof, prof[1:]):
            if ra <= r <= rb:
                return va + (vb - va) * (r - ra) / (rb - ra)
        return 0.0

    for name in ("hour", "minute"):
        h, z = t[name], hs["z"][name]
        deg, prof = h["angle_deg"], h["outline_mm"]
        add("hand_" + name, plate([{"outer": [list(p) for p in loop(prof[:-1] + [[prof[-1][0], 0.001]], deg)], "holes": []}], z, z + th, P + "hand_" + name),
            "bronze_polished", bevel=0.02)
        l0, l1 = h["lume_mm"]
        rs = [l0] + [r for r, _ in prof if l0 < r < l1] + [l1]
        add("hand_%s_lume" % name, Geo().prism(loop([[r, max(half_at(prof, r) - k, 0.02)] for r in rs], deg), z + th, z + th + 0.05), "lume")
    collar_r, cap_r = tr["hub_radius_mm"]
    zh, zm_ = hs["z"]["hour"], hs["z"]["minute"]
    add("hub", Geo().lathe([(0, d["z"]), (collar_r, d["z"]), (collar_r, zm_ + th), (0, zm_ + th)], segs=64), "bronze_polished", bevel=0.02)
    add("hub_cap", Geo().lathe([(0, zm_ + th), (cap_r, zm_ + th), (cap_r, zm_ + th + 0.12), (cap_r * 0.6, zm_ + th + 0.2), (0, zm_ + th + 0.2)], segs=48),
        "steel_polished")
    sd = tr["small_seconds"]  # needle down-left, lozenge counterweight up-right, bronze hub
    cx, cy = sd["centre_mm"]
    zs = hs["z"]["small_seconds"]
    L, tl, w, hb = sd["length_mm"], sd["tail_mm"], sd["half_mm"], sd["hub_mm"]
    prof = [[-tl, 0.001], [-tl * 0.75, w * 0.7], [-tl * 0.45, w * 0.35], [0.0, 0.06], [L * 0.85, 0.05], [L, 0.001]]
    add("small_seconds_hand", Geo().prism(loop(prof, sd["angle_deg"], cx, cy), zs, zs + th), "bronze_polished", bevel=0.01)
    add("small_seconds_hub", Geo().lathe([(0, d["z"]), (hb, d["z"]), (hb, zs + th + 0.05), (0, zs + th + 0.05)], segs=48, m=Matrix.Translation((cx, cy, 0))),
        "bronze_polished", bevel=0.02)

    # ---- crown at 3: neck and fluted cylinder on a radial axis ----
    cw_ = cfg["crown"]
    crn = tr["crown"]
    a = math.radians(crn["angle_deg"])
    R0, teeth = crn["radius_mm"], crn["teeth"]
    star = [((R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.cos(math.pi * i / teeth), (R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.sin(math.pi * i / teeth))
            for i in range(teeth * 2)]
    u_, dr = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
    m = Matrix((u_, (0, 0, 1), dr)).transposed().to_4x4()
    m.translation = (0, 0, cw_["z"])
    r0, r1 = crn["r_mm"]
    add("crown_neck", Geo().lathe([(0, r0 - 1.0), (R0 * 0.5, r0 - 1.0), (R0 * 0.5, r0 + 0.6), (0, r0 + 0.6)], segs=48, m=m), "bronze_polished", smooth=True)
    add("crown", Geo().prism(star, r0 + 0.6, r1, m), "bronze_polished", bevel=0.15)

    # ---- case flanks and lugs: one slab from the silhouette (left edge, the crown is at 3; top and bottom averaged) ----
    lg, tl_ = cfg["lug"], tr["lug"]
    tip, xi = tl_["tip_mm"], tl_["inner_x_mm"]
    sil = {p[0]: p[1] for p in tr["case_half_width_by_y_mm"]}
    ys = [k_ * 0.25 for k_ in range(int(tip / 0.25) + 1)]
    outline = [(xi, 0.0)] + [((sil[round(y, 2)] + sil[round(-y, 2)]) / 2, y) for y in ys if round(y, 2) in sil and round(-y, 2) in sil] + [(xi, tip)]
    outline = [(x, y) for x, y in outline if x >= xi]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * min(1.0, max(0.0, (abs(y) - lg["slope_from_y"]) / (tip - lg["slope_from_y"])))
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("case_lugs", g, "bronze_brushed", bevel=lg["bevel"], polished_bevel=True)

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
    out = {"diameter": round(2 * tip_r, 3), "lug_to_lug": round(2 * tip, 3), "strap_width": round(2 * hw, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
