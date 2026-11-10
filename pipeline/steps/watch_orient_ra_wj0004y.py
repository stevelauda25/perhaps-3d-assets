"""watch_orient_ra_wj0004y: build the Orient RA-WJ0004Y (Mako Solar: brushed steel diver case and bracelet, beige bezel insert,
brown sunburst dial, applied lume indices and numerals, sword hands) as a flat-backed front relief.

Params: spec (config/watches/orient-ra-wj0004y.json). Frame as watch_seiko_sfk001: mm, origin = hand pivot, dial faces +z, back
flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, bracelet built at final depth with the
house curl. Parts: the case as one brushed plate from the photo silhouette with lugs either side of the bracelet, a polished
bezel ring with the photo's insert, the dial and rehaut from one photo map (pipeline/orient_ra_wj0004y_dial.py, hands removed),
applied polished frames with lume (traced from the photo's lume), raised ORIENT letters, sword hands with lume, a dark seconds
hand with an orange tip, a fluted crown at 3 and a three-column bracelet. Rebuild with --force after regenerating the photo map.
"""
import json
import math

import bpy
import numpy as np
from mathutils import Matrix

from pipeline.steps.watch_orient_ra_ak0705r10b import ridge
from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled
from pipeline.steps.watch_speedmaster import Geo, ROOT, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    pm = json.loads((ROOT / cfg["photo_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Orient RA-WJ0004Y front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    for key, rough in cfg["photo_roughness"].items():
        mats[key] = photo_material(key, ROOT / cfg["photo_map"], rough)
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
    H = pm["half_mm"]
    photo_uv = lambda x, y, z=0: (0.5 + x / (2 * H), 0.5 + y / (2 * H))

    def add(name, geo, mat, bevel=None, polished_bevel=False, uv_of=None, smooth=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured:  # planar UV, lines along the bracelet (model Y)
            uv, tile = me.uv_layers.new(name="UVMap"), textured[mat]["tile_mm"]
            for loop in me.loops:
                x, y, _ = me.vertices[loop.vertex_index].co
                uv.data[loop.index].uv = (y / tile, -x / tile)
        if mat in cfg["photo_roughness"]:
            uv = me.uv_layers.new(name="UVMap")
            f = uv_of or photo_uv
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
    rg, inner_x, notch = tr["rings_mm"], tr["lug_inner_x_mm"], tr["notch_mm"]
    tip = tr["lug_tip_mm"]["mean"]
    bo_x, bo_y = tr["bezel_offset_mm"]
    sides = {round(p[0], 2): p[1:] for p in tr["silhouette_y_left_right_mm"]}
    q = lambda y: round(round(y * 4) / 4, 2)
    edge0 = lambda y: (sum(sides[q(y)]) / 2 + sum(sides[q(-y)]) / 2) / 2  # both edges, top and bottom averaged
    edge = lambda y: sum(edge0(y + k * 0.25) for k in range(-2, 3)) / 5  # 1 mm running mean

    # ---- case: one brushed plate with lugs either side of the bracelet, open in the middle for the dial ----
    c = cfg["case"]
    ys = [tip - k * 0.25 for k in range(int(2 * tip / 0.25) + 1)]
    right = [(inner_x, notch), (inner_x, tip)] + [(edge(y), y) for y in ys] + [(inner_x, -tip), (inner_x, -notch)]
    outline = right + [(-x, -y) for x, y in right]
    add("case", plate([{"outer": outline, "holes": [circle(c["opening_r"])]}], 0.0, c["top_z"], P + "case"), "steel_brushed",
        bevel=c["bevel"], polished_bevel=True)

    # ---- polished bezel ring, photo insert (mapped about the bezel centre), dial + rehaut, crystal ----
    bz = cfg["bezel"]
    add("bezel_ring", plate([{"outer": circle(rg["bezel_outer"]), "holes": [circle(rg["insert_outer"] - 0.1)]}], bz["z0"], bz["ring_top_z"], P + "bezel_ring"),
        "steel_polished", bevel=0.15)
    ri, ro = rg["insert_inner"], rg["insert_outer"]
    prof = [(ri, bz["z0"]), (ro, bz["z0"]), (ro, bz["insert_top_z"][1]), (ri, bz["insert_top_z"][0]), (ri, bz["z0"])]
    add("bezel_insert", Geo().lathe(prof, segs=192).mesh(P + "bezel_insert", True), "bezel_insert",
        uv_of=lambda x, y, z: photo_uv(x + bo_x, y + bo_y))
    d = cfg["dial"]
    me = upward(Geo().lathe([(0, d["z"]), (rg["dial_edge"], d["z"]), (ri + 0.05, d["rehaut_z"])], segs=192).mesh(P + "dial", True))
    add("dial", me, "dial")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (ri, cr["z0"]), (ri, cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- applied indices and numerals: polished frames with lume, raised ORIENT letters with the photo ----
    ap = cfg["applied"]
    z0, z1 = d["z"], d["z"] + ap["height"]
    add("indices", plate(tr["indices"]["frames"], z0, z1, P + "indices"), "steel_polished", bevel=ap["frame_bevel"])
    add("index_lume", plate(tr["indices"]["lume"], z1, z1 + ap["lume_height"], P + "index_lume"), "lume")
    add("logo", plate(tr["logo"], z0, z0 + ap["logo_height"], P + "logo"), "dial")

    # ---- hands at the photo's time: sword frames with lume, dark seconds needle with an orange tip ----
    hs, th, lh = cfg["hands"], cfg["hands"]["thickness"], cfg["hands"]["lume_height"]

    def side_poly(stations, deg):
        return [rot(w, r, deg) for r, w in stations] + [rot(-w, r, deg) for r, w in stations[::-1]]
    for name in ("hour", "minute"):
        h, z = tr["hands"][name], hs["z"][name]
        add("hand_" + name, Geo().prism(side_poly(h["stations_mm"], h["angle_deg"]), z, z + th), "steel_polished", bevel=0.03)
        add("hand_%s_lume" % name, Geo().prism(side_poly(h["lume_mm"], h["angle_deg"]), z + th, z + th + lh), "lume")
    h, z = tr["hands"]["seconds"], hs["z"]["seconds"]
    cut = h["orange_from_mm"]
    steel = [s for s in h["stations_mm"] if s[0] <= cut]
    w_cut = float(np.interp(cut, *np.array(h["stations_mm"]).T))
    orange = [(cut, w_cut)] + [tuple(s) for s in h["stations_mm"] if s[0] > cut]
    g = ridge(Geo(), [tuple(s) for s in steel] + [(cut, w_cut)], z, th, 0.6, h["angle_deg"])
    g.lathe([(0, z), (hs["seconds_disc_r"], z), (hs["seconds_disc_r"], z + th), (0, z + th)], segs=64)
    add("hand_seconds", g, "steel_dark", bevel=0.02)
    add("hand_seconds_tip", ridge(Geo(), orange, z, th, 0.6, h["angle_deg"]), "orange", bevel=0.02)
    hub_r, cap_r = tr["hub_mm"]
    zc = z + th
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, zc), (0, zc)], segs=48), "steel_polished")
    add("hub_cap", Geo().lathe([(0, zc), (cap_r * 1.6, zc), (cap_r * 1.6, zc + hs["hub_cap_height"] * 0.6), (cap_r, zc + hs["hub_cap_height"]), (0, zc + hs["hub_cap_height"])], segs=48),
        "steel_polished")

    # ---- crown on the 3 o'clock axis: neck, fluted body, rounded end ----
    cw, tc = cfg["crown"], tr["crown"]
    case_r = edge(0.0)
    m = Matrix(((0, -1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_4x4()  # local z along +x, local y up
    m.translation = (0.0, tc["centre_y_mm"], cw["z"])
    R0, (r1, r2) = tc["radius_mm"], tc["x_from_to_mm"]
    r1 += cw["gap"]
    add("crown_neck", Geo().lathe([(0, case_r - 1.0), (R0 * cw["neck_fraction"], case_r - 1.0), (R0 * cw["neck_fraction"], r1 + 0.1), (0, r1 + 0.1)], segs=48, m=m),
        "steel_polished", smooth=True)
    star = [((R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.cos(math.pi * i / cw["teeth"]),
             (R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.sin(math.pi * i / cw["teeth"])) for i in range(cw["teeth"] * 2)]
    add("crown", Geo().prism(star, r1, r2 - 0.5, m), "steel_polished", bevel=0.08)
    add("crown_end", Geo().lathe([(0, r2 - 0.5), (R0 - 0.15, r2 - 0.5), (R0 - 0.8, r2), (0, r2)], segs=48, m=m), "steel_polished", smooth=True)

    # ---- three columns with the house curl: outer and centre links from their photo joints, end links from the case edge ----
    br, el = cfg["bracelet"], cfg["end_link"]
    fc, pitch, gap = tr["bracelet_centre_fraction"], tr["bracelet_pitch_mm"], br["gap"]
    outer0, centre0 = tr["bracelet_outer_start_mm"], tr["bracelet_centre_start_mm"]
    end_y = tip + br["bend_radius"] * br["arc_over_radius"]
    sides_b = [sorted((abs(y), hw) for y, hw in tr["bracelet_half_y_mm"] if (y > 0) == top) for top in (True, False)]
    hw_at = lambda s: min(sum(np.interp(s, [p[0] for p in sd], [p[1] for p in sd]) for sd in sides_b) / 2, inner_x)

    def columns(hw):
        return [(-fc * hw, fc * hw, "centre"), (fc * hw + gap, hw, "outer"), (-hw, -(fc * hw + gap), "outer")]

    zm = ds * (br["z0"] + br["z1"]) / 2
    box = curl(tip + br["bend_after_tip"], br["bend_radius"], zm)
    za, zb = ds * br["z0"], ds * br["z1"]
    links, ends, back = Geo(), Geo(), Geo()
    rows = 0
    for sy in (1, -1):
        for x0, x1, kind in columns(inner_x - 0.05):
            box(ends, x0, x1, notch - 1.0, (outer0 if kind == "outer" else centre0) - gap, 0.0, ds * el["top_z"], sy)
        for kind, start in (("outer", outer0), ("centre", centre0)):
            y0 = start
            while y0 < end_y - 0.5:
                y1 = min(y0 + pitch - gap, end_y)
                hw = hw_at((y0 + y1) / 2)
                for x0, x1, k in columns(hw):
                    if k == kind:
                        box(links, x0, x1, y0, y1, za, zb, sy)
                if kind == "outer":
                    box(back, -(hw - 0.3), hw - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                y0 = y1 + gap
    add("bracelet_end_links", ends, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_links", links, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * edge(0.0), 3), "lug_width": round(2 * hw_at(tip + 1.0), 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.5, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "bracelet_rows": rows, "bracelet_end_y_mm": end_y,
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
