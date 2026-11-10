"""watch_orient_ra_aa0c02l19b: build the Orient RA-AA0C02L19B (brushed bezel, blue sunburst day-date dial, crown guards, steel
bracelet) as a flat-backed front relief.

Params: spec (config/watches/orient-ra-aa0c02l19b.json). Same frame, pose, 2.5D depth scale, materials, lugs, end links and
three-column bracelet curl as watch_orient_ra_wj0002l. Parts from the photo: a polished case flank under a flat brushed bezel,
a dark ring at the crystal edge, crown guards above and below a fluted crown, applied rounded bars as polished frames with a grey
lume inlay (the 12 a wider solid faceted bar), a polished day-date frame, hour and minute swords as polished frames with a lume
inlay, a thin seconds needle with a short tail, a stepped hub. The dial (sunburst, minute track, printed lume squares, prints,
day-date) is the photo map from pipeline/orient_ra_aa0c02l19b_dial.py. Rebuild with --force after regenerating the map.
"""
import json
import math

import bpy
import numpy as np
from mathutils import Matrix

from pipeline.steps.watch_orient_faa02004b9 import hand_poly
from pipeline.steps.watch_orient_ra_wj0002l import inset
from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def rrect(cx, cy, w, h, r, n=6):
    """Rounded rectangle centred on (cx, cy), corner radius r, counter-clockwise."""
    pts = []
    for qx, qy, a0 in ((1, 1, 0), (-1, 1, 90), (-1, -1, 180), (1, -1, 270)):
        ccx, ccy = cx + qx * (w / 2 - r), cy + qy * (h / 2 - r)
        pts += [(ccx + r * math.cos(math.radians(a0 + 90 * k / n)), ccy + r * math.sin(math.radians(a0 + 90 * k / n))) for k in range(n + 1)]
    return pts


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    dm = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | " + cfg["model"] + " front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    d = cfg["dial"]
    mats["dial"] = photo_material("dial_photo", ROOT / cfg["dial_map"], d["roughness"])
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

    def add(name, geo, mat, bevel=None, polished_bevel=False, smooth=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured:  # planar UV in mm / tile, lines along the bracelet (model Y)
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

    # ---- polished case flank, flat brushed bezel, dark ring at the crystal edge, crystal ----
    c, bz = cfg["case"], cfg["bezel"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), "steel_polished", smooth=True)
    add("bezel", Geo().lathe([tuple(p) for p in bz["profile_rz"]], segs=192), "steel_satin", smooth=True)
    gk = cfg["gasket"]
    add("gasket", Geo().lathe([(gk["r_in"], gk["z0"]), (gk["r_out"], gk["z0"]), (gk["r_out"], gk["z1"]), (gk["r_in"], gk["z1"])], segs=192), "gasket_black")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial + grey inner slope (rehaut), photo map on a planar UV about the index ring centre ----
    H = dm["half_size_mm"]
    me = Geo().lathe([(0, d["z"]), (tr["rehaut_mm"], d["z"]), (d["rehaut_r"], d["rehaut_z"])], segs=192).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    uv = me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        x, y, _ = me.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
    add("dial", me, "dial")

    # ---- applied rounded bars: polished frame, grey lume inlay; solid faceted bar at 12; polished day-date frame ----
    ix, ti = cfg["indices"], tr["indices"]
    z0, z1 = d["z"], d["z"] + ix["height"]
    b, fw = ti["bar_mm"], ti["frame_mm"]
    shapes, lume = [], Geo()
    for hr in range(1, 12):
        r0 = ti["index_3_inner_mm"] if hr == 3 else b["inner"]
        outer = [rot(x, y, hr * 30) for x, y in rrect(0, (r0 + b["outer"]) / 2, 2 * b["half"], b["outer"] - r0, b["half"] * 0.7)]
        hole = [rot(x, y, hr * 30) for x, y in rrect(0, (r0 + b["outer"]) / 2, 2 * (b["half"] - fw), b["outer"] - r0 - 2 * fw, (b["half"] - fw) * 0.7)]
        shapes.append({"outer": [list(p) for p in outer], "holes": [[list(p) for p in hole]]})
        lume.prism(hole, z0, z1 - ix["lume_recess"])
    dd = tr["daydate"]
    dx0, dy0, dx1, dy1 = dd["x0_y0_x1_y1_mm"]
    k, xd = dd["frame_mm"], dd["divider_x_mm"]
    outer = [(dx0, dy1), (dx1, dy1), (dx1, dy0), (dx0, dy0)]
    holes = [[(dx0 + k, dy1 + k), (xd - k / 2, dy1 + k), (xd - k / 2, dy0 - k), (dx0 + k, dy0 - k)],
             [(xd + k / 2, dy1 + k), (dx1 - k, dy1 + k), (dx1 - k, dy0 - k), (xd + k / 2, dy0 - k)]]
    shapes.append({"outer": [list(p) for p in outer], "holes": [[list(p) for p in h] for h in holes]})
    add("indices", plate(shapes, z0, z1, P + "indices"), "steel_polished")
    add("index_lume", lume, "lume_index")
    q = ti["index_12_mm"]
    g = Geo()
    for sx in (1, -1):  # two facets meeting at a ridge on the centre line
        pts = [(0.0, q["inner"]), (sx * q["half"], q["inner"]), (sx * q["half"], q["outer"]), (0.0, q["outer"])]
        slab(g, pts, z0, lambda x, y: z1 + ix["ridge"] * (x == 0.0))
    add("index_12", g, "steel_polished", bevel=0.04)

    # ---- hands at the photo's time: polished sword frames with a lume inlay, thin seconds with a short tail, stepped hub ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]

    def hand(name, poly, deg, z, mat, h=th):
        add(name, Geo().prism([rot(x, y, deg) for x, y in poly], z, z + h), mat, bevel=0.02 if mat == "steel_polished" else None)

    for name in ("hour", "minute"):
        h = t[name]
        deg, z = h["angle_deg"], hs["z"][name]
        hand("hand_" + name, hand_poly(h["outline_mm"]), deg, z, "steel_polished")
        hand("hand_%s_lume" % name, hand_poly(h["lume_mm"]), deg, z + th, "lume_hands", hs["lume_height"])
    h = t["seconds"]
    L, tail, deg, z = h["length_mm"], h["tail_mm"], h["angle_deg"], hs["z"]["seconds"]
    nw, cw = h["half_width_mm"], h["tail_half_width_mm"]
    hand("hand_seconds", [(-nw, 0), (nw, 0), (nw, L - 0.3), (0, L), (-nw, L - 0.3)], deg, z, "steel_polished")
    hand("hand_seconds_tail", [(-cw, -tail), (cw, -tail), (cw, 0.5), (-cw, 0.5)], deg, z, "steel_polished")
    collar_r, cap_r = tr["hub_radius_mm"]
    zh = hs["z"]["hour"] + th
    add("hub", Geo().lathe([(0, d["z"]), (collar_r, d["z"]), (collar_r, zh), (collar_r * 0.72, zh), (collar_r * 0.72, zh + 0.08),
                            (0, zh + 0.08)], segs=64), "steel_polished")
    zc = z + th
    add("hub_cap", Geo().lathe([(0, zh), (cap_r, zh), (cap_r, zc + 0.1), (cap_r * 0.6, zc + 0.18), (0, zc + 0.18)], segs=48), "steel_polished")

    # ---- crown on the 3 o'clock axis (neck, fluted body, smooth cap) between two crown guards ----
    cw_, tc = cfg["crown"], tr["crown"]
    R0, teeth = tc["radius_mm"], tc["teeth"]
    star = [((R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.cos(math.pi * i / teeth),
             (R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.sin(math.pi * i / teeth)) for i in range(teeth * 2)]
    m = Matrix(((0, -1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_4x4()  # local z along +x, local y up
    m.translation = (0.0, 0.0, cw_["z"])
    r_case = tr["case"]["radius_mm"]
    add("crown_neck", Geo().lathe([(0, r_case - 1.0), (R0 * 0.6, r_case - 1.0), (R0 * 0.6, cw_["r_from"] + 0.1), (0, cw_["r_from"] + 0.1)], segs=48, m=m),
        "steel_polished", smooth=True)
    add("crown", Geo().prism(star, cw_["r_from"], tc["cap_from_mm"], m), "steel_polished", bevel=0.1)
    add("crown_cap", Geo().lathe([(0, tc["cap_from_mm"]), (R0 * 0.85, tc["cap_from_mm"]), (R0 * 0.85, tc["to_mm"]), (0, tc["to_mm"])], segs=48, m=m),
        "steel_polished", bevel=0.08)
    gd = tc["guard_mm"]
    guard = [tuple(p) for p in cfg["crown_guard"]["outline_mm"]]
    assert abs(guard[0][1] - gd["from_axis"]) < 0.3 and abs(max(x for x, _ in guard) - gd["outer_x"]) < 0.3
    g = Geo()
    for sy in (1, -1):
        slab(g, [(x, sy * y) for x, y in guard], 0.0, lambda x, y: cfg["crown_guard"]["top_z"])
    add("crown_guards", g, "steel_brushed", bevel=cfg["crown_guard"]["bevel"], polished_bevel=True)

    # ---- lugs: outline by depth from the tip (top and bottom averaged), brushed top sloping to the tip, polished chamfer ----
    lg, tl = cfg["lug"], tr["lug"]
    tip, xi = tl["tip_mm"], tl["inner_x_mm"]
    outer = [(w, tip - dd_) for dd_, w in tl["half_width_by_depth_mm"] if math.hypot(w, tip - dd_) > r_case - lg["into_case"]]  # until it runs into the case
    outer = [(lg["tip_outer_x"], tip)] + outer
    poly = [(xi, tip)] + outer + [(xi, outer[-1][1])]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * min(1.0, max(0.0, (abs(y) - lg["slope_from_y"]) / (tip - lg["slope_from_y"])))
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in poly], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

    # ---- three-column bracelet: brushed outer and centre links, centre joints `shift` nearer the case ----
    br, el = cfg["bracelet"], cfg["end_link"]
    ch, shift, gap = tr["bracelet_centre_half_mm"], tr["bracelet_centre_joint_shift_mm"], br["gap"]
    ss, hws = np.array(tr["bracelet_half_width_by_s_mm"]).T
    hw_at = lambda s: min(float(np.interp(s, ss, hws)), el["half_width"])  # the photo's taper, past its end the last width
    end = Geo()
    for sy in (1, -1):
        M = Matrix.Translation((0, sy * (el["from_y"] + tip) / 2, 0))
        for sx in (1, -1):
            end.prism(rect(sx * (ch + gap + el["half_width"]) / 2, 0, el["half_width"] - ch - gap, tip - el["from_y"]), 0.0, el["top_z"], M)
        y1 = tip - shift - gap
        end.prism(rect(0, sy * (el["from_y"] + y1) / 2, 2 * ch, y1 - el["from_y"]), 0.0, el["top_z"])
    add("end_links", end, "steel_brushed", bevel=el["bevel"], polished_bevel=True)

    zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]
    bent_box = curl(tip + br.get("bend_after_tip", 0.0), R, zm)
    pitch = tr["bracelet_pitch_mm"]
    links, back = Geo(), Geo()
    rows = 0
    za, zb = ds * br["z0"], ds * br["z1"]
    for sy in (1, -1):
        for kind, start in (("outer", tip), ("centre", tip - shift)):
            y0 = start
            while y0 < br["end_y"] - 0.5:
                y1 = min(y0 + pitch - gap, br["end_y"])
                hw_ = hw_at((y0 + y1) / 2)
                if kind == "outer":
                    for sx in (1, -1):
                        x0, x1 = sorted((sx * (ch + gap), sx * hw_))
                        bent_box(links, x0, x1, y0, y1, za, zb, sy)
                    bent_box(back, -(hw_ - 0.3), hw_ - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                else:
                    bent_box(links, -ch, ch, y0, y1, za, zb + ds * br["centre_raise"], sy)
                y0 = y1 + gap
    add("bracelet_links", links, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "lug_to_lug": round(2 * tip, 3),
           "end_link_width": round(2 * el["half_width"], 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "bracelet_rows": rows,
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
