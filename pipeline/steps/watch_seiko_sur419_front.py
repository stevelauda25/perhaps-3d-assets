"""watch_seiko_sur419_front: build the Seiko SUR419P1 as a flat-backed front relief (like the other GLBs in models/watches/).

Params: spec (config/watches/seiko-sur419p1.json). Same frame, pose, 2.5D depth scale and materials as watch_seiko_front
(SNK607K1), whose helpers it reuses; this model differs in the parts: faceted pointed batons and hands (a raised ridge along
the middle), applied 12 and 6, a skeleton lancet counterweight, a three-column bracelet whose centre joints sit about 1 mm
nearer the case than the outer ones and whose links bend smoothly with the curve, and an end link with a shorter centre. Plan sizes come from
config/watches/seiko-sur419p1-trace.json; heights from the spec. The dial is the photo map from pipeline/seiko_sur419_dial.py.
Rebuild with --force after regenerating the dial map (the map is not part of the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, photo_material, plate, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    scene = bpy.context.scene
    coll = bpy.data.collections.new("WATCH | Seiko SUR419P1 front relief")
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

    # ---- case (full circle: the end links sit lower and run under it), gasket, crystal ----
    c, lg = cfg["case"], cfg["lug"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), c["material"])
    gk = cfg["gasket"]
    add("gasket", Geo().lathe([(gk["r_in"], gk["z0"]), (gk["r_out"], gk["z0"]), (gk["r_out"], gk["z1"]), (gk["r_in"], gk["z1"])], segs=192), "gasket_black")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial + rehaut, photo map on a planar UV ----
    g = Geo().lathe([(0, d["z"]), (tr["dial_edge_radius_mm"], d["z"]), (d["rehaut_r"], d["rehaut_z"])], segs=192)
    me = g.mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    uv = me.uv_layers.new(name="UVMap")
    H = tr["crystal_ring"]["radius_mm"]
    for loop in me.loops:
        x, y, _ = me.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
    add("dial", me, "dial")

    # ---- applied faceted batons (wide at the outer end), a short one at 3 beside the date, applied 12 and 6 ----
    ix, ti = cfg["indices"], tr["indices"]
    z0, top = d["z"], d["z"] + ix["height"]
    g = Geo()
    for hour in (1, 2, 3, 4, 5, 7, 8, 9, 10, 11):
        if hour == 3:
            r0, r1, w0, w1 = ti["short_inner_mm"], ti["short_outer_mm"], ti["short_width_mm"], ti["short_width_mm"]
        else:
            r0, r1, w0, w1 = ti["inner_mm"], ti["outer_mm"], ti["width_inner_mm"], ti["width_outer_mm"]
        half = [(0, r0), (w0 / 2, r0), (w1 / 2, r1), (0, r1)]
        for sx in (1, -1):  # two facets meeting at a ridge on the centre line
            slab(g, [rot(sx * x, y, hour * 30) for x, y in half], z0, lambda x, y, h=hour: top + ix["ridge"] * _on_axis(x, y, h))
    add("indices", g, "steel_polished", bevel=0.04)
    nu = cfg["numerals"]
    for k in ("numeral_12", "numeral_6"):
        add(k, plate(tr[k + "_shapes"], d["z"], d["z"] + nu["height"], P + k), "steel_polished")

    # ---- hands at the photo's time: faceted pointed hour and minute, thin seconds needle with a skeleton lancet ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]

    def hand(name, half, deg, z, mat="steel_polished"):
        g_ = Geo()
        for sx in (1, -1):
            slab(g_, [rot(sx * x, y, deg) for x, y in half], z, lambda x, y, deg=deg: z + th + hs["ridge"] * _on_axis(x, y, deg / 30))
        add(name, g_, mat, bevel=0.02)

    for name in ("hour", "minute"):
        h = t[name]
        L, tail, deg, z = h["length_mm"], h["tail_mm"], h["angle_deg"], hs["z"][name]
        w0, w1, tw = h["half_width_root_mm"], h["half_width_tip_mm"], hs[name + "_tail_half_width"]
        hand("hand_" + name, [(0, -tail), (tw * 0.6, -tail), (tw, -tail + 0.4), (tw, -0.6), (w0, 0.6), (w1, 0.88 * L), (0, L)], deg, z)
    h = t["seconds"]
    L, tail, deg, z = h["length_mm"], h["tail_mm"], h["angle_deg"], hs["z"]["seconds"]
    nw, cw = h["half_width_mm"], h["tail_half_width_mm"]
    add("hand_seconds", Geo().prism([rot(x, y, deg) for x, y in
                                     [(nw, -1.2), (nw, L - 0.4), (0, L), (-nw, L - 0.4), (-nw, -1.2)]], z, z + th), "steel_polished", bevel=0.02)
    lancet = lambda s: [(0, -1.0), (s * cw * 0.45, -1.3), (s * cw, -tail + 1.6), (s * cw * 0.55, -tail + 0.5), (0, -tail)]
    outer = lancet(1) + lancet(-1)[::-1][1:-1]
    rim = hs["seconds_rim"]
    hole = [(0, -1.3 - rim), (cw * 0.45 - rim, -1.45), (cw - rim, -tail + 1.6), (cw * 0.55 - rim, -tail + 0.55 + rim), (0, -tail + 2 * rim)]
    hole = hole + [(-x, y) for x, y in hole[::-1][1:-1]]
    turn = lambda poly: [list(rot(x, y, deg)) for x, y in poly]
    add("hand_seconds_lancet", plate([{"outer": turn(outer), "holes": [turn(hole)]}], z, z + th, P + "hand_seconds_lancet"), "steel_polished")
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

    # ---- lugs from the traced silhouette (left/right and top/bottom averaged); polished like the case ----
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

    # ---- three columns: polished centre link with two lengthwise grooves, brushed outer links; centre joints sit
    #      `shift` nearer the case than the outer joints (as in the photo) ----
    br, el = cfg["bracelet"], cfg["end_link"]
    ch, gh, shift = tr["bracelet_centre_half_mm"], tr["bracelet_groove_half_mm"], tr["bracelet_centre_joint_shift_mm"]
    sil_max = min(max(sil), -min(sil)) - 0.25  # the photo ends here; links further out keep the last traced width
    hw_at = lambda y: min(half(round(min(max(y, tip + 1.0), sil_max) * 4) / 4), el["half_width"])
    gap, grv = br["gap"], br["groove"]

    def centre_piece(geo, ylen, za, zb, M=None):
        geo.prism(rect(0, 0, 2 * gh - grv, ylen), za, zb, M)
        for sx in (1, -1):
            geo.prism(rect(sx * (gh + ch) / 2, 0, ch - gh - grv / 2, ylen), za, zb, M)

    def outer_piece(geo, hw, ylen, za, zb, M=None):
        for sx in (1, -1):
            geo.prism(rect(sx * (ch + gap + hw) / 2, 0, hw - ch - gap, ylen), za, zb, M)

    # end link between the lugs, from under the case: outer columns to the lug tips, centre column `shift` shorter
    end_brushed, end_polished = Geo(), Geo()
    for sy in (1, -1):
        for y1, kind in ((tip, "outer"), (tip - shift - gap, "centre")):
            M = Matrix.Translation((0, sy * (el["from_y"] + y1) / 2, 0))
            if kind == "outer":
                outer_piece(end_brushed, el["half_width"], y1 - el["from_y"], 0.0, el["top_z"], M)
            else:
                centre_piece(end_polished, y1 - el["from_y"], 0.0, el["top_z"], M)
    add("end_links", end_brushed, "steel_brushed", bevel=el["bevel"], polished_bevel=True)
    add("end_links_centre", end_polished, "steel_polished", bevel=el["bevel"])

    zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]  # bracelet built at final depth: flattened thickness, unflattened curve
    bend_y = tip + br.get("bend_after_tip", 0.0)

    def bend(s, z):
        """(distance along the bracelet, height) -> (y, z): straight up to bend_y, then rolled back over a circle of
        radius R (away from the viewer), so the ends curve out of sight. Heights stay normal to the curve."""
        if s <= bend_y:
            return s, z
        a, r = (s - bend_y) / R, R + z - zm
        return bend_y + r * math.sin(a), zm - R + r * math.cos(a)

    def bent_box(geo, x0, x1, s0, s1, za, zb, sy):
        """Box from s0 to s1 along the bracelet, sliced every 0.4 mm inside the bend so it follows the curve smoothly
        (like the resin straps of the Casio GLBs) instead of turning as one rigid piece."""
        cuts = [s0] + [s0 + k * 0.4 for k in range(1, int((s1 - s0) / 0.4) + 1) if s0 + k * 0.4 > bend_y - 0.4 and s0 + k * 0.4 < s1 - 0.05] + [s1]
        base = len(geo.v)
        for s_ in cuts:
            for x, z in ((x0, za), (x1, za), (x1, zb), (x0, zb)):
                y, z_ = bend(s_, z)
                geo.v.append((x, sy * y, z_))
        faces = [(0, 1, 2, 3)]
        for k in range(len(cuts) - 1):
            b, n = 4 * k, 4 * k + 4
            faces += [(b, n, n + 1, b + 1), (b + 3, b + 2, n + 2, n + 3), (b + 1, n + 1, n + 2, b + 2), (b, b + 3, n + 3, n)]
        n = 4 * (len(cuts) - 1)
        faces.append((n + 3, n + 2, n + 1, n))
        for f in faces:
            f = tuple(base + i for i in f)
            geo.f.append(f if sy > 0 else f[::-1])  # mirrored in y: flip the winding to keep normals outward
            geo.smooth.append(True)

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
                        x0, x1 = sorted((sx * (ch + gap), sx * hw))
                        bent_box(brushed, x0, x1, y0, y1, za, zb, sy)
                    bent_box(back, -(hw - 0.3), hw - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                else:
                    bent_box(polished, -(gh - grv / 2), gh - grv / 2, y0, y1, za, zb, sy)
                    for sx in (1, -1):
                        x0, x1 = sorted((sx * (gh + grv / 2), sx * ch))
                        bent_box(polished, x0, x1, y0, y1, za, zb, sy)
                y0 = y1 + gap
    add("bracelet_links", brushed, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_links_centre", polished, "steel_polished", bevel=br["bevel"])
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


def _on_axis(x, y, hour):
    """1 on the radial centre line through angle hour * 30 deg (the ridge), 0 elsewhere."""
    a = math.radians(hour * 30)
    return 1.0 if abs(x * math.cos(a) - y * math.sin(a)) < 1e-4 else 0.0
