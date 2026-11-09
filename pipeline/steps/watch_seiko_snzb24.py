"""watch_seiko_snzb24: build the Seiko 5 Sports SNZB24J1 (two-tone, white dial) as a flat-backed front relief.

Params: spec (config/watches/seiko-snzb24j1.json). Same build as watch_seiko_snzb26 (same case): mm, origin = dial centre, dial
faces +z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, bracelet built at final
depth with the smooth curl. Differences: two-tone materials per part from the spec (steel case and bezel top; gold crystal ring,
knurled skirt, pads, indices, hands, crown and bracelet stripes); solid gold batons with a pointed outer end; a black frame round
the lume pip at 12; bracelet columns (with their materials) from the spec. Rebuild with --force after regenerating the dial map.
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled
from pipeline.steps.watch_seiko_snz450 import sculpted_case
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def arc(r, a0, a1, n=12):
    return [(r * math.sin(math.radians(a0 + (a1 - a0) * i / n)), r * math.cos(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
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

    # ---- case (round, hidden under the bezel except the lugs), bezel, knurled skirt, pads, print, crystal ----
    c, bz, tb = cfg["case"], cfg["bezel"], tr["bezel"]
    add("case", sculpted_case(tr["case_outline_r_mm"], c, c["r_in"], [], []), c["material"])
    for part in ("crystal_ring", "top"):  # gold sloped ring round the crystal, then the flat steel numeral ring
        prof = [tuple(p) for p in bz[part]["profile_rz"]]
        add("bezel_" + part, Geo().lathe(prof + [(prof[-1][0], bz["z_bottom"]), (prof[0][0], bz["z_bottom"])], segs=192), bz[part]["material"])
    sk, n = bz["skirt"], bz["skirt"]["teeth"]
    star = [((sk["r_out"] if i % 2 == 0 else sk["r_out"] - sk["depth"]) * math.sin(math.pi * i / n),
             (sk["r_out"] if i % 2 == 0 else sk["r_out"] - sk["depth"]) * math.cos(math.pi * i / n)) for i in range(2 * n)]
    hole = arc(sk["r_in"], 0, 360, 96)[:-1]
    add("bezel_skirt", plate([{"outer": star, "holes": [hole[::-1]]}], sk["z0"], sk["z1"], P + "bezel_skirt"), sk["material"])
    top, pad = bz["top_z"], bz["pad"]
    r0, r1, hd = tb["block_r_mm"][0], tb["block_r_mm"][1], tb["block_half_deg"]
    pads = [{"outer": arc(r0, a + hd, a - hd) + arc(r1, a - hd, a + hd), "holes": []} for a in tr["bezel_blocks_deg"]]
    add("bezel_pads", plate(pads, top - 0.2, top + pad["height"], P + "bezel_pads"), pad["material"], bevel=pad["bevel"])
    on_pad = lambda sh: any(abs((math.degrees(math.atan2(*map(lambda v: sum(v) / len(v), zip(*sh["outer"])))) - a + 180) % 360 - 180) < hd
                            for a in tr["bezel_blocks_deg"])
    for name, shapes, z in (("bezel_print", [s for s in tr["bezel_print_shapes"] if not on_pad(s)], top),
                            ("bezel_pad_print", [s for s in tr["bezel_print_shapes"] if on_pad(s)], top + pad["height"])):
        add(name, plate(shapes, z - 0.1, z + bz["print_height"], P + name), "gasket_black")
    bp = tr["bezel_pip"]
    (px, py), pr_ = bp["centre_mm"], bp["lume_r_mm"]
    zp = top + pad["height"]
    (f0, f1), (w0, w1) = bp["frame_r_mm"], bp["frame_half_w_mm"]
    add("bezel_pip_frame", plate([{"outer": [(-w0, f0), (w0, f0), (w1, f1), (-w1, f1)], "holes": []}], zp - 0.1, zp + bz["print_height"],
                                 P + "bezel_pip_frame"), "gasket_black")
    add("bezel_pip", Geo().lathe([(0, zp - 0.1), (pr_, zp - 0.1), (pr_, zp + 0.06), (0, zp + 0.06)], segs=32,
                                 m=Matrix.Translation((px, py, 0))), "lume")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial + rehaut, photo map on a planar UV ----
    me = Geo().lathe([(0, d["z"]), (d["texture_edge_r"], d["z"]), (d["rehaut_r"], d["rehaut_z"])], segs=192).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    uv, H = me.uv_layers.new(name="UVMap"), d["map_half_mm"]
    for loop in me.loops:
        x, y = me.vertices[loop.vertex_index].co[:2]
        uv.data[loop.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
    add("dial", me, "dial")

    # ---- day-date frame, batons with cream lume in gold frames (wider at 6 and 9), double baton at 12 ----
    fr, box = cfg["daydate_frame"], tr["daydate_frame"]
    (fx, fy), (fw, fh), wl = box["centre_mm"], box["size_mm"], fr["wall"]
    g = Geo()
    for cx_, cy_, w_, h_ in ((fx, fy + fh / 2 - wl / 2, fw, wl), (fx, fy - fh / 2 + wl / 2, fw, wl),
                             (fx - fw / 2 + wl / 2, fy, wl, fh - 2 * wl), (fx + fw / 2 - wl / 2, fy, wl, fh - 2 * wl)):
        g.prism(rect(cx_, cy_, w_, h_), d["z"], d["z"] + fr["height"])
    add("daydate_frame", g, fr["material"], bevel=0.03)
    ix, ti = cfg["indices"], tr["indices"]
    z0, zt = d["z"], d["z"] + ix["height"]
    gold = Geo()
    r0, r1 = ti["lume_inner_mm"], ti["lume_outer_mm"]
    for hour in (1, 2, 4, 5, 6, 7, 8, 9, 10, 11):  # solid faceted gold batons, pointed outer end
        hw = (ti["wide_width_mm"] if hour in (6, 9) else ti["lume_width_mm"]) / 2
        pt = hw * ix["point_ratio"]
        gold.prism([rot(x, y, hour * 30) for x, y in [(-hw, r0), (hw, r0), (hw, r1 - pt), (0, r1), (-hw, r1 - pt)]], z0, zt)
    m12 = ti["marker_12"]
    hw, a, b, tip = m12["width_mm"] / 2, m12["inner_mm"], m12["outer_mm"], m12["tip_mm"]
    gold.prism([(-hw, a), (hw, a), (hw, b), (0, tip), (-hw, b)], z0, zt)
    add("indices", gold, "gold_polished", bevel=ix["bevel"])
    g = Geo()  # groove splitting the double baton at 12
    g.prism(rect(0, (a + b) / 2, ix["groove_12"], b - a - 0.2), zt - 0.05, zt + 0.005)
    add("indices_groove", g, "gasket_black")

    # ---- applied SEIKO and 5 shield: raised gold plates (shapes fitted in the trace) ----
    lg = cfg["logo"]
    for k, hgt in (("logo_seiko", lg["seiko_height"]), ("logo_5_shield", lg["shield_height"])):
        add(k, plate(tr[k + "_shapes"], d["z"], d["z"] + hgt, P + k), "gold_polished", bevel=lg["bevel"])

    # ---- hands at the photo's time: gold sword hands with two lume windows; needle seconds with a lume disc on the tail ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], json.loads(json.dumps(tr["hands"]))
    for name, deg in hs.get("pose_deg", {}).items():  # optional time from another photo (SNZB26J1 gold version); shapes stay traced
        if name != "note":
            t[name]["angle_deg"] = deg
    for name in ("hour", "minute"):
        h = t[name]
        L, tail, hw, deg, z = h["length_mm"], h["tail_mm"], h["half_width_mm"], h["angle_deg"], hs["z"][name]
        tp = hw * hs["tip_ratio"]
        blade = [(hw, 0), (hw, L - tp), (0, L), (-hw, L - tp), (-hw, 0), (-hw * 0.8, 0), (-hw * 0.8, -tail), (hw * 0.8, -tail), (hw * 0.8, 0)]
        add("hand_" + name, Geo().prism([rot(x, y, deg) for x, y in blade], z, z + th), "gold_polished", bevel=0.02)
        lw, (la, lb), zt_ = hw - hs["frame"], h["lume_from_to_mm"], z + th
        lb = min(lb, L - tp * 0.6)
        lu, bl = Geo(), Geo()
        cuts = sorted(h["black_from_to_mm"])
        segs, s0 = [], la
        for ca, cb in cuts:  # lume between the black bars
            if cb <= la:
                continue
            segs.append((s0, max(s0, ca)))
            s0 = cb
        segs.append((s0, lb))
        for sa, sb in segs:
            if sb - sa > 0.2:
                lu.prism([rot(x, y, deg) for x, y in rect(0, (sa + sb) / 2, 2 * lw, sb - sa)], zt_, zt_ + 0.02)
        for ca, cb in cuts:
            bl.prism([rot(x, y, deg) for x, y in rect(0, (ca + cb) / 2, 2 * lw, cb - ca)], zt_, zt_ + 0.02)
        add("hand_%s_lume" % name, lu, "lume")
        add("hand_%s_bar" % name, bl, "gold_polished")  # gold bars between the lume windows (black on SNZB26J1)
    h = t["seconds"]
    L, deg, z, nw = h["length_mm"], h["angle_deg"], hs["z"]["seconds"], h["half_width_mm"]
    add("hand_seconds", Geo().prism([rot(x, y, deg) for x, y in [(nw, 0), (nw, L - 0.3), (0, L), (-nw, L - 0.3), (-nw, 0), (-nw, -h["disc_at_mm"]), (nw, -h["disc_at_mm"])]],
                                    z, z + th), "gold_polished", bevel=0.02)
    dx, dy = rot(0, -h["disc_at_mm"], deg)
    rd = h["disc_r_mm"]
    add("hand_seconds_disc", Geo().lathe([(0, z), (rd + hs["frame"], z), (rd + hs["frame"], z + th), (0, z + th)], segs=32, m=Matrix.Translation((dx, dy, 0))), "gold_polished")
    add("hand_seconds_lume", Geo().lathe([(0, z + th), (rd, z + th), (rd, z + th + 0.02), (0, z + th + 0.02)], segs=32, m=Matrix.Translation((dx, dy, 0))), "lume")
    hub_r, cap_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, z), (0, z)], segs=48), "gold_polished")
    zc, ch = z + th, hs["hub"]["cap_height"]
    add("hub_cap", Geo().lathe([(0, zc), (hub_r, zc), (hub_r, zc + ch * 0.6), (hub_r * 0.8, zc + ch), (0, zc + ch)], segs=48), "gold_polished")
    add("hub_hole", Geo().lathe([(0, zc + ch), (cap_r, zc + ch), (cap_r, zc + ch + 0.01), (0, zc + ch + 0.01)], segs=32), "gasket_black")

    # ---- crown: fluted cylinder on a radial axis at the traced angle ----
    cw = cfg["crown"]
    a = math.atan2(*tr["crown_box"]["centre_mm"])
    star = [((cw["radius"] if i % 2 == 0 else cw["radius"] - cw["flute_depth"]) * math.cos(math.pi * i / cw["teeth"]),
             (cw["radius"] if i % 2 == 0 else cw["radius"] - cw["flute_depth"]) * math.sin(math.pi * i / cw["teeth"])) for i in range(cw["teeth"] * 2)]
    m = Matrix(((math.cos(a), -math.sin(a), 0), (0, 0, 1), (math.sin(a), math.cos(a), 0))).transposed().to_4x4()
    m.translation = (0, 0, cw["z"])
    add("crown", Geo().prism(star, cw["r_from"], cw["r_to"], m), "gold_polished", bevel=0.15)

    # ---- end link between the lugs, then three columns of links with the smooth curl ----
    br, el, cs = cfg["bracelet"], cfg["end_link"], tr["case"]
    tip = tr["lug_tip_mm"]["mean"]
    hw_tab = br["half_width"]
    g = Geo()
    y_from = cs["flat_edge_y_mm"] - el["under_case"]
    for sy in (1, -1):
        g.prism(rect(0, sy * (y_from + tip) / 2, 2 * hw_tab[0][1], tip - y_from), 0.0, el["top_z"])
    add("end_links", g, "steel_brushed", bevel=el["bevel"], polished_bevel=True)
    g = Geo()  # gold stripes run on up to the bezel
    f0, f1 = el["stripe"]
    for sy in (1, -1):
        for sx in (1, -1):
            g.prism(rect(sx * (f0 + f1) / 2 * hw_tab[0][1], sy * (y_from + tip) / 2, (f1 - f0) * hw_tab[0][1], tip - y_from), el["top_z"] - 0.2, el["top_z"] + 0.1)
    add("end_link_stripes", g, "gold_polished", bevel=0.1)

    def hw_at(y):
        for (ya, wa), (yb, wb) in zip(hw_tab, hw_tab[1:]):
            if y <= yb:
                return wa + (wb - wa) * max(0.0, (y - ya) / (yb - ya))
        return hw_tab[-1][1]

    zm = ds * (br["z0"] + br["z1"]) / 2
    box = curl(tip, br["bend_radius"], zm)  # bend starts at the first outer joint (approved curl from SUR419P1)
    za, zb = ds * br["z0"], ds * br["z1"]
    pitch, phase = tr["bracelet_pitch_mm"], tr["bracelet_centre_phase"]
    end_y = tip + 2.2 * br["bend_radius"]
    columns = br["columns"]
    groups, back, rows = {}, Geo(), 0
    for sy in (1, -1):
        y0 = tip + br["gap"]
        while y0 < end_y - 0.5:  # backing plate per row, under every column
            y1 = min(y0 + pitch, end_y)
            hb = hw_at((y0 + y1) / 2) - 0.3
            box(back, -hb, hb, y0, y1, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
            y0 = y1
            rows += 1
        for f0, f1, joints, mat in columns:
            g = groups.setdefault(mat, Geo())
            y0 = tip + br["gap"] + ((phase - 1) * pitch if joints == "centre" else 0.0)
            while y0 < end_y - 0.5:
                a_, b_ = max(y0, tip + br["gap"]), min(y0 + pitch - br["gap"], end_y)
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
        add("bracelet_links_" + mat, g, mat, bevel=br["bevel"], polished_bevel=mat in textured)
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"bezel_diameter": round(2 * bz["skirt"]["r_out"], 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "bracelet_rows": rows, "end_y_mm": round(end_y, 2),
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
