"""watch_seiko_snkm87: build the Seiko 5 SNKM87K1 as a flat-backed front relief (like the other GLBs in models/watches/).

Params: spec (config/watches/seiko-snkm87k1.json). Same frame, pose, 2.5D depth scale, materials and bracelet curl as
watch_seiko_sur419_front, whose structure it follows; this model differs in the parts: a sloped chapter ring around a flat
patterned centre, faceted batons (double at 12, none at 3) plus a white lume block at every hour on the chapter ring edge,
faceted dauphine hour and minute hands with pointed counterweights, a needle seconds hand with a paddle tail, a polished
day-date frame, and a three-column bracelet whose centre joints sit further from the case than the outer ones.
Plan sizes come from config/watches/seiko-snkm87k1-trace.json; heights from the spec. The dial is the photo map from
pipeline/seiko_snkm87_dial.py. Rebuild with --force after regenerating the dial map (the map is not part of the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    scene = bpy.context.scene
    coll = bpy.data.collections.new("WATCH | Seiko 5 SNKM87K1 front relief")
    scene.collection.children.link(coll)
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

    def brushed_uv(me, tile_mm):
        """Planar UV in mm / tile, turned 90 deg so the texture's lines (along image X) run along the bracelet (model Y)."""
        uv = me.uv_layers.new(name="UVMap")
        for loop in me.loops:
            x, y, _ = me.vertices[loop.vertex_index].co
            uv.data[loop.index].uv = (y / tile_mm, -x / tile_mm)

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"])
    pose.scale = (0.001,) * 3
    ds = cfg["pose"]["depth_scale"]

    def add(name, geo, mat, bevel=None, polished_bevel=False):
        me = geo.mesh(P + name, True if bevel else None) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured:
            brushed_uv(me, textured[mat]["tile_mm"])
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

    # ---- case (full circle: the end links sit lower and run under it), gasket, crystal ----
    c, lg = cfg["case"], cfg["lug"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), c["material"])
    gk = cfg["gasket"]
    add("gasket", Geo().lathe([(gk["r_in"], gk["z0"]), (gk["r_out"], gk["z0"]), (gk["r_out"], gk["z1"]), (gk["r_in"], gk["z1"])], segs=192), "gasket_black")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial: flat patterned centre, small step, sloped chapter ring up to the crystal; photo map on a planar UV ----
    S = tr["scale_px_per_mm"]
    H = math.ceil(tr["crystal_ring"]["radius_mm"] * S) / S  # the map is a square of whole pixels out to the crystal ring
    edge = tr["dial_edge_radius_mm"]
    g = Geo().lathe([(0, d["z"]), (edge, d["z"]), (d["chapter_step_r"], d["chapter_step_z"]), (H, d["chapter_top_z"])], segs=192)
    me = g.mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    uv = me.uv_layers.new(name="UVMap")
    for loop in me.loops:
        x, y, _ = me.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
    add("dial", me, "dial")

    # ---- faceted batons (double at 12, none at 3 beside the day-date); a lume block at every hour on the chapter ring ----
    ix, ti = cfg["indices"], tr["indices"]
    z0, top = d["z"], d["z"] + ix["height"]
    r0, r1 = ti["inner_mm"], ti["outer_mm"]
    g = Geo()

    def baton(cx, w, hour):
        for sx in (1, -1):  # two facets meeting at a ridge along the bar
            half = [(cx, r0), (cx + sx * w / 2, r0), (cx + sx * w / 2, r1), (cx, r1)]
            slab(g, [rot(x, y, hour * 30) for x, y in half], z0, lambda x, y, cx=cx, h=hour: top + ix["ridge"] * _on_line(x, y, h, cx))

    for hour in range(1, 13):
        if hour == 12:
            off = (ti["bar_12_mm"] + ti["gap_12_mm"]) / 2
            baton(-off, ti["bar_12_mm"], hour)
            baton(off, ti["bar_12_mm"], hour)
        elif hour != 3:
            baton(0.0, ti["width_mm"], hour)
    add("indices", g, "steel_polished", bevel=0.04)
    blocks, lume = Geo(), Geo()
    b0, b1, bw, bz, wl = ti["block_inner_mm"], ti["block_outer_mm"], ti["block_width_mm"], ix["block_z0"], ix["block_wall"]
    for hour in range(1, 13):
        turn = lambda poly: [rot(x, y, hour * 30) for x, y in poly]
        blocks.prism(turn(rect(0, (b0 + b1) / 2, bw, b1 - b0)), bz, bz + ix["block_height"])
        lume.prism(turn(rect(0, (b0 + b1) / 2, bw - 2 * wl, b1 - b0 - 2 * wl)), bz + ix["block_height"], bz + ix["block_height"] + 0.03)
    add("index_blocks", blocks, "steel_polished", bevel=0.04)
    add("index_lume", lume, "lume")
    fr, box = cfg["daydate_frame"], tr["daydate_frame"]
    (fx, fy), (fw, fh), wl = box["centre_mm"], box["size_mm"], fr["wall"]
    g = Geo()
    for cx_, cy_, w_, h_ in ((fx, fy + fh / 2 - wl / 2, fw, wl), (fx, fy - fh / 2 + wl / 2, fw, wl),
                             (fx - fw / 2 + wl / 2, fy, wl, fh - 2 * wl), (fx + fw / 2 - wl / 2, fy, wl, fh - 2 * wl)):
        g.prism(rect(cx_, cy_, w_, h_), d["z"], d["z"] + fr["height"])
    add("daydate_frame", g, "steel_polished", bevel=0.05)

    # ---- hands at the photo's time: faceted dauphine blades with pointed counterweights, needle seconds hand ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]

    def hand(name, half, deg, z):
        g_ = Geo()
        for sx in (1, -1):
            slab(g_, [rot(sx * x, y, deg) for x, y in half], z, lambda x, y, deg=deg: z + th + hs["ridge"] * _on_line(x, y, deg / 30, 0.0))
        add(name, g_, "steel_polished", bevel=0.02)

    for name in ("hour", "minute"):
        h = t[name]
        L, tail, deg, z, wa, hw, tw = h["length_mm"], h["tail_mm"], h["angle_deg"], hs["z"][name], h["widest_at_mm"], h["half_width_mm"], h["tail_half_width_mm"]
        hand("hand_" + name, [(0, -tail), (tw, -0.6), (hw * 0.8, 0.4), (hw, wa), (0, L)], deg, z)
        # white lume strip along the middle of the blade, tapering with it (3/4 photo)
        a, b, k = hs["lume_from"] * L, hs["lume_to"] * L, hs["lume_width"]
        blade = lambda y: hw * min(1.0, (L - y) / (L - wa))
        zl = z + th + hs["ridge"]
        strip = [(-k * blade(a), a), (k * blade(a), a), (k * blade(b), b), (0, b + 0.3), (-k * blade(b), b)]
        add("hand_%s_lume" % name, Geo().prism([rot(x, y, deg) for x, y in strip], zl, zl + 0.03), "lume")
    h = t["seconds"]
    L, tail, deg, z, nw, cw = h["length_mm"], h["tail_mm"], h["angle_deg"], hs["z"]["seconds"], h["half_width_mm"], h["tail_half_width_mm"]
    add("hand_seconds", Geo().prism([rot(x, y, deg) for x, y in
                                     [(cw, -tail), (cw, -1.2), (nw, -0.6), (nw, L - 0.3), (0, L), (-nw, L - 0.3), (-nw, -0.6), (-cw, -1.2), (-cw, -tail)]],
                                    z, z + th), "steel_polished", bevel=0.02)
    hub_r, cap_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, z), (0, z)], segs=48), "steel_polished")
    zc = z + th
    add("hub_cap", Geo().lathe([(0, zc), (cap_r, zc), (cap_r, zc + 0.12), (cap_r * 0.6, zc + 0.2), (0, zc + 0.2)], segs=48), "steel_polished")

    # ---- crown: fluted cylinder on a radial axis at the traced angle (3 o'clock) ----
    cw_ = cfg["crown"]
    a = math.radians(math.degrees(math.atan2(*tr["crown_box"]["centre_mm"])) % 360)
    star = [((cw_["radius"] if i % 2 == 0 else cw_["radius"] - cw_["flute_depth"]) * math.cos(math.pi * i / cw_["teeth"]),
             (cw_["radius"] if i % 2 == 0 else cw_["radius"] - cw_["flute_depth"]) * math.sin(math.pi * i / cw_["teeth"])) for i in range(cw_["teeth"] * 2)]
    u, dr = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
    m = Matrix((u, (0, 0, 1), dr)).transposed().to_4x4()
    m.translation = (0, 0, cw_["z"])
    add("crown", Geo().prism(star, cw_["r_from"], cw_["r_to"], m), "steel_polished", bevel=0.15)

    # ---- lugs from the traced silhouette (mirrored from the left edge in the trace; top and bottom stretched to the mean tip) ----
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}
    tips = tr["lug_tip_mm"]
    tip = tips["mean"]

    def lug_half(y):
        return sum((sil[k][2] - sil[k][1]) / 2 for k in (round(y * tips["top"] / tip * 4) / 4, -round(y * tips["bottom"] / tip * 4) / 4)) / 2

    steps = [lg["from_y"] + k * 0.25 for k in range(int((tip - lg["from_y"]) / 0.25) + 1)]
    outline = [(lg["inner_x"], lg["from_y"])] + [(lug_half(y), y) for y in steps] + [(lg["inner_x"], tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * (abs(y) - lg["from_y"]) / (tip - lg["from_y"])
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

    # ---- three columns, all brushed with polished edges; centre joints `shift` further from the case than the outer ones ----
    br, el = cfg["bracelet"], cfg["end_link"]
    ehw, frac, shift = tr["end_link_half_width_mm"], tr["bracelet_centre_fraction"], -tr["bracelet_centre_joint_shift_mm"]
    gap = br["gap"]

    def half_at(y):  # bracelet half width past the lug tips: the photo's taper, both ends averaged, never wider than the end link
        y = min(y, min(max(sil), -min(sil)) - 0.25)  # the photo ends here; links further out keep the last traced width
        ys = [k for k in (round(y * 4) / 4, -round(y * 4) / 4) if k in sil]
        return min(sum((sil[k][2] - sil[k][1]) / 2 for k in ys) / len(ys), ehw)

    end_link = Geo()
    for sy in (1, -1):
        for y1, kind in ((tip, "outer"), (tip + shift - gap, "centre")):
            M = Matrix.Translation((0, sy * (el["from_y"] + y1) / 2, 0))
            ch = frac * ehw
            if kind == "outer":
                for sx in (1, -1):
                    end_link.prism(rect(sx * (ch + gap + ehw) / 2, 0, ehw - ch - gap, y1 - el["from_y"]), 0.0, el["top_z"], M)
            else:
                end_link.prism(rect(0, 0, 2 * ch, y1 - el["from_y"]), 0.0, el["top_z"], M)
    add("end_links", end_link, "steel_brushed", bevel=el["bevel"], polished_bevel=True)

    zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]  # bracelet built at final depth: flattened thickness, unflattened curve
    bent_box = curl(tip, R, zm)
    pitch = tr["bracelet_pitch_mm"]
    links_, back = Geo(), Geo()
    rows = 0
    za, zb = ds * br["z0"], ds * br["z1"]
    for sy in (1, -1):
        for kind, start in (("outer", tip), ("centre", tip + shift)):
            y0 = start
            while y0 < br["end_y"] - 0.5:
                y1 = min(y0 + pitch - gap, br["end_y"])
                hw = half_at((y0 + y1) / 2)
                ch = frac * hw
                if kind == "outer":
                    for sx in (1, -1):
                        x0, x1 = sorted((sx * (ch + gap), sx * hw))
                        bent_box(links_, x0, x1, y0, y1, za, zb, sy)
                    bent_box(back, -(hw - 0.3), hw - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                else:
                    bent_box(links_, -ch, ch, y0, y1, za, zb, sy)
                y0 = y1 + gap
    add("bracelet_links", links_, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "lug_gap": round(2 * ehw, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(tips["top"] + tips["bottom"], 2), "bracelet_rows": rows,
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}


def _on_line(x, y, hour, cx):
    """1 on the radial line offset cx from the centre line through angle hour * 30 deg (a facet ridge), 0 elsewhere."""
    a = math.radians(hour * 30)
    return 1.0 if abs(x * math.cos(a) - y * math.sin(a) - cx) < 1e-4 else 0.0
