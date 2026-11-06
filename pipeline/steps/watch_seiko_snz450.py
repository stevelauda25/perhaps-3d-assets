"""watch_seiko_snz450: build the Seiko 5 Sports SNZ450J1 (gold tone) as a flat-backed front relief, like watch_seiko_snkl50.

Params: spec (config/watches/seiko-snz450j1.json). Same frame as watch_seiko_snkl50: mm, origin = dial centre, dial faces +z,
back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, bracelet built at final depth with
the smooth curl. Differences: the case is not round: its traced outline r(angle) carries a sloped top with teardrop scoops and
pointed claws (a polar height field), a separate polished bezel ring, a solid end link under the flat case edge; white-lume batons in gold
frames and a pentagon marker at 12; applied SEIKO and 5 shield plates; gold baton hands with lume, black inlays and wide tails; a needle seconds hand with a long
tail; two bracelet columns. The photo is turned by photo_rot_deg: the dial UV turns it back. Rebuild with --force after
regenerating the dial map.
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def sculpted_case(r_out, c, r_in, claws, scoops):
    """Closed ring mesh: sloped top from r_in to the traced outline r_out[deg] with scoops and claws, rounded edge, wall, flat back."""
    sc, cl = c["scoop"], c["claw"]

    def feature(x, y):
        r, a = math.hypot(x, y), math.atan2(x, y)
        dz = 0.0
        for k, (rk, deg) in enumerate(scoops):  # elliptical dish with a crisp rim: depth * (1 - q^2)
            d = (a - math.radians(deg) + math.pi) % (2 * math.pi) - math.pi
            at, ar, rc = (sc["tangential"][0], sc["radial"][0], sc["centre_r"][0]) if k < 2 else (sc["tangential"][1], sc["radial"][1], sc["centre_r"][1])
            q2 = (rc * d / at) ** 2 + ((r - rc) / ar) ** 2
            if q2 < 1:
                dz -= sc["depth"] * (1 - q2)
        for rk, deg in claws:  # pyramid pointing at the dial: ridge on the claw's centre line, flat sides
            d = abs((a - math.radians(deg) + math.pi) % (2 * math.pi) - math.pi) * r
            s = (r - cl["inner_r"]) / max(rk - cl["inner_r"], 0.5)  # 0 at the point, 1 at the traced centre
            if s > 0:
                w = cl["half_width"] * min(s, 1.0)
                fade = 1.0 if s <= 1 else max(0.0, 1 - (s - 1) * cl["fade"])
                dz += cl["height"] * max(0.0, 1 - d / w) * fade
        return dz

    def ring(fr, z_of, inset=0.0):
        pts = []
        for deg in range(360):
            ro = r_out[deg] - inset
            r = r_in + fr * (ro - r_in)
            x, y = r * math.sin(math.radians(deg)), r * math.cos(math.radians(deg))
            pts.append((x, y, z_of(fr, x, y)))
        return pts

    zi, ze, er, pw = c["z_inner"], c["z_edge"], c["edge_round"], c["slope_power"]
    top = lambda f, x, y: zi + (ze - zi) * f ** pw + feature(x, y) * (1 - f ** 4)
    rings = [ring(k / c["rings"], top, er * (k / c["rings"]) ** 8) for k in range(c["rings"] + 1)]
    rings.append(ring(1, lambda f, x, y: ze - er * 0.4, er * 0.25))
    rings.append(ring(1, lambda f, x, y: ze - er, 0.0))
    rings.append(ring(1, lambda f, x, y: 0.0, 0.0))
    rings.append(ring(0, lambda f, x, y: 0.0))
    g = Geo()
    n = 360
    for rg in rings:
        g.v += rg
    for j in range(len(rings)):  # closed profile: the last ring (r_in, z 0) joins the first (r_in, top)
        j2 = (j + 1) % len(rings)
        for i in range(n):
            i2 = (i + 1) % n
            g.f.append((j * n + i, j * n + i2, j2 * n + i2, j2 * n + i))
            g.smooth.append(j < c["rings"] + 2)
    return g


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    coll = bpy.data.collections.new("WATCH | Seiko 5 Sports SNZ450J1 front relief")
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
    ds = cfg["pose"].get("depth_scale", 1.0)

    def add(name, geo, mat, bevel=None, polished_bevel=False):
        me = geo.mesh(P + name, True if bevel else None) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured:  # planar UV, lines along the bracelet (model Y)
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

    # ---- sculpted case, bezel ring, gasket, crystal ----
    c, bz = cfg["case"], cfg["bezel"]
    r_in = bz["profile_rz"][0][0]
    add("case", sculpted_case(tr["case_outline_r_mm"], c, r_in, tr["claws_r_deg"], tr["scoops_r_deg"]), c["material"])
    add("bezel", Geo().lathe([tuple(p) for p in bz["profile_rz"]] + [(bz["profile_rz"][-1][0], 0.0), (r_in, 0.0)], segs=192), bz["material"])
    gk = cfg["gasket"]
    add("gasket", Geo().lathe([(gk["r_in"], gk["z0"]), (gk["r_out"], gk["z0"]), (gk["r_out"], gk["z1"]), (gk["r_in"], gk["z1"])], segs=192), "gasket_black")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial + rehaut, photo map on a planar UV turned back by the photo's rotation ----
    me = Geo().lathe([(0, d["z"]), (d["texture_edge_r"], d["z"]), (d["rehaut_r"], d["rehaut_z"])], segs=192).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    uv, H, pr = me.uv_layers.new(name="UVMap"), d["map_half_mm"], tr["photo_rot_deg"]
    for loop in me.loops:
        x, y = rot(*me.vertices[loop.vertex_index].co[:2], pr)  # model angle a samples the photo at a + photo_rot_deg
        uv.data[loop.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
    add("dial", me, "dial")

    # ---- day-date frame (gold), batons with white lume in gold frames, pentagon marker at 12 ----
    fr, box = cfg["daydate_frame"], tr["daydate_frame"]
    (fx, fy), (fw, fh), wl = box["centre_mm"], box["size_mm"], fr["wall"]
    fx, fy = rot(fx, fy, -pr)
    g = Geo()
    for cx_, cy_, w_, h_ in ((fx, fy + fh / 2 - wl / 2, fw, wl), (fx, fy - fh / 2 + wl / 2, fw, wl),
                             (fx - fw / 2 + wl / 2, fy, wl, fh - 2 * wl), (fx + fw / 2 - wl / 2, fy, wl, fh - 2 * wl)):
        g.prism(rect(cx_, cy_, w_, h_), d["z"], d["z"] + fr["height"])
    add("daydate_frame", g, fr["material"], bevel=0.03)
    ix, ti = cfg["indices"], tr["indices"]
    z0, top = d["z"], d["z"] + ix["height"]
    gold, lume = Geo(), Geo()
    r0, r1, w = ti["lume_inner_mm"], ti["lume_outer_mm"], ti["lume_width_mm"]
    for hour in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11):
        f = ix["frame"]
        gold.prism([rot(x, y, hour * 30) for x, y in rect(0, (r0 + r1) / 2, w + 2 * f, r1 - r0 + 2 * f)], z0, top)
        lume.prism([rot(x, y, hour * 30) for x, y in rect(0, (r0 + r1) / 2, w, r1 - r0)], top, top + ix["lume_height"])
    m12 = ti["marker_12"]

    def pentagon(inset):
        hw, a, b = m12["width_mm"] / 2 - inset, m12["inner_mm"] + inset * 1.6, m12["outer_mm"] - inset
        return [(-hw, b), (-hw, a + hw * 0.9), (0, a), (hw, a + hw * 0.9), (hw, b)]
    gold.prism(pentagon(0), z0, top)
    lume.prism(pentagon(ix["marker_12_lume_inset"]), top, top + ix["lume_height"])
    add("indices", gold, "steel_polished", bevel=0.04)
    add("indices_lume", lume, "lume")

    # ---- applied SEIKO and 5 shield: raised gold plates (shapes fitted in the trace), turned back with the dial ----
    lg = cfg["logo"]
    turn = lambda pts: [list(rot(x, y, -pr)) for x, y in pts]
    for k, hgt in (("logo_seiko", lg["seiko_height"]), ("logo_5_shield", lg["shield_height"])):
        shapes = [{"outer": turn(sh["outer"]), "holes": [turn(hl) for hl in sh["holes"]]} for sh in tr[k + "_shapes"]]
        add(k, plate(shapes, d["z"], d["z"] + hgt, P + k), "steel_polished", bevel=lg["bevel"])

    # ---- hands at the photo's time: gold batons with lume, black inlays and wide tails; needle seconds ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute"):
        h = t[name]
        L, tail, hw, deg, z = h["length_mm"], h["tail_mm"], h["half_width_mm"], h["angle_deg"], hs["z"][name]
        tw = hw * hs["tail_widen"]
        blade = [(hw, 0), (hw, L - hw), (0, L), (-hw, L - hw), (-hw, 0), (-tw, 0), (-tw, -tail), (tw, -tail), (tw, 0)]
        add("hand_" + name, Geo().prism([rot(x, y, deg) for x, y in blade], z, z + th), "steel_polished", bevel=0.02)
        lw = hs["lume_half_width"] * hw
        zt = z + th
        lu, bl = Geo(), Geo()
        lu.prism([rot(x, y, deg) for x, y in rect(0, (hs["lume_from"] + hs["lume_to"]) * L / 2, 2 * lw, (hs["lume_to"] - hs["lume_from"]) * L)], zt, zt + 0.02)
        for a, b in h["black_from_to_mm"]:
            a, b = max(a, hs["lume_from"] * L), min(b, hs["lume_to"] * L)
            bl.prism([rot(x, y, deg) for x, y in rect(0, (a + b) / 2, 2 * lw, b - a)], zt, zt + 0.03)
        bl.prism([rot(x, y, deg) for x, y in rect(0, -(tail + 0.5) / 2, 2 * (tw - 0.12), tail - 0.5 - 0.12)], zt, zt + 0.03)
        add("hand_%s_lume" % name, lu, "lume")
        add("hand_%s_black" % name, bl, "gasket_black")
    h = t["seconds"]
    L, tail, deg, z = h["length_mm"], h["tail_mm"], h["angle_deg"], hs["z"]["seconds"]
    nw, cw = hs["seconds_half_width"], hs["seconds_tail_half_width"]
    add("hand_seconds", Geo().prism([rot(x, y, deg) for x, y in
                                     [(nw, 0), (nw, L - 0.3), (0, L), (-nw, L - 0.3), (-nw, 0), (-cw, -tail * 0.4), (-cw * 0.6, -tail), (cw * 0.6, -tail), (cw, -tail * 0.4)]],
                                    z, z + th), "steel_polished", bevel=0.02)
    hub_r, cap_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, z), (0, z)], segs=48), "steel_polished")
    zc, ch = z + th, hs["hub"]["cap_height"]
    add("hub_cap", Geo().lathe([(0, zc), (hub_r, zc), (hub_r, zc + ch * 0.6), (hub_r * 0.8, zc + ch), (0, zc + ch)], segs=48), "steel_polished")
    add("hub_hole", Geo().lathe([(0, zc + ch), (cap_r, zc + ch), (cap_r, zc + ch + 0.01), (0, zc + ch + 0.01)], segs=32), "gasket_black")

    # ---- crown: fluted cylinder on a radial axis at the traced angle ----
    cw = cfg["crown"]
    a = math.radians(math.degrees(math.atan2(*rot(*tr["crown_box"]["centre_mm"], -pr))) % 360)
    star = [((cw["radius"] if i % 2 == 0 else cw["radius"] - cw["flute_depth"]) * math.cos(math.pi * i / cw["teeth"]),
             (cw["radius"] if i % 2 == 0 else cw["radius"] - cw["flute_depth"]) * math.sin(math.pi * i / cw["teeth"])) for i in range(cw["teeth"] * 2)]
    m = Matrix(((math.cos(a), -math.sin(a), 0), (0, 0, 1), (math.sin(a), math.cos(a), 0))).transposed().to_4x4()
    m.translation = (0, 0, cw["z"])
    add("crown", Geo().prism(star, cw["r_from"], cw["r_to"], m), "steel_polished", bevel=0.15)

    # ---- solid end link under the flat case edge, then two columns of links with the smooth curl ----
    br, el, cs = cfg["bracelet"], cfg["end_link"], tr["case"]
    tip = tr["lug_tip_mm"]["mean"]
    hw_tab = br["half_width"]
    g = Geo()
    y_from = cs["flat_edge_y_mm"] - el["under_case"]
    for sy in (1, -1):  # as wide as the flared first link where it meets it
        g.prism(rect(0, sy * (y_from + tip) / 2, 2 * hw_tab[0][1], tip - y_from), 0.0, el["top_z"])
    add("end_links", g, "steel_brushed", bevel=el["bevel"], polished_bevel=True)

    def hw_at(y):
        for (ya, wa), (yb, wb) in zip(hw_tab, hw_tab[1:]):
            if y <= yb:
                return wa + (wb - wa) * max(0.0, (y - ya) / (yb - ya))
        return hw_tab[-1][1]

    zm = ds * (br["z0"] + br["z1"]) / 2
    box = curl(tip, br["bend_radius"], zm)  # bend starts at the first outer joint (approved curl from SUR419P1)
    za, zb = ds * br["z0"], ds * br["z1"]
    pitch, phase = tr["bracelet_pitch_mm"], tr["bracelet_centre_phase"]
    groups, back, rows = {}, Geo(), 0
    for sy in (1, -1):
        y0 = tip + br["gap"]
        while y0 < br["end_y"] - 0.5:  # backing plate per row, under every column
            y1 = min(y0 + pitch, br["end_y"])
            hb = hw_at((y0 + y1) / 2) - 0.3
            box(back, -hb, hb, y0, y1, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
            y0 = y1
            rows += 1
        for f0, f1, joints, mat in br["columns"]:
            g = groups.setdefault(mat, Geo())
            y0 = tip + br["gap"] + ((phase - 1) * pitch if joints == "centre" else 0.0)
            while y0 < br["end_y"] - 0.5:
                a_, b_ = max(y0, tip + br["gap"]), min(y0 + pitch - br["gap"], br["end_y"])
                if b_ - a_ > 0.5:
                    ym = (a_ + b_) / 2
                    x0, x1 = f0 * hw_at(ym) + (br["gap"] / 2 if f0 else 0), f1 * hw_at(ym) - (br["gap"] / 2 if f1 < 1 else 0)
                    if f0:
                        box(g, x0, x1, a_, b_, za, zb, sy)
                        box(g, -x1, -x0, a_, b_, za, zb, sy)
                    else:
                        box(g, -x1, x1, a_, b_, za, zb, sy)
                y0 += pitch
    for mat, g in groups.items():
        add("bracelet_links_" + mat.split("_")[1], g, mat, bevel=br["bevel"], polished_bevel=mat != "steel_polished")
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    rr = tr["case_outline_r_mm"]
    out = {"width_flanks": round(rr[90] + rr[270], 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "bracelet_rows": rows,
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
