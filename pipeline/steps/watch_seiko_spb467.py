"""watch_seiko_spb467: build the Seiko Presage Classic SPB467J1 as a flat-backed front relief (like the other GLBs in models/watches/).

Params: spec (config/watches/seiko-spb467j1.json). Same frame, pose, 2.5D depth scale, materials and bracelet curl as
watch_seiko_front (SNK607K1), whose helpers it reuses. This model's parts: round polished case with a wide sloped bezel and a
box crystal, applied polished batons (double at 12, short at 3), a polished date frame, faceted dauphine hour and minute hands,
a seconds needle with a long counterweight, a big fluted crown with a plain cap, and a seven-column bracelet: brushed outer
links and middle links B and D in one row, three polished pills A C E half a row out of step. Plan sizes from
config/watches/seiko-spb467j1-trace.json; heights from the spec. The dial is the photo map from pipeline/seiko_spb467_dial.py.
Rebuild with --force after regenerating the dial map (the map is not part of the stage fingerprint).
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
    map_meta = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    scene = bpy.context.scene
    coll = bpy.data.collections.new("WATCH | Seiko Presage SPB467J1 front relief")
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

    def add(name, geo, mat, bevel=None, polished_bevel=False, smooth=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
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

    # ---- case (full circle: the end links run under it), gasket, box crystal ----
    c, lg = cfg["case"], cfg["lug"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), c["material"])
    gk = cfg["gasket"]
    add("gasket", Geo().lathe([(gk["r_in"], gk["z0"]), (gk["r_out"], gk["z0"]), (gk["r_out"], gk["z1"]), (gk["r_in"], gk["z1"])], segs=192), "gasket_black")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial + sloped minute-track flange, photo map on a planar UV ----
    H = map_meta["half_size_mm"]
    g = Geo().lathe([(0, d["z"]), (tr["dial_flat_radius_mm"], d["z"]), (cr["radius"], d["rehaut_z"])], segs=192)
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

    # ---- applied polished batons (double at 12, short at 3 beside the date), polished date frame ----
    ix, ti = cfg["indices"], tr["indices"]
    z0, top = d["z"], d["z"] + ix["height"]
    g = Geo()
    for hour in range(1, 12):
        r0, r1 = (ti["short_inner_mm"], ti["short_outer_mm"]) if hour == 3 else (ti["inner_mm"], ti["outer_mm"])
        g.prism([rot(x, y, hour * 30) for x, y in rect(0, (r0 + r1) / 2, ti["width_mm"], r1 - r0)], z0, top)
    for sx in (-1, 1):
        g.prism(rect(sx * ti["offset_12_mm"], (ti["inner_mm"] + ti["outer_mm"]) / 2, ti["width_12_mm"], ti["outer_mm"] - ti["inner_mm"]), z0, top)
    add("indices", g, "steel_polished", bevel=ix["bevel"])
    fo, fi = tr["date_frame"]["x0_y0_x1_y1_mm"], tr["date_window"]["x0_y0_x1_y1_mm"]
    g, zt = Geo(), d["z"] + cfg["date_frame"]["height"]
    for x0, y0, x1, y1 in ((fo[0], fo[1], fo[2], fi[1]), (fo[0], fi[3], fo[2], fo[3]), (fo[0], fi[1], fi[0], fi[3]), (fi[2], fi[1], fo[2], fi[3])):
        g.prism(rect((x0 + x1) / 2, (y0 + y1) / 2, abs(x1 - x0), abs(y1 - y0)), d["z"], zt)
    add("date_frame", g, "steel_polished", bevel=0.04)

    # ---- hands at the photo's time: faceted dauphine hour and minute, seconds needle with a long counterweight ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]

    def hand(name, half, deg, z):
        g_ = Geo()
        for sx in (1, -1):  # two facets meeting at a ridge on the centre line
            slab(g_, [rot(sx * x, y, deg) for x, y in half], z, lambda x, y, deg=deg: z + th + hs["ridge"] * _on_axis(x, y, deg))
        add(name, g_, "steel_polished", bevel=0.02)

    for name in ("hour", "minute"):
        h = t[name]
        L, tail, deg, z = h["length_mm"], h["tail_mm"], h["angle_deg"], hs["z"][name]
        w0, w1, tw = h["half_width_root_mm"], h["half_width_tip_mm"], hs["tail_half_width"]
        hand("hand_" + name, [(0, -tail), (tw, -tail + 0.3), (tw, 0.0), (w0, 0.08 * L), (max(w1, 0.08), 0.88 * L), (0, L)], deg, z)
    h = t["seconds"]
    L, tail, deg, z = h["length_mm"], h["tail_mm"], h["angle_deg"], hs["z"]["seconds"]
    nw, cw = h["half_width_mm"], h["tail_half_width_mm"]
    poly = [(nw, 0), (nw, L - 0.3), (0, L), (-nw, L - 0.3), (-nw, 0), (-cw, -tail * 0.4), (-cw * 0.7, -tail + 0.3), (0, -tail),
            (cw * 0.7, -tail + 0.3), (cw, -tail * 0.4)]
    add("hand_seconds", Geo().prism([rot(x, y, deg) for x, y in poly], z, z + th), "steel_polished", bevel=0.02)
    hub_r, cap_r = tr["hub_radius_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, hs["z"]["minute"]), (0, hs["z"]["minute"])], segs=48), "steel_polished")
    zc = z + th
    add("hub_cap", Geo().lathe([(0, z - 0.1), (cap_r, z - 0.1), (cap_r, zc + 0.1), (cap_r * 0.6, zc + 0.18), (0, zc + 0.18)], segs=48), "steel_polished")

    # ---- crown: fluted cylinder plus a plain domed cap on a radial axis at the traced angle (3 o'clock) ----
    cw_ = cfg["crown"]
    a = math.radians(math.degrees(math.atan2(*tr["crown_box"]["centre_mm"])) % 360)
    star = [((cw_["radius"] if i % 2 == 0 else cw_["radius"] - cw_["flute_depth"]) * math.cos(math.pi * i / cw_["teeth"]),
             (cw_["radius"] if i % 2 == 0 else cw_["radius"] - cw_["flute_depth"]) * math.sin(math.pi * i / cw_["teeth"])) for i in range(cw_["teeth"] * 2)]
    u, dr = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
    m = Matrix((u, (0, 0, 1), dr)).transposed().to_4x4()
    m.translation = (0, 0, cw_["z"])
    add("crown", Geo().prism(star, cw_["r_from"], cw_["r_flutes_to"], m), "steel_polished", bevel=0.15)
    cap = [(0, cw_["r_flutes_to"]), (cw_["cap_radius"], cw_["r_flutes_to"]), (cw_["cap_radius"], cw_["r_to"] - 0.5),
           (cw_["cap_radius"] * 0.6, cw_["r_to"]), (0, cw_["r_to"])]
    add("crown_cap", Geo().lathe(cap, segs=48, m=m), "steel_polished", smooth=True)

    # ---- lugs from the traced silhouette (left/right and top/bottom averaged), polished like the case ----
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}

    def half(y):
        ys = [sil[k] for k in (round(y, 2), round(-y, 2)) if k in sil]
        return sum((p[2] - p[1]) / 2 for p in ys) / len(ys)

    tip = tr["lug_tip_mm"]["mean"]
    steps = [lg["from_y"] + k * 0.25 for k in range(int((tip - lg["from_y"]) / 0.25) + 1)]
    outline = [(lg["inner_x"], lg["from_y"])] + [(half(y), y) for y in steps] + [(lg["inner_x"], tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * (abs(y) - lg["from_y"]) / (tip - lg["from_y"])
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_polished", bevel=lg["bevel"])

    # ---- seven columns: outer | A | B | C | D | E | outer. Outer, B and D brushed and in step; pills A C E polished,
    #      `shift` nearer the case (as in the photo) ----
    br, el, tb = cfg["bracelet"], cfg["end_link"], tr["bracelet"]
    ch, gap, hw, shift = tb["centre_half_mm"], br["gap"], br["half_width"], tb["pill_shift_mm"]
    w = (2 * ch - 4 * gap) / 5
    cols = [(-ch + k * (w + gap), -ch + k * (w + gap) + w) for k in range(5)]
    pills, middles = cols[0::2], cols[1::2]
    outers = [(ch + gap, hw), (-hw, -ch - gap)]

    # end link between the lugs, from under the case: outer, B and D to the lug tips, the pill columns `shift` shorter
    end_brushed, end_polished = Geo(), Geo()
    for sy in (1, -1):
        for (x0, x1), y1, geo in [(c_, tip, end_brushed) for c_ in outers + middles] + [(c_, tip - shift - gap, end_polished) for c_ in pills]:
            geo.prism(rect((x0 + x1) / 2, sy * (el["from_y"] + y1) / 2, x1 - x0, y1 - el["from_y"]), 0.0, el["top_z"])
    add("end_links", end_brushed, "steel_brushed", bevel=el["bevel"], polished_bevel=True)
    add("end_links_centre", end_polished, "steel_polished", bevel=el["bevel"])

    zm, R = ds * (br["z0"] + br["z_outer"]) / 2, br["bend_radius"]  # built at final depth: flattened thickness, unflattened curve
    bent_box = curl(tip + br.get("bend_after_tip", 0.0), R, zm)
    pitch = tb["pitch_mm"]
    brushed, polished, back = Geo(), Geo(), Geo()
    rows = 0
    za = ds * br["z0"]
    for sy in (1, -1):
        for kind, start in (("outer", tip), ("pill", tip - shift)):
            y0 = start
            while y0 < br["end_y"] - 0.5:
                y1 = min(y0 + pitch - gap, br["end_y"])
                if kind == "outer":
                    for x0, x1 in outers:
                        bent_box(brushed, x0, x1, y0, y1, za, ds * br["z_outer"], sy)
                    for x0, x1 in middles:
                        bent_box(brushed, x0, x1, y0, y1, za, ds * br["z_middle"], sy)
                    bent_box(back, -(hw - 0.3), hw - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                else:
                    for x0, x1 in pills:
                        bent_box(polished, x0, x1, y0, y1, za, ds * br["z_pill"], sy)
                y0 = y1 + gap
    add("bracelet_links", brushed, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_pills", polished, "steel_polished", bevel=br["pill_bevel"])
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "lug_to_lug": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "bracelet_rows": rows, "column_width_mm": round(w, 3),
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}


def _on_axis(x, y, deg):
    """1 on the radial centre line through angle deg (the ridge), 0 elsewhere."""
    a = math.radians(deg)
    return 1.0 if abs(x * math.cos(a) - y * math.sin(a)) < 1e-4 else 0.0
