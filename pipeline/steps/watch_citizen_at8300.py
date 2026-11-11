"""watch_citizen_at8300: build the Citizen AT8300-58L (Promaster Navihawk A-T, 41 mm, blue dial, slide rule, steel bracelet) as
a flat-backed front relief.

Params: spec (config/watches/citizen-at8300-58l.json). Same frame, pose, 2.5D depth scale, materials and bracelet curl as
watch_citizen_nk0024; origin = the dial centre (the hand stack is placed here). Parts from the official render: a brushed case
with broad horns and a recess for the end link at 12 and 6, the crown guard on the right flank and the shoulder by the left
crown, a satin steel bezel with polished chamfers, applied polished batons and small squares with lume, the traced hour and
minute hands (polished outline, lume inlay), a white chronograph needle with its black hooked counterweight, a black hub,
knurled crowns at 3 and 8, pushers at 2 and 4, and a three-column bracelet (wide centre links half a link nearer the case).
The dial, city ring, both slide rules, subdials and their needles are the photo map from pipeline/citizen_at8300_dial.py.
Rebuild with --force after regenerating the map (it is not part of the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    dm = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Citizen AT8300-58L front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    d = cfg["dial"]
    mats["dial"] = photo_material("dial_photo", ROOT / cfg["dial_map"], d["roughness"])
    textured = cfg.get("brushed_textures", {})
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

    def add(name, geo, mat, bevel=None, bevel_mat=None, smooth=None, uv_of=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured and not uv_of:  # planar UV in mm / tile, lines along the bracelet (model Y)
            tile = textured[mat]["tile_mm"]
            uv_of = lambda x, y, z: (y / tile, -x / tile)
        if uv_of:
            uv = me.uv_layers.new(name="UVMap")
            for loop in me.loops:
                uv.data[loop.index].uv = uv_of(*me.vertices[loop.vertex_index].co)
        if bevel:
            if bevel_mat:
                me.materials.append(mats[bevel_mat])
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            if bevel_mat:
                m.material = 1
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if not name.startswith("bracelet"):
            o.scale = (1, 1, ds)
        return o

    def upward(me):
        if me.polygons[0].normal.z < 0:
            for poly in me.polygons:
                poly.flip()
            me.update()
        return me

    circle = lambda r, n=192, cx=0.0, cy=0.0: [(cx + r * math.sin(2 * math.pi * k / n), cy + r * math.cos(2 * math.pi * k / n)) for k in range(n)]
    rg, c = tr["rings_mm"], cfg["case"]

    # ---- case with broad horns: traced half widths (top and bottom averaged), recess for the end link at 12 and 6 ----
    rows = {round(y, 1): h for y, h in tr["case_half_width_mm"]}
    tip = tr["horn_tip_mm"]
    nh, ny = tr["end_link"]["half_mm"], c["recess_from_y"]

    def half(y):
        ks = sorted(rows, key=lambda k: abs(k - y))[:1] + sorted(rows, key=lambda k: abs(k + y))[:1]
        return sum(rows[k] for k in ks) / 2

    ys = [tip - 0.25 * k for k in range(int(2 * tip / 0.25) + 1)]
    right = [(max(half(y), nh + 0.3), y) for y in ys]  # top tip -> bottom tip
    outline = right + [(nh, -tip), (nh, -ny), (-nh, -ny), (-nh, -tip)] + [(-x, y) for x, y in right[::-1]] + [(-nh, tip), (-nh, ny), (nh, ny), (nh, tip)]
    add("case", plate([{"outer": outline, "holes": [circle(rg["bezel_in"] - 0.3, 192)]}], 0.0, c["top_z"], P + "case"), "steel_brushed",
        bevel=c["bevel"], bevel_mat="steel_polished")
    for key in ("guard_mm", "left_shoulder_mm"):
        pts = [tuple(p) for p in tr[key]]
        add(key.split("_mm")[0], plate([{"outer": pts, "holes": []}], c["guard_z"][0], c["guard_z"][1], P + key), "steel_brushed", bevel=c["guard_bevel"],
            bevel_mat="steel_polished")

    # ---- bezel: polished inner chamfer, satin flat top, rounded polished outer edge; crystal ----
    bz = cfg["bezel"]
    bi, bo = rg["bezel_in"], rg["bezel_out"]
    add("bezel_chamfer", Geo().lathe([(bi, bz["lip_z"]), (bi + bz["chamfer"], bz["top_z"]), (bi + bz["chamfer"], c["top_z"] - 0.3), (bi, c["top_z"] - 0.3)], segs=256),
        "steel_polished", smooth=True)
    add("bezel", Geo().lathe([(bi + bz["chamfer"], c["top_z"] - 0.3), (bi + bz["chamfer"], bz["top_z"]), (bo - bz["round"], bz["top_z"]),
                              (bo - 0.15, bz["top_z"] - 0.3), (bo, bz["top_z"] - bz["round"]), (bo, c["top_z"] - 0.3)], segs=256), "steel_satin", smooth=True)
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (bi + 0.02, cr["z0"]), (bi + 0.02, cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial (to the city ring), inner slide rule and outer slide rule a step higher each; one photo map, planar UV ----
    S = tr["scale_px_per_mm"]
    ox, oy = dm["centre_offset_px"][0] / S, -dm["centre_offset_px"][1] / S
    H = dm["half_size_mm"]
    prof = [(0, d["z"]), (rg["city"], d["z"]), (rg["city"], d["inner_rule_z"]), (rg["inner_rule"], d["inner_rule_z"]), (rg["inner_rule"], d["outer_rule_z"]),
            (bi + 0.02, d["outer_rule_z"])]
    me = upward(Geo().lathe(prof, segs=256).mesh(P + "dial", True))
    add("dial", me, "dial", uv_of=lambda x, y, z: (0.5 + (x + ox) / (2 * H), 0.5 + (y + oy) / (2 * H)))

    # ---- applied indices: polished bars and squares, lume inlay ----
    ix, ti = cfg["indices"], tr["indices"]
    z0, z1, fr = d["z"], d["z"] + ix["height"], ti["frame_mm"]
    bt = ti["baton"]
    bars = [{"centre_mm": [bt["r_mm"] * math.sin(math.radians(30 * h)), bt["r_mm"] * math.cos(math.radians(30 * h))], "angle_deg": 30 * h,
             "half_len_mm": bt["half_len_mm"], "half_w_mm": bt["half_w_mm"]} for h in bt["hours"]] + ti["small"]
    frames, lume = Geo(), Geo()
    for b in bars:
        m = Matrix.Translation((*b["centre_mm"], 0)) @ Matrix.Rotation(-math.radians(b["angle_deg"]), 4, "Z")
        frames.prism(rect(0, 0, 2 * b["half_w_mm"], 2 * b["half_len_mm"]), z0, z1, m)
        lume.prism(rect(0, 0, 2 * (b["half_w_mm"] - fr), 2 * (b["half_len_mm"] - fr)), z0, z1 + ix["lume_raise"], m)
    add("indices", frames, "steel_polished", bevel=0.04)
    add("index_lume", lume, "lume")

    # ---- hands: traced outlines moved from the render's hand pivot to the origin ----
    hs, th = cfg["hands"], cfg["hands"]["thickness"]
    hx, hy = tr["hand_offset_mm"]
    for name in ("hour", "minute"):
        h, z = tr["hands"][name], hs["z"][name]
        out_ = [(x - hx, y - hy) for x, y in h["outline_mm"]]
        lm = [(x - hx, y - hy) for x, y in h["lume_mm"]]
        add("hand_" + name, plate([{"outer": out_, "holes": []}], z, z + th, P + "hand_" + name), "steel_polished", bevel=0.02)
        add("hand_%s_lume" % name, plate([{"outer": lm, "holes": []}], z + th - 0.02, z + th + hs["lume_raise"], P + "hand_%s_lume" % name), "lume")
    h, z = tr["hands"]["chrono"], hs["z"]["chrono"]
    h0, h1 = h["half_mm"]
    add("hand_chrono", Geo().prism([rot(x, y, h["angle_deg"]) for x, y in [(-h0, -h["tail_mm"]), (h0, -h["tail_mm"]), (h1, h["tip_mm"] - 0.3), (0, h["tip_mm"]),
                                                                            (-h1, h["tip_mm"] - 0.3)]], z, z + th), "hand_white", bevel=0.015)
    cw = tr["counter"]
    c0, c1 = cw["half_mm"]
    g = Geo()
    g.prism([rot(x, y, cw["angle_deg"]) for x, y in [(-c0, 0.0), (c0, 0.0), (c1, cw["length_mm"] - 0.2), (0, cw["length_mm"]), (-c1, cw["length_mm"] - 0.2)]], z, z + th)
    for hk in cw["hooks"]:
        g.prism(circle(hk["radius_mm"], 32, *rot(0, hk["r_mm"], hk["angle_deg"])), z, z + th)
    add("hand_chrono_counter", g, "hand_black", bevel=0.015)
    hub_r, screw_r = tr["hub_radius_mm"]
    zt = z + th
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, zt + 0.05), (0, zt + 0.05)], segs=64), "hand_black", smooth=True)
    add("hub_screw", Geo().lathe([(0, zt + 0.05), (screw_r, zt + 0.05), (screw_r, zt + 0.12), (0, zt + 0.12)], segs=32), "steel_polished", smooth=True)
    for k, (sx, sy) in enumerate(tr["subs"]["centres_mm"]):
        add("hub_sub%d" % k, Geo().lathe([(0, d["z"]), (tr["subs"]["hub_mm"], d["z"]), (tr["subs"]["hub_mm"], d["z"] + 0.12), (0, d["z"] + 0.12)], segs=48,
                                         m=Matrix.Translation((sx, sy, 0))), "hand_black", smooth=True)

    # ---- crowns (knurled) at 3 and 8, pushers at 2 and 4, each on a radial axis ----
    def radial(angle_deg, zc):
        a = math.radians(angle_deg)
        u_, dr_ = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
        m = Matrix((u_, (0, 0, 1), dr_)).transposed().to_4x4()
        m.translation = (0, 0, zc)
        return m

    ck = cfg["crowns"]
    for key in ("crown", "crown_left"):
        cr_ = tr[key]
        R0, n = cr_["radius_mm"], cr_["teeth"]
        star = [((R0 if i % 2 == 0 else R0 - ck["flute_depth"]) * math.cos(math.pi * i / n), (R0 if i % 2 == 0 else R0 - ck["flute_depth"]) * math.sin(math.pi * i / n))
                for i in range(2 * n)]
        m = radial(cr_["angle_deg"], ck["z"])
        r0, r1 = cr_["r_mm"]
        add(key + "_collar", Geo().lathe([(0, r0 - 1.0), (R0 * 0.6, r0 - 1.0), (R0 * 0.6, r0 + 0.3), (0, r0 + 0.3)], segs=48, m=m), "steel_polished", bevel=0.08)
        add(key, Geo().prism(star, r0 + 0.3, r1 - 0.4, m), "steel_satin", bevel=0.1)
        add(key + "_end", Geo().lathe([(0, r1 - 0.4), (R0 - 0.15, r1 - 0.4), (R0 - 0.5, r1), (0, r1)], segs=64, m=m), "steel_polished", smooth=True)
    for k, p in enumerate(tr["pushers"]):
        m = radial(p["angle_deg"], ck["z"])
        r0, r1 = p["r_mm"]
        R0 = p["radius_mm"]
        add("pusher%d" % k, Geo().lathe([(0, r0 - 1.0), (R0, r0 - 1.0), (R0, r1 - 0.5), (R0 - 0.3, r1), (0, r1)], segs=48, m=m), "steel_polished", smooth=True)
        add("pusher%d_collar" % k, Geo().lathe([(0, r0 - 1.0), (R0 + 0.35, r0 - 1.0), (R0 + 0.35, r0 + 0.6), (0, r0 + 0.6)], segs=48, m=m), "steel_satin", bevel=0.08)

    # ---- end link in the recess; three-column bracelet from its tip with the house curl ----
    br, el, tb = cfg["bracelet"], cfg["end_link"], tr["bracelet"]
    etip = tr["end_link"]["tip_mm"]
    ch, gap, pitch = tb["centre_half_mm"], br["gap"], tb["pitch_mm"]
    end = Geo()
    for sy in (1, -1):
        end.prism(rect(0, sy * (ny - el["under"] + etip) / 2, 2 * nh, etip - ny + el["under"]), 0.0, el["top_z"])
    add("end_links", end, "steel_brushed", bevel=el["bevel"], bevel_mat="steel_polished")
    hw_at = lambda y: br["half_at_tip"] + (br["half_at_end"] - br["half_at_tip"]) * min(max((y - etip) / (br["end_y"] - etip), 0.0), 1.0)
    zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]
    bent_box = curl(etip + br.get("bend_after_tip", 0.0), R, zm)
    outer, centre, back = Geo(), Geo(), Geo()
    za, zb = ds * br["z0"], ds * br["z1"]
    n_rows = 0
    for sy in (1, -1):
        for kind, start in (("outer", etip), ("centre", etip - tb["centre_lead_mm"])):
            y0 = start
            while y0 < br["end_y"] - 0.5:
                y1 = min(y0 + pitch - gap, br["end_y"])
                if kind == "outer":
                    hw_ = hw_at((y0 + y1) / 2)
                    for sx in (1, -1):
                        x0, x1 = sorted((sx * (ch + gap), sx * hw_))
                        bent_box(outer, x0, x1, max(y0, etip), y1, za, zb, sy)
                    bent_box(back, -(hw_ - 0.3), hw_ - 0.3, max(y0, etip), y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    n_rows += 1
                else:
                    bent_box(centre, -ch, ch, y0, y1, za, zb + ds * br["centre_raise"], sy)
                y0 = y1 + gap
    add("bracelet_links", outer, "steel_brushed", bevel=br["bevel"], bevel_mat="steel_polished")
    add("bracelet_centre", centre, "steel_brushed", bevel=br["bevel"], bevel_mat="steel_polished")
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * bo, 3), "horn_to_horn": round(2 * tip, 3), "bracelet_width": round(2 * br["half_at_tip"], 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "horn_tip_mm": tip, "bracelet_rows": n_rows, "indices": len(bars), "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
