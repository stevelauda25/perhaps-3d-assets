"""watch_hamilton_h76419931: build the Hamilton H76419931 (Khaki Aviation Pilot Pioneer Mechanical 36 x 33 mm, black dial,
grey NATO strap) as a flat-backed front relief.

Params: spec (config/watches/hamilton-h76419931.json). Same frame, pose, 2.5D depth scale, materials and strap curl as
watch_hamilton_h70515137. Parts from the official render: a brushed cushion case as one slab from the render's outline (top
and bottom kept as drawn, not centred on the pivot) with a polished edge, a polished ring round the crystal; a lance hour hand
and needle minute hand (polished outline, beige lume), a polished seconds needle; a fluted crown at 3; and a grey NATO strap
that runs under the case and rolls away with the house curl past the case at 12 and 6. Photo maps: the dial (hands removed)
and the strap weave (pipeline/hamilton_h76419931_dial.py). Rebuild with --force after regenerating the maps (not part of the
fingerprint).
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
    sm = json.loads((ROOT / cfg["strap_map"]).with_suffix(".json").read_text())
    st = cfg["strap"]
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

    def add(name, geo, mat, bevel=None, polished_bevel=False, smooth=None, uv_of=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if uv_of:
            uv = me.uv_layers.new(name="UVMap")
            for loop_ in me.loops:
                uv.data[loop_.index].uv = uv_of(*me.vertices[loop_.vertex_index].co)
        elif mat in textured:  # planar UV in mm / tile, lines along the bracelet (model Y)
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
        if not name.startswith("strap"):
            o.scale = (1, 1, ds)
        return o

    # ---- dial (the polished ring round it is in the map), crystal, polished lip ----
    c, rg = cfg["case"], tr["rings_mm"]
    H = dm["half_size_mm"]
    me = Geo().lathe([(0, d["z"]), (rg["dial"], d["z"]), (rg["bezel_in"], d["rehaut_z"])], segs=192).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    add("dial", me, "dial", uv_of=lambda x, y, z: (0.5 + x / (2 * H), 0.5 + y / (2 * H)))
    cr = cfg["crystal"]
    ri = rg["bezel_in"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (ri, cr["z0"]), (ri, cr["z1"]), (0, cr["z1"])], segs=192), "crystal")
    add("bezel_lip", Geo().lathe([(ri, d["rehaut_z"]), (c["lip_out"], d["rehaut_z"]), (c["lip_out"], c["lip_z"]), (ri + 0.15, c["lip_z"])], segs=192),
        "steel_polished", smooth=True)

    # ---- cushion case: one slab from the render's outline, brushed top with a polished edge, open over the dial. Built as
    #      quads between the hole circle and the outline, sampled on the same rays (a triangulated cap with a hole shades
    #      with streaks along its long triangles) ----
    rows = tr["case_left_by_y_mm"]  # [y, half width], top to bottom
    outline = [(w, y) for y, w in rows] + [(-w, y) for y, w in rows[::-1]]

    def ray_hit(a):
        dx, dy = math.sin(a), math.cos(a)
        best = None
        for (x0, y0), (x1, y1) in zip(outline, outline[1:] + outline[:1]):
            ex, ey = x1 - x0, y1 - y0
            den = dx * ey - dy * ex
            if abs(den) < 1e-12:
                continue
            t_ = (x0 * ey - y0 * ex) / den
            u = (x0 * dy - y0 * dx) / den
            if t_ > 0 and -1e-9 <= u <= 1 + 1e-9:
                best = t_ if best is None else max(best, t_)
        return best

    n_ = 360
    r_in = c["lip_out"] - 0.05
    verts, faces = [], []
    for i in range(n_):
        a = 2 * math.pi * i / n_
        ro_ = ray_hit(a)
        for r_, z_ in ((r_in, 0.0), (ro_, 0.0), (ro_, c["top_z"]), (r_in, c["top_z"])):
            verts.append((r_ * math.sin(a), r_ * math.cos(a), z_))
    for i in range(n_):
        j = (i + 1) % n_
        a0, b0 = 4 * i, 4 * j
        for k_ in range(4):  # bottom, outer wall, top, inner wall
            faces.append((b0 + k_, a0 + k_, a0 + (k_ + 1) % 4, b0 + (k_ + 1) % 4))
    me = bpy.data.meshes.new(P + "case")
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    if sum(p_.normal.z * (1 if p_.center.z > c["top_z"] / 2 else 0) for p_ in me.polygons) < 0:
        for p_ in me.polygons:
            p_.flip()
        me.update()
    add("case", me, "steel_brushed", bevel=c["bevel"], polished_bevel=True)

    # ---- hands at the render's time ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    k = tr["hand_outline_mm"]

    def loop(pairs, deg):
        return [rot(v, r, deg) for r, v in pairs] + [rot(-v, r, deg) for r, v in pairs[::-1]]

    def half_at(prof, r):
        for (ra, va), (rb, vb) in zip(prof, prof[1:]):
            if ra <= r <= rb:
                return va + (vb - va) * (r - ra) / (rb - ra)
        return 0.0

    for name in ("hour", "minute"):  # polished outline, beige lume
        h, z = t[name], hs["z"][name]
        deg, prof = h["angle_deg"], h["outline_mm"]
        add("hand_" + name, plate([{"outer": [list(p) for p in loop(prof[:-1] + [[prof[-1][0], 0.001]], deg)], "holes": []}], z, z + th, P + "hand_" + name),
            "steel_polished", bevel=0.02)
        l0, l1 = h["lume_mm"]
        rs = [l0] + [r for r, _ in prof if l0 < r < l1] + [l1]
        add("hand_%s_lume" % name, Geo().prism(loop([[r, max(half_at(prof, r) - k, 0.02)] for r in rs], deg), z + th, z + th + 0.05), "lume")
    h = t["seconds"]
    L, deg, z, tl = h["length_mm"], h["angle_deg"], hs["z"]["seconds"], h["tail_mm"]
    nw = hs["seconds_half_width"]
    add("hand_seconds", Geo().prism([rot(x, y, deg) for x, y in [(-nw * 1.6, -tl), (nw * 1.6, -tl), (nw, L - 0.4), (0, L), (-nw, L - 0.4)]], z, z + th),
        "steel_polished", bevel=0.01)
    collar_r, cap_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (collar_r, d["z"]), (collar_r, hs["z"]["minute"] + th), (0, hs["z"]["minute"] + th)], segs=64), "steel_polished", bevel=0.02)
    zc = z + th
    add("hub_cap", Geo().lathe([(0, zc), (cap_r, zc), (cap_r, zc + 0.1), (cap_r * 0.6, zc + 0.18), (0, zc + 0.18)], segs=48), "steel_polished")

    # ---- crown at 3: collar and fluted cylinder on a radial axis ----
    cw_, crn = cfg["crown"], tr["crown"]
    a = math.radians(crn["angle_deg"])
    R0, teeth = crn["radius_mm"], crn["teeth"]
    star = [((R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.cos(math.pi * i / teeth), (R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.sin(math.pi * i / teeth))
            for i in range(teeth * 2)]
    u_, dr_ = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
    m = Matrix((u_, (0, 0, 1), dr_)).transposed().to_4x4()
    m.translation = (0, 0, cw_["z"])
    r0, r1 = crn["r_mm"]
    add("crown_collar", Geo().lathe([(0, r0 - 0.8), (R0 * 0.55, r0 - 0.8), (R0 * 0.55, r0 + 0.3), (0, r0 + 0.3)], segs=48, m=m), "steel_polished", bevel=0.06)
    add("crown", Geo().prism(star, r0 + 0.3, r1, m), "steel_polished", bevel=0.1)

    # ---- NATO strap: one band under the case, straight to the case ends, house curl past them; each side samples its own
    #      render strap, folded back and forth over its flat weave ----
    hw = tr["strap"]["half_width_mm"]
    tip = (tr["case"]["top_mm"] + tr["case"]["bottom_mm"]) / 2
    zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], tip + st["bend_after_tip"]
    box = curl(bend_y, R, zm)
    g = Geo()
    for sy in (1, -1):
        box(g, -hw, hw, st["start_y"], bend_y + R * st["arc_over_radius"], ds * st["z0"], ds * st["z1"], sy)
    Sp, n_rows = sm["scale_px_per_mm"], sm["size_px"][1]
    sides = {}
    for key, tip_px, half_u in (("top", sm["lug_tips_px"][0], 0.0), ("bottom", sm["lug_tips_px"][1], 0.5)):
        rws = sm["rows_px"][key]
        sides[key] = (tip + abs(rws[0] - tip_px) / Sp, tip + abs(rws[-1] - tip_px) / Sp, len(rws), half_u)

    def strap_uv(x, y, z):
        lo, hi, n, half_u = sides["top" if y > 0 else "bottom"]
        u = min(max((x + hw) / (2 * hw), st["uv_inset"]), 1 - st["uv_inset"])
        s = abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
        k_, w = divmod(s - lo, hi - lo)
        sp = lo + w if int(k_) % 2 == 0 else hi - w
        row = (sp - lo) / (hi - lo) * (n - 1)
        return half_u + 0.5 * u, 1 - (row + 0.5) / n_rows
    add("strap", g, "strap_leather", bevel=st["bevel"], uv_of=strap_uv)

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(w for _, w in rows), 3), "lug_to_lug": round(rows[0][0] - rows[-1][0], 3), "strap_width": round(2 * hw, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
