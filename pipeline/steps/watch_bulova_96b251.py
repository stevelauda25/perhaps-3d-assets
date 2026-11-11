"""watch_bulova_96b251: build the Bulova 96B251 (Lunar Pilot chronograph, 45 mm, black leather strap) as a flat-backed front
relief.

Params: spec (config/watches/bulova-96b251.json). Copy of watch_bulova_96b258 (same head: brushed case with integrated horns
and pusher shoulders, polished sloped bezel, applied indices, hands, subdial needles, fluted crown) with the bracelet replaced
by a 20 mm leather strap: straight in the recess between the horns, the house curl from the horn tips, the leather from the
render's own strap rows (strap_photo.jpg from pipeline/bulova_96b251_dial.py, as watch_hamilton_h76709530). Rebuild with
--force after regenerating the maps (not part of the fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_hamilton_scuba_pioneer import circle
from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    dm = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | %s front relief" % cfg["model"])
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    d = cfg["dial"]
    mats["dial"] = photo_material("dial_photo", ROOT / cfg["dial_map"], d["roughness"])
    textured = cfg.get("steel_textures", {})
    for key, tx in textured.items():  # brushed lines as a tangent-space normal map (plain image link, kept by the GLB)
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

    sm = json.loads((ROOT / cfg["strap_map"]).with_suffix(".json").read_text())
    st = cfg["strap"]
    mats["strap_leather"] = photo_material("strap_photo", ROOT / cfg["strap_map"], st["roughness"])

    def add(name, geo, mat, bevel=None, polished_bevel=False, smooth=None, uv_of=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured and not uv_of:  # planar UV in mm / tile; lines along model Y
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

    def upward(me):  # lathe discs: top faces up
        if me.polygons[0].normal.z < 0:
            for poly in me.polygons:
                poly.flip()
            me.update()
        return me

    rg, c, cr = tr["rings_mm"], cfg["case"], cfg["crystal"]
    lg = tr["lug"]
    tip, nh, ny = lg["tip_mm"], lg["notch_half_mm"], lg["notch_y_mm"]

    # ---- case with integrated horns: traced half widths, symmetric about the pivot; recess for the end link at 12 and 6 ----
    hw = sorted((y, h) for y, h in tr["case_half_width_mm"])  # y from -tip to +tip
    right = [(max(h, nh + 0.3), y) for y, h in hw[::-1]]  # top tip -> bottom tip
    left = [(-max(h, nh + 0.3), y) for y, h in hw]  # bottom tip -> top tip
    outline = right + [(nh, -tip), (nh, -ny), (-nh, -ny), (-nh, -tip)] + left + [(-nh, tip), (-nh, ny), (nh, ny), (nh, tip)]
    clean = [outline[0]]
    for q in outline[1:]:
        if math.hypot(q[0] - clean[-1][0], q[1] - clean[-1][1]) > 0.08:
            clean.append(q)
    add("case", plate([{"outer": clean, "holes": [circle(rg["bezel_in"] - 0.2, 192)]}], 0.0, c["top_z"], P + "case"), "steel_brushed",
        bevel=c["bevel"], polished_bevel=True)

    # ---- pusher shoulders at 2 and 4: the render's right silhouette beyond the case outline ----
    sh = cfg["shoulders"]
    half_at = lambda y: min(hw, key=lambda p: abs(p[0] - y))[1]
    for key, pts in tr["shoulders_mm"].items():
        pts = sorted(pts)
        loop = [(r, y) for y, r in pts] + [(half_at(y) - sh["overlap"], y) for y, _ in pts[::-1]]
        add("shoulder_" + key, plate([{"outer": loop, "holes": []}], sh["z0"], sh["z1"], P + "shoulder_" + key), "steel_brushed",
            bevel=sh["bevel"], polished_bevel=True)

    # ---- polished bezel sloping up to the crystal; crystal ----
    bz = cfg["bezel"]
    add("bezel", Geo().lathe([(rg["bezel_out"], c["top_z"] - 0.4), (rg["bezel_out"], bz["outer_z"]), (rg["bezel_in"] + 0.35, bz["top_z"]),
                              (rg["bezel_in"], bz["top_z"] - 0.1), (rg["bezel_in"], c["top_z"] - 0.4)], segs=256), "steel_polished", smooth=True)
    add("crystal", Geo().lathe([(0, cr["z0"]), (rg["bezel_in"] + 0.02, cr["z0"]), (rg["bezel_in"] + 0.02, cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial flat to the chapter ring, sloped chapter ring, tachymeter flange (photo map on a planar UV about the pivot) ----
    me = upward(Geo().lathe([(0, d["z"]), (rg["dial"], d["z"]), (rg["chapter"], d["chapter_z"]), (rg["bezel_in"], d["flange_z"])], segs=256).mesh(P + "dial", True))
    uv = me.uv_layers.new(name="UVMap")
    H = dm["half_size_mm"]
    for loop_ in me.loops:
        x, y, _ = me.vertices[loop_.vertex_index].co
        uv.data[loop_.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
    add("dial", me, "dial")

    # ---- applied indices: polished frame round a white lume fill ----
    ix, ti = cfg["indices"], tr["index"]
    z0, top, fr = d["z"], d["z"] + ix["height"], ti["frame"]
    frames, lume = [], Geo()
    for hr in range(12):
        r0, h = (ti["square_inner"], ti["square_half"]) if hr in (3, 6, 9) else (ti["inner"], ti["half_12"] if hr == 0 else ti["half"])
        q = [rot(x, y, hr * 30) for x, y in [(h, r0), (h, ti["outer"]), (-h, ti["outer"]), (-h, r0)]]
        qi = [rot(x, y, hr * 30) for x, y in [(h - fr, r0 + fr), (h - fr, ti["outer"] - fr), (-(h - fr), ti["outer"] - fr), (-(h - fr), r0 + fr)]]
        frames.append({"outer": q, "holes": [qi]})
        lume.prism(qi, z0, top - ix["lume_drop"])
    add("indices", plate(frames, z0, top, P + "indices"), "steel_polished", bevel=ix["bevel"])
    add("indices_lume", lume, "lume")

    # ---- hands at the render's time ----
    hs, th = cfg["hands"], cfg["hands"]["thickness"]
    inset = tr["lume_inset_mm"]
    for name in ("hour", "minute"):
        h, z = tr["hands"][name], hs["z"][name]
        deg = h["angle_deg"]
        loop = lambda prof: [rot(v, r, deg) for r, v in prof] + [rot(-v, r, deg) for r, v in prof[::-1]]
        prof = h["outline_mm"]
        inner = [(max(r, prof[0][0] + inset + tr["hub_radius_mm"][0]), v - inset) for r, v in prof if v - inset > 0.06]
        inner.append((prof[-1][0] - 2.5 * inset, 0.06))
        add("hand_" + name, plate([{"outer": loop(prof), "holes": [loop(inner)]}], z, z + th, P + "hand_" + name), "steel_polished", bevel=0.02)
        add("hand_%s_lume" % name, Geo().prism(loop(inner), z + 0.02, z + th + hs["lume_raise"]), "lume")
    h, z = tr["hands"]["chrono"], hs["z"]["chrono"]
    prof = h["outline_mm"]
    add("hand_chrono", Geo().prism([rot(v, r, h["angle_deg"]) for r, v in prof] + [rot(-v, r, h["angle_deg"]) for r, v in prof[::-1]], z, z + th),
        "hand_white", bevel=0.015)
    hub_r, cap_r = tr["hub_radius_mm"]
    zt = hs["z"]["chrono"] + th
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, hs["z"]["hour"] + th), (cap_r, hs["z"]["hour"] + th), (cap_r, zt + 0.05), (0, zt + 0.05)], segs=64),
        "steel_polished", smooth=True)
    add("hub_cap", Geo().lathe([(0, zt + 0.05), (cap_r * 0.55, zt + 0.05), (cap_r * 0.55, zt + 0.15), (0, zt + 0.15)], segs=48), "steel_polished", smooth=True)
    sb = tr["subs"]
    for k, (cx, cy) in enumerate(sb["centres_mm"]):
        z = hs["z"]["sub"]
        pts = [(-sb["half_mm"] * 1.2, -sb["tail_mm"]), (sb["half_mm"] * 1.2, -sb["tail_mm"]), (sb["half_mm"], sb["length_mm"] - 0.1), (0, sb["length_mm"]),
               (-sb["half_mm"], sb["length_mm"] - 0.1)]
        add("hand_sub%d" % k, Geo().prism([(cx + x, cy + y) for x, y in (rot(a, b, sb["angle_deg"]) for a, b in pts)], z, z + th), "hand_white", bevel=0.01)
        add("hub_sub%d" % k, Geo().lathe([(0, d["z"]), (sb["hub_mm"], d["z"]), (sb["hub_mm"], z + th + 0.04), (0, z + th + 0.04)], segs=48,
                                         m=Matrix.Translation((cx, cy, 0))), "steel_polished", smooth=True)

    # ---- crown at 3: collar, fluted cylinder, rounded end ----
    cw_, crn = cfg["crown"], tr["crown"]
    a = math.radians(crn["angle_deg"])
    R0, teeth = crn["radius_mm"], crn["teeth"]
    star = [((R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.cos(math.pi * i / teeth), (R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.sin(math.pi * i / teeth))
            for i in range(teeth * 2)]
    u_, dr_ = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
    m = Matrix((u_, (0, 0, 1), dr_)).transposed().to_4x4()
    m.translation = (0, 0, cw_["z"])
    r0, r1 = crn["r_mm"]
    add("crown_collar", Geo().lathe([(0, r0 - 1.0), (R0 * 0.6, r0 - 1.0), (R0 * 0.6, r0 + 0.4), (0, r0 + 0.4)], segs=48, m=m), "steel_polished", bevel=0.08)
    add("crown", Geo().prism(star, r0 + 0.4, r1 - cw_["end"], m), "steel_polished", bevel=0.12)
    add("crown_end", Geo().lathe([(0, r1 - cw_["end"]), (R0 - 0.1, r1 - cw_["end"]), (R0 - 0.5, r1 - 0.15), (R0 - 1.0, r1), (0, r1)], segs=64, m=m),
        "steel_polished", smooth=True)

    # ---- leather strap: straight in the recess between the horns, house curl from the horn tips; each side samples its own
    #      photo strap, tips aligned, folded back and forth over its flat leather under the case ----
    shw = tr["strap"]["half_mm"] - st["edge_inset"]
    zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], tip + st["bend_after_tip"]
    box = curl(bend_y, R, zm)
    g = Geo()
    for sy in (1, -1):
        box(g, -shw, shw, st["start_y"], bend_y + R * st["arc_over_radius"], ds * st["z0"], ds * st["z1"], sy)
    Sp, n_rows = sm["scale_px_per_mm"], sm["size_px"][1]
    sides = {}
    for key, tip_px, half_u in (("top", sm["lug_tips_px"][0], 0.0), ("bottom", sm["lug_tips_px"][1], 0.5)):
        rows = sm["rows_px"][key]
        sides[key] = (tip + abs(rows[0] - tip_px) / Sp, tip + abs(rows[-1] - tip_px) / Sp, len(rows), half_u)

    def strap_uv(x, y, z):
        lo, hi, n, half_u = sides["top" if y > 0 else "bottom"]
        u = min(max((x + shw) / (2 * shw), st["uv_inset"]), 1 - st["uv_inset"])  # side walls take the strap's own edge pixels
        s_ = abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
        k_, w = divmod(s_ - lo, hi - lo)  # in the recess the strip is folded, not clamped
        sp = lo + w if int(k_) % 2 == 0 else hi - w
        row = (sp - lo) / (hi - lo) * (n - 1)
        return half_u + 0.5 * u, 1 - (row + 0.5) / n_rows
    add("strap", g, "strap_leather", bevel=st["bevel"], uv_of=strap_uv)

    # ---- checks against the anchors ----
    out = {"case_width": round(2 * max(h for _, h in hw), 3), "lug_to_lug": round(2 * tip, 3), "strap_width": round(2 * (shw + st["edge_inset"]), 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
