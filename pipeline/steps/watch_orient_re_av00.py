"""watch_orient_re_av00: build an Orient Star Modern Skeleton (RE-AV0004N00B steel bracelet, RE-AV0005L00B leather strap) as a
flat-backed front relief.

Params: spec (config/watches/orient-re-av0004n00b.json or orient-re-av0005l00b.json). Same frame, pose, 2.5D depth scale,
materials and curl as watch_orient_ra_ac0f06l10b (leather strap) and watch_orient_re_au0107e (five-piece bracelet). Parts from
the photo: a lathe for the case and its wide polished sloped bezel, four brushed lugs with polished edges flowing out of the case
(outline by depth from the tip), applied faceted wedges (8 and 10 shortened by the open heart and the window), an applied XII
traced from the photo, faceted-frame hour and minute hands with long counterweight tails and lume inlays (rose gold or steel),
a hub, a large fluted crown. Either a five-piece bracelet (brushed outer, polished narrow, brushed centre; narrow and centre
joints nearer the case) or a leather strap from the strap photo map. The dial (open heart, power reserve, small seconds, chapter
ring, logo) is the photo map from pipeline/orient_re_av00_dial.py. Rebuild with --force after regenerating the maps.
"""
import json
import math

import bpy
import numpy as np
from mathutils import Matrix

from pipeline.steps.watch_orient_faa02004b9 import hand_poly
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
    if "strap" in cfg:
        mats["strap_leather"] = photo_material("strap_photo", ROOT / cfg["strap_map"], cfg["strap"]["roughness"])
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
        if uv_of or mat in textured:  # photo maps: their own UVs; brushed: planar in mm / tile, lines along the bracelet (model Y)
            tile = textured.get(mat, {}).get("tile_mm", 1.0)
            f = uv_of or (lambda x, y, z: (y / tile, -x / tile))
            uv = me.uv_layers.new(name="UVMap")
            for loop in me.loops:
                uv.data[loop.index].uv = f(*me.vertices[loop.vertex_index].co)
        if bevel:
            if polished_bevel:
                me.materials.append(mats["steel_polished"])
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            if polished_bevel:
                m.material = 1
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if not name.startswith(("bracelet", "strap")):
            o.scale = (1, 1, ds)
        return o

    # ---- polished case with the wide sloped bezel, dark line at the crystal edge, crystal ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), "steel_polished", smooth=True)
    gk = cfg["gasket"]
    add("gasket", Geo().lathe([(gk["r_in"], gk["z0"]), (gk["r_out"], gk["z0"]), (gk["r_out"], gk["z1"]), (gk["r_in"], gk["z1"])], segs=192), "gasket_black")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial + grey inner slope (rehaut), photo map on a planar UV about the hand pivot ----
    H = dm["half_size_mm"]
    me = Geo().lathe([(0, d["z"]), (tr["rehaut_mm"], d["z"]), (d["rehaut_r"], d["rehaut_z"])], segs=192).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    add("dial", me, "dial", uv_of=lambda x, y, z: (0.5 + x / (2 * H), 0.5 + y / (2 * H)))

    # ---- applied faceted wedges (ridge on the centre line), applied XII ----
    ix, ti = cfg["indices"], tr["indices"]
    z0, top = d["z"], d["z"] + ix["height"]
    b = ti["baton_mm"]
    g = Geo()
    for hour in ti["hours"]:
        r0 = ti["inner_mm_by_hour"].get(str(hour), b["inner"])
        h0 = b["half_inner"] + (b["half_outer"] - b["half_inner"]) * (r0 - b["inner"]) / (b["outer"] - b["inner"])
        for sx in (1, -1):
            pts = [(0.0, r0), (sx * h0, r0), (sx * b["half_outer"], b["outer"]), (0.0, b["outer"])]
            ridge = {rot(x, y, hour * 30) for x, y in pts if x == 0.0}
            slab(g, [rot(x, y, hour * 30) for x, y in pts], z0, lambda x, y, ridge=ridge: top + ix["ridge"] * ((x, y) in ridge))
    add("indices", g, "steel_polished", bevel=0.03)
    add("numeral_xii", plate(tr["xii_shapes"], z0, z0 + ix["numeral_height"], P + "numeral_xii"), cfg["hand_metal"], bevel=ix["numeral_bevel"])

    # ---- hands at the photo's time: metal frame with a lume inlay, long counterweight tails; hub ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute"):
        h = t[name]
        deg, z = h["angle_deg"], hs["z"][name]
        add("hand_" + name, Geo().prism([rot(x, y, deg) for x, y in hand_poly(h["outline_mm"])], z, z + th), cfg["hand_metal"], bevel=0.02)
        add("hand_%s_lume" % name, Geo().prism([rot(x, y, deg) for x, y in hand_poly(h["lume_mm"])], z + th, z + th + hs["lume_height"]), "lume")
    collar_r, cap_r = tr["hub_radius_mm"]
    zh, zm_ = hs["z"]["hour"], hs["z"]["minute"] + th
    add("hub", Geo().lathe([(0, d["z"]), (collar_r, d["z"]), (collar_r, zm_ + 0.06), (cap_r, zm_ + 0.06), (cap_r, zm_ + 0.2),
                            (cap_r * 0.6, zm_ + 0.26), (0, zm_ + 0.26)], segs=64), cfg["hand_metal"])

    # ---- crown on the 3 o'clock axis: neck, fluted body, smooth cap ----
    cw_, tc = cfg["crown"], tr["crown"]
    R0, teeth = tc["radius_mm"], tc["teeth"]
    star = [((R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.cos(math.pi * i / teeth),
             (R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.sin(math.pi * i / teeth)) for i in range(teeth * 2)]
    m = Matrix(((0, -1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_4x4()  # local z along +x, local y up
    m.translation = (0.0, 0.0, cw_["z"])
    r_case = tr["case"]["radius_mm"]
    add("crown_neck", Geo().lathe([(0, r_case - 1.0), (R0 * 0.55, r_case - 1.0), (R0 * 0.55, cw_["r_from"] + 0.1), (0, cw_["r_from"] + 0.1)], segs=48, m=m),
        "steel_polished", smooth=True)
    add("crown", Geo().prism(star, cw_["r_from"], tc["cap_from_mm"], m), "steel_polished", bevel=0.12)
    add("crown_cap", Geo().lathe([(0, tc["cap_from_mm"]), (R0 * 0.88, tc["cap_from_mm"]), (R0 * 0.88, tc["to_mm"]), (0, tc["to_mm"])], segs=48, m=m),
        "steel_polished", bevel=0.1)

    # ---- lugs: outline by depth from the tip (top and bottom averaged), brushed top sloping to the tip, polished edge ----
    lg, tl = cfg["lug"], tr["lug"]
    tip, xi = tl["tip_mm"], cfg["lug_inner_x"]
    outer = [(w, tip - dd) for dd, w in tl["half_width_by_depth_mm"] if math.hypot(w, tip - dd) > r_case - lg["into_case"]]  # until it runs into the case
    outer = [(lg["tip_outer_x"], tip)] + outer
    poly = [(xi, tip)] + outer + [(xi, outer[-1][1])]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * min(1.0, max(0.0, (abs(y) - lg["slope_from_y"]) / (tip - lg["slope_from_y"])))
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in poly], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "lug_to_lug": round(2 * tip, 3)}
    if "bracelet" in cfg:
        # ---- five-piece bracelet: brushed outer links at the lug tips; polished narrow and brushed centre links whose joints
        #      sit `shift` nearer the case ----
        br, el, tb = cfg["bracelet"], cfg["end_link"], tr["bracelet"]
        ch, nh, shift, gap = tb["centre_half_mm"], tb["narrow_half_mm"], tb["centre_joint_shift_mm"], br["gap"]
        ss, hws = np.array(tb["half_width_by_s_mm"]).T
        hw_at = lambda s: min(float(np.interp(s, ss, hws)), xi + br["flare"])
        end_brushed, end_polished = Geo(), Geo()
        for sy in (1, -1):
            for sx in (1, -1):
                end_brushed.prism(rect(sx * (nh + gap + xi) / 2, sy * (el["from_y"] + tip) / 2, xi - nh - gap, tip - el["from_y"]), 0.0, el["top_z"])
            y1 = tip - shift - gap
            for sx in (1, -1):
                end_polished.prism(rect(sx * (ch + gap + nh) / 2, sy * (el["from_y"] + y1) / 2, nh - ch - gap, y1 - el["from_y"]), 0.0, el["top_z"])
            end_brushed.prism(rect(0, sy * (el["from_y"] + y1) / 2, 2 * ch, y1 - el["from_y"]), 0.0, el["top_z"])
        add("end_links", end_brushed, "steel_brushed", bevel=el["bevel"], polished_bevel=True)
        add("end_links_narrow", end_polished, "steel_polished", bevel=el["bevel"])

        zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]
        bent_box = curl(tip + br.get("bend_after_tip", 0.0), R, zm)
        pitch = tb["pitch_mm"]
        brushed, polished, back = Geo(), Geo(), Geo()
        za, zb = ds * br["z0"], ds * br["z1"]
        for sy in (1, -1):
            for kind, start in (("outer", tip), ("centre", tip - shift)):
                y0 = start
                while y0 < br["end_y"] - 0.5:
                    y1 = min(y0 + pitch - gap, br["end_y"])
                    hw = hw_at((y0 + y1) / 2)
                    if kind == "outer":
                        for sx in (1, -1):
                            x0, x1 = sorted((sx * (nh + gap), sx * hw))
                            bent_box(brushed, x0, x1, y0, y1, za, zb, sy)
                        bent_box(back, -(hw - 0.3), hw - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    else:
                        for sx in (1, -1):
                            x0, x1 = sorted((sx * (ch + gap), sx * nh))
                            bent_box(polished, x0, x1, y0, y1, za, zb + ds * br["narrow_raise"], sy)
                        bent_box(brushed, -ch, ch, y0, y1, za, zb, sy)
                    y0 = y1 + gap
        add("bracelet_links", brushed, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
        add("bracelet_links_narrow", polished, "steel_polished", bevel=br["bevel"] * 0.6)
        add("bracelet_backing", back, "steel_gap")
        out["lug_width"] = round(2 * xi, 3)
    else:
        # ---- leather strap: straight between the lugs, house curl from the tips; samples the photo's bottom strap from its
        #      lug tip outward, folded back and forth over its flat leather ----
        st, sm = cfg["strap"], json.loads((ROOT / cfg["strap_map"]).with_suffix(".json").read_text())
        hw = xi - st["edge_inset"]
        zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], tip + st["bend_after_tip"]
        box = curl(bend_y, R, zm)
        g = Geo()
        for sy in (1, -1):
            box(g, -hw, hw, st["start_y"], bend_y + R * st["arc_over_radius"], ds * st["z0"], ds * st["z1"], sy)
        rows, Sp, tip_px, n_rows = sm["rows_px"], sm["scale_px_per_mm"], sm["lug_tip_px"], sm["size_px"][1]
        lo, hi = tip + (rows[0] - tip_px) / Sp, tip + (rows[-1] - tip_px) / Sp  # flat leather in the photo, model s

        def strap_uv(x, y, z):
            u = min(max((x + hw) / (2 * hw), st["uv_inset"]), 1 - st["uv_inset"])
            s = abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
            k_, w = divmod(s - lo, hi - lo)  # under the case and lugs too: folded, not clamped (a clamp streaks)
            sp = lo + w if int(k_) % 2 == 0 else hi - w
            return u, 1 - ((sp - lo) / (hi - lo) * (len(rows) - 1) + 0.5) / n_rows
        add("strap", g, "strap_leather", bevel=st["bevel"], uv_of=strap_uv)
        out["strap_width"] = round(2 * hw, 3)

    # ---- checks against the anchors ----
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
