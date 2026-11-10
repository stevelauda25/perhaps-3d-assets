"""watch_hamilton_h77616533: build the Hamilton H77616533 (Khaki Aviation X-Wind Auto Chrono 44 mm, black dial, three
subdials, tan leather strap) as a flat-backed front relief.

Params: spec (config/watches/hamilton-h77616533.json). Same frame, pose, 2.5D depth scale, materials and strap curl as
watch_hamilton_h76305530. Parts from the official render: a polished steel bezel with the engraved scale as black inlays
(traced), the case and lugs as one slab from the silhouette (narrower side per row, bottom lugs scaled to the official 54 mm
lug to lug), sword hour and minute hands (polished outline, lume), a white chrono seconds needle with an arrow tip, three
subdial hands with polished hubs, a fluted crown at 9 and two fluted pushers at 2 and 4, and a 22 mm strap with the house
curl. Photo maps: the dial with the printed inner rotating ring, subdials, numerals and day-date (hands removed), and the
strap leather with its rivets and stitching (pipeline/hamilton_h77616533_dial.py). Rebuild with --force after regenerating
the maps (not part of the fingerprint).
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

    # ---- case under the bezel, crystal ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), "steel_polished", smooth=True)
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- polished bezel with the engraved scale as black inlays ----
    bz = cfg["bezel"]
    ri, ro = tr["rings_mm"]["dial"], tr["rings_mm"]["bezel_out"]
    add("bezel", Geo().lathe([(ri, bz["z0"]), (ro, bz["z0"]), (ro, bz["top_z"] - bz["chamfer"]), (ro - bz["chamfer"], bz["top_z"]), (ri, bz["top_z"])], segs=240),
        "steel_polished", smooth=True)
    add("bezel_prints", plate(tr["bezel_prints"], bz["top_z"] - 0.05, bz["top_z"] + bz["print_raise"], P + "bezel_prints"), "print_black")

    # ---- dial with the printed inner ring, photo map on a planar UV about the hand pivot ----
    H = dm["half_size_mm"]
    me = Geo().lathe([(0, d["z"]), (ri, d["z"])], segs=192).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    add("dial", me, "dial", uv_of=lambda x, y, z: (0.5 + x / (2 * H), 0.5 + y / (2 * H)))

    # ---- hands at the render's time ----
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

    for name in ("hour", "minute"):  # sword: polished outline, lume body
        h, z = t[name], hs["z"][name]
        deg, prof = h["angle_deg"], h["outline_mm"]
        add("hand_" + name, plate([{"outer": [list(p) for p in loop(prof[:-1] + [[prof[-1][0], 0.001]], deg)], "holes": []}], z, z + th, P + "hand_" + name),
            "steel_polished", bevel=0.02)
        l0, l1 = h["lume_mm"]
        rs = [l0] + [r for r, _ in prof if l0 < r < l1] + [l1]
        add("hand_%s_lume" % name, Geo().prism(loop([[r, max(half_at(prof, r) - k, 0.02)] for r in rs], deg), z + th, z + th + 0.05), "lume")
    h = t["chrono"]  # white needle, arrow tip, short tail
    L, deg, z = h["length_mm"], h["angle_deg"], hs["z"]["chrono"]
    nw, (a0, aw) = h["half_width_mm"], h["arrow_mm"]
    add("hand_chrono", Geo().prism([rot(x, y, deg) for x, y in [(-nw, -h["tail_mm"]), (nw, -h["tail_mm"]), (nw, a0), (aw, a0), (0, L), (-aw, a0), (-nw, a0)]], z, z + th),
        "print_white", bevel=0.02)
    ring_r, mid_r, cap_r = tr["hub_radius_mm"]
    zh = hs["z"]["hour"]
    add("hub", Geo().lathe([(0, d["z"]), (ring_r, d["z"]), (ring_r, zh + th), (0, zh + th)], segs=64), "steel_polished", bevel=0.02)
    add("hub_ring", Geo().lathe([(0, zh + th), (mid_r, zh + th), (mid_r, z), (0, z)], segs=64), "steel_polished")
    add("hub_cap", Geo().lathe([(0, z + th), (cap_r, z + th), (cap_r, z + th + 0.1), (cap_r * 0.6, z + th + 0.18), (0, z + th + 0.18)], segs=48), "steel_polished")
    zs = hs["z"]["subdial"]
    for key, sd in tr["subdials"].items():  # small swords: polished outline, white body, polished hub
        cx, cy = sd["centre_mm"]
        L, tl, w, hb = sd["length_mm"], sd["tail_mm"], sd["half_mm"], sd["hub_mm"]
        prof = [[-tl, w * 0.45], [0.0, w * 0.45], [0.7 * L, w], [L, 0.001]]
        add("subdial_%s_hand" % key, Geo().prism(loop(prof, sd["angle_deg"], cx, cy), zs, zs + th), "steel_polished", bevel=0.01)
        add("subdial_%s_lume" % key, Geo().prism(loop([[0.25 * L, w * 0.5 - k * 0.6], [0.7 * L, w - k], [0.93 * L, 0.001]], sd["angle_deg"], cx, cy), zs + th, zs + th + 0.03), "print_white")
        add("subdial_%s_hub" % key, Geo().lathe([(0, d["z"]), (hb, d["z"]), (hb, zs + th + 0.05), (0, zs + th + 0.05)], segs=48, m=Matrix.Translation((cx, cy, 0))),
            "steel_polished", bevel=0.02)

    # ---- crown at 9 and pushers at 2 and 4: fluted cylinders on radial axes ----
    def fluted(name, angle, r0, r1, R0, teeth, depth, z, collar):
        a = math.radians(angle)
        star = [((R0 if i % 2 == 0 else R0 - depth) * math.cos(math.pi * i / teeth), (R0 if i % 2 == 0 else R0 - depth) * math.sin(math.pi * i / teeth))
                for i in range(teeth * 2)]
        u, dr = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
        m = Matrix((u, (0, 0, 1), dr)).transposed().to_4x4()
        m.translation = (0, 0, z)
        add(name + "_collar", Geo().lathe([(0, r0 - 0.6), (R0 * collar, r0 - 0.6), (R0 * collar, r0 + 0.5), (0, r0 + 0.5)], segs=48, m=m), "steel_polished", bevel=0.08)
        add(name, Geo().prism(star, r0 + 0.5, r1, m), "steel_polished", bevel=0.12)

    cw_ = cfg["crown"]
    crn = tr["crown"]
    fluted("crown", crn["angle_deg"], crn["r_mm"][0], crn["r_mm"][1], crn["radius_mm"], crn["teeth"], cw_["flute_depth"], cw_["z"], 0.6)
    for i, pu in enumerate(tr["pushers"]):
        fluted("pusher_%d" % i, pu["angle_deg"], pu["r_mm"][0], pu["r_mm"][1], pu["radius_mm"], cw_["pusher_teeth"], cw_["flute_depth"] * 0.7, cw_["z"], 0.7)

    # ---- case flanks, lobes and lugs: one slab from the silhouette (narrower side per row; the bottom half, whose lugs are
    #      least foreshortened, scaled to the official lug to lug and mirrored to the top) ----
    lg, tl = cfg["lug"], tr["lug"]
    tip, xi = tl["tip_mm"], tl["inner_x_mm"]
    k_y = tip / tl["photo_tips_mm"][1]
    prof = sorted((-y * k_y, w) for y, w in tr["case_half_width_by_y_mm"] if y <= 0 and -y * k_y <= tip)
    outline = [(xi, 0.0)] + [(w, y) for y, w in prof if w > xi] + [(xi, tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * min(1.0, max(0.0, (abs(y) - lg["slope_from_y"]) / (tip - lg["slope_from_y"])))
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("case_lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

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
    out = {"diameter": round(2 * ro, 3), "lug_to_lug": round(2 * tip, 3), "strap_width": round(2 * hw, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
