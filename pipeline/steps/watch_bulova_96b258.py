"""watch_bulova_96b258: build the Bulova 96B258 (Lunar Pilot chronograph, 45 mm, steel bracelet) as a flat-backed front relief.

Params: spec (config/watches/bulova-96b258.json). Frame as watch_bulova_98a227: mm, origin = hand pivot, dial faces +z, back
flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, bracelet built at final depth with the
house curl. Parts from the official render: a brushed case with integrated horns (one body from the traced outline, the end
link sits in a recess between the horns), pusher shoulders at 2 and 4, a polished sloped bezel, the dial with its sloped
chapter ring and tachymeter flange (photo map, pipeline/bulova_96b258_dial.py), applied polished frames with white lume
(batons, a wide 12, squares at 3, 6 and 9), lume hour and minute hands in a polished frame, a white chronograph hand with
counterweight and lozenge, three white subdial needles, a fluted crown, a three-column bracelet. Rebuild with --force
after regenerating the map (not part of the fingerprint).
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

    def add(name, geo, mat, bevel=None, polished_bevel=False, smooth=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured:  # planar UV in mm / tile; lines along the bracelet (model Y)
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

    # ---- end links in the recess, three-column bracelet from the lug tips with the house curl ----
    br, el, bt = cfg["bracelet"], cfg["end_link"], tr["bracelet"]
    half, ch, gap = bt["half_mm"], bt["centre_half_mm"], br["gap"]
    end = Geo()
    for sy in (1, -1):
        y0, y1 = ny - el["under"], tip
        for x0, x1 in ((-half, -ch - gap / 2), (-ch + gap / 2, ch - gap / 2), (ch + gap / 2, half)):
            end.prism(rect((x0 + x1) / 2, sy * (y0 + y1) / 2, x1 - x0, y1 - y0), 0.0, el["top_z"])
    add("end_links", end, "steel_brushed", bevel=el["bevel"], polished_bevel=True)

    zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]
    bent_box = curl(tip + br.get("bend_after_tip", 0.0), R, zm)
    outer, centre, back = Geo(), Geo(), Geo()
    za, zb = ds * br["z0"], ds * br["z1"]
    pitch, rows = bt["pitch_mm"], 0
    for sy in (1, -1):
        for kind, start in (("outer", tip + gap), ("centre", tip + gap + bt["centre_offset_mm"])):
            y0 = start if kind == "outer" else tip + gap
            first = True
            while y0 < br["end_y"] - 0.3:
                y1 = min((start + pitch if first and kind == "centre" else y0 + pitch) - gap, br["end_y"])
                first = False
                if kind == "outer":
                    for sx in (1, -1):
                        x0, x1 = sorted((sx * (ch + gap / 2), sx * half))
                        bent_box(outer, x0, x1, y0, y1, za, zb, sy)
                    bent_box(back, -(half - 0.3), half - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                else:
                    bent_box(centre, -(ch - gap / 2), ch - gap / 2, y0, y1, za, zb + ds * br["centre_raise"], sy)
                y0 = y1 + gap
    add("bracelet_links", outer, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_centre", centre, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"case_width": round(2 * max(h for _, h in hw), 3), "lug_to_lug": round(2 * tip, 3), "bracelet_width": round(2 * half, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "bracelet_rows": rows, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
