"""watch_orient_re_au0107e: build the Orient Star RE-AU0107E (green power reserve dial, steel bracelet) as a flat-backed front relief.

Params: spec (config/watches/orient-re-au0107e.json). Same frame, pose, 2.5D depth scale, materials and bracelet curl as
watch_seiko_sur419_front, whose helpers it reuses. Parts from the photo: a wide polished sloped bezel, faceted lugs with a
brushed top and polished chamfer, applied faceted batons (wide ones at 3 and 9 with dark grooves), applied serif XII and VI
built from their strokes, faceted sword hands with pointed counter-tails and a polished collar, a seconds needle with a dark
counterweight, a fluted crown and a five-piece bracelet row: brushed outer links, narrow polished links, a brushed centre link
whose joints sit nearer the case. The dial (sunburst, ribbed rings, power reserve, date, logo) is the photo map from
pipeline/orient_re_au0107e_dial.py. Rebuild with --force after regenerating the map (it is not part of the stage fingerprint).
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
    dm = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Orient Star RE-AU0107E front relief")
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

    # ---- case with the wide polished sloped bezel, dark gasket line, crystal ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), "steel_polished")
    gk = cfg["gasket"]
    add("gasket", Geo().lathe([(gk["r_in"], gk["z0"]), (gk["r_out"], gk["z0"]), (gk["r_out"], gk["z1"]), (gk["r_in"], gk["z1"])], segs=192), "gasket_black")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial + rehaut, photo map on a planar UV ----
    me = Geo().lathe([(0, d["z"]), (tr["dial_edge_radius_mm"], d["z"]), (d["rehaut_r"], d["rehaut_z"])], segs=192).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    uv = me.uv_layers.new(name="UVMap")
    H = dm["half_size_mm"]
    for loop in me.loops:
        x, y, _ = me.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
    add("dial", me, "dial")

    # ---- applied faceted batons; wide ones at 3 (short, outside the date) and 9 with dark grooves ----
    ix, ti = cfg["indices"], tr["indices"]
    z0, top = d["z"], d["z"] + ix["height"]
    g, grooves = Geo(), Geo()

    def baton(r0, r1, hw, to_model, slope):
        """Two facets meeting at a ridge on the centre line; the inner `slope` of the length falls to the dial (dark facet)."""
        rk = r0 + slope * (r1 - r0)
        half = [(0, r0), (hw, r0), (hw, rk), (hw, r1), (0, r1), (0, rk)] if slope else [(0, r0), (hw, r0), (hw, r1), (0, r1)]
        for sx in (1, -1):
            pts = [(sx * x, y) for x, y in half]
            hgt = {to_model(x, y): z0 + ix["inner_end_z"] if (slope and y == r0) else top + ix["ridge"] * (x == 0) for x, y in pts}
            slab(g, [to_model(x, y) for x, y in pts], z0, lambda x, y: hgt[(x, y)])

    for hour in (1, 2, 4, 5, 7, 8, 10, 11):
        baton(ti["inner_mm"], ti["outer_mm"], ti["width_mm"] / 2, lambda x, y, hour=hour: rot(x, y, hour * 30), ix["inner_slope"])
    for hour, key in ((3, "index_3"), (9, "index_9")):
        x0, y0, x1, y1 = ti[key]["x0_y0_x1_y1_mm"]
        r0, r1 = sorted((abs(x0), abs(x1)))
        hw, yc = abs(y0 - y1) / 2, (y0 + y1) / 2
        rotate = lambda x, y, hour=hour, yc=yc: (y if hour == 3 else -y, yc - x if hour == 3 else yc + x)  # radial (y) -> model
        baton(r0, r1, hw, rotate, ix["wide_inner_slope"][str(hour)])
        for off, frac in ix["grooves"][str(hour)]:
            ra = r1 - frac * (r1 - r0)
            grooves.prism([rotate(x, y) for x, y in rect(off, (ra + r1) / 2 - 0.15, ix["groove_width"], r1 - ra - 0.3)], top, top + ix["ridge"] + 0.05)  # clear of the facets: thin layers z-fight in web viewers
    add("indices", g, "steel_polished", bevel=0.04)
    add("index_grooves", grooves, "hand_dark")

    # ---- applied serif XII and VI from their measured strokes ----
    nu = cfg["numerals"]
    for k in ("numeral_12", "numeral_6"):
        g = Geo()
        zt = d["z"] + nu["height"]
        for i, q in enumerate(tr[k + "_quads"]):
            (ax, ay), (bx, by), (cx, cy), (dx, dy) = q  # top-left, top-right, bottom-right, bottom-left
            if abs(ay - dy) > 1.0:  # stroke: two facets meeting at a ridge along its centre line
                mt, mb = ((ax + bx) / 2, ay), ((cx + dx) / 2, cy)
                for half in ([(ax, ay), mt, mb, (dx, dy)], [mt, (bx, by), (cx, cy), mb]):
                    slab(g, half, d["z"], lambda x, y, mt=mt, mb=mb: zt + (nu["ridge"] if (x, y) in (mt, mb) else 0.0))
            else:  # serif: flat, a hair lower than the strokes it joins
                g.prism([tuple(p) for p in q], d["z"], zt - 0.01)
        add(k, g, "steel_polished")

    # ---- hands at the photo's time: faceted swords with pointed counter-tails, collar, seconds needle with a dark counterweight ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]

    def faceted(name, half, deg, z):
        g_ = Geo()
        for sx in (1, -1):
            slab(g_, [rot(sx * x, y, deg) for x, y in half], z, lambda x, y, deg=deg: z + th + hs["ridge"] * _on_axis(x, y, deg))
        add(name, g_, "steel_polished", bevel=0.02)

    for name in ("hour", "minute"):
        h = t[name]
        L, tail, deg, z = h["length_mm"], h["tail_mm"], h["angle_deg"], hs["z"][name]
        w0, w1, tw = h["half_width_root_mm"], h["half_width_tip_mm"], h["tail_half_width_mm"]
        faceted("hand_" + name, [(0, -tail), (tw, -0.55 * tail), (0.8 * w0, 0.0), (w0, 0.12 * L), (w1, 0.85 * L), (0, L)], deg, z)
    h = t["seconds"]
    L, tail, deg, z = h["length_mm"], h["tail_mm"], h["angle_deg"], hs["z"]["seconds"]
    nw, cw = h["half_width_mm"], h["tail_half_width_mm"]
    add("hand_seconds", Geo().prism([rot(x, y, deg) for x, y in [(nw, -tail), (nw, L - 0.4), (0, L), (-nw, L - 0.4), (-nw, -tail)]], z, z + th),
        "steel_polished", bevel=0.02)
    add("hand_seconds_counterweight", Geo().prism([rot(x, y, deg) for x, y in rect(0, -(tail + hs["counterweight_from"]) / 2, 2 * cw,
                                                                                    tail - hs["counterweight_from"])], z + th, z + th + 0.05), "hand_dark")
    collar_r, cap_r = tr["hub_radius_mm"]
    zh = hs["z"]["hour"]
    add("hub", Geo().lathe([(0, d["z"]), (collar_r, d["z"]), (collar_r, zh + th), (0, zh + th)], segs=64), "steel_polished")
    add("hub_post", Geo().lathe([(0, zh), (cap_r * 1.4, zh), (cap_r * 1.4, z), (0, z)], segs=48), "hand_dark")
    zc = z + th
    add("hub_cap", Geo().lathe([(0, zc), (cap_r, zc), (cap_r, zc + 0.1), (cap_r * 0.6, zc + 0.18), (0, zc + 0.18)], segs=48), "steel_polished")

    # ---- crown: fluted cylinder on a radial axis at the traced angle (3 o'clock) ----
    cw_ = cfg["crown"]
    a = math.radians(math.degrees(math.atan2(*tr["crown_box"]["centre_mm"])) % 360)
    star = [((cw_["radius"] if i % 2 == 0 else cw_["radius"] - cw_["flute_depth"]) * math.cos(math.pi * i / cw_["teeth"]),
             (cw_["radius"] if i % 2 == 0 else cw_["radius"] - cw_["flute_depth"]) * math.sin(math.pi * i / cw_["teeth"])) for i in range(cw_["teeth"] * 2)]
    u, dr = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
    m = Matrix((u, (0, 0, 1), dr)).transposed().to_4x4()
    m.translation = (0, 0, cw_["z"])
    add("crown", Geo().prism(star, cw_["r_from"], cw_["r_to"], m), "steel_polished", bevel=0.15)
    add("crown_cap", Geo().lathe([(0, cw_["r_to"]), (cw_["radius"] * 0.92, cw_["r_to"]), (cw_["radius"] * 0.92, cw_["r_to"] + cw_["cap"]),
                                  (0, cw_["r_to"] + cw_["cap"])], segs=48, m=m), "steel_polished", bevel=0.1)

    # ---- lugs from the traced silhouette (left/right and top/bottom averaged): brushed top, polished chamfer ----
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}

    def half(y):
        ys = [sil[k] for k in (round(y, 2), round(-y, 2)) if k in sil]
        return sum((p[2] - p[1]) / 2 for p in ys) / len(ys)

    lg = cfg["lug"]
    tip = tr["lug_tip_mm"]["mean"]
    steps = [lg["from_y"] + k * 0.25 for k in range(int((tip - lg["from_y"]) / 0.25) + 1)]
    outline = [(lg["inner_x"], lg["from_y"])] + [(half(y), y) for y in steps] + [(lg["inner_x"], tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * (abs(y) - lg["from_y"]) / (tip - lg["from_y"])
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel=True)

    # ---- bracelet rows: brushed outer links, narrow polished links (with the outer joints), brushed centre link whose joints
    #      sit `shift` nearer the case ----
    br, el = cfg["bracelet"], cfg["end_link"]
    ch, nh, shift = tr["bracelet_centre_half_mm"], tr["bracelet_narrow_half_mm"], tr["bracelet_centre_joint_shift_mm"]
    sil_max = min(max(sil), -min(sil)) - 0.25  # the photo ends here; links further out keep the last traced width
    hw_at = lambda y: min(half(round(min(max(y, tip + 1.0), sil_max) * 4) / 4), el["half_width"])
    gap = br["gap"]

    # end link between the lugs, from under the case: outer and narrow columns to the lug tips, centre `shift` shorter
    end_brushed, end_polished = Geo(), Geo()
    for sy in (1, -1):
        y1 = tip
        M = Matrix.Translation((0, sy * (el["from_y"] + y1) / 2, 0))
        for sx in (1, -1):
            end_brushed.prism(rect(sx * (nh + gap + el["half_width"]) / 2, 0, el["half_width"] - nh - gap, y1 - el["from_y"]), 0.0, el["top_z"], M)
            end_polished.prism(rect(sx * (ch + gap + nh) / 2, 0, nh - ch - gap, y1 - el["from_y"]), 0.0, el["top_z"], M)
        y1 = tip - shift - gap
        end_brushed.prism(rect(0, sy * (el["from_y"] + y1) / 2, 2 * ch, y1 - el["from_y"]), 0.0, el["top_z"])
    add("end_links", end_brushed, "steel_brushed", bevel=el["bevel"], polished_bevel=True)
    add("end_links_narrow", end_polished, "steel_polished", bevel=el["bevel"])

    zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]  # built at final depth: flattened thickness, unflattened curve
    bent_box = curl(tip + br.get("bend_after_tip", 0.0), R, zm)
    pitch = tr["bracelet_pitch_mm"]
    brushed, polished, back = Geo(), Geo(), Geo()
    rows = 0
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
                        x0, x1 = sorted((sx * (ch + gap), sx * nh))
                        bent_box(polished, x0, x1, y0, y1, za, zb + ds * br["narrow_raise"], sy)
                    bent_box(back, -(hw - 0.3), hw - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                else:
                    bent_box(brushed, -ch, ch, y0, y1, za, zb, sy)
                y0 = y1 + gap
    add("bracelet_links", brushed, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_links_narrow", polished, "steel_polished", bevel=br["bevel"] * 0.6)
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "lug_to_lug": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "bracelet_rows": rows,
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}


def _on_axis(x, y, deg):
    """1 on the radial centre line through angle deg (the ridge), 0 elsewhere."""
    a = math.radians(deg)
    return 1.0 if abs(x * math.cos(a) - y * math.sin(a)) < 1e-4 else 0.0
