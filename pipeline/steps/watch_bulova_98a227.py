"""watch_bulova_98a227: build the Bulova 98A227 (Marine Star automatic, 44 mm, rose-gold tone case, blue outer ring, blue
silicone strap) as a flat-backed front relief.

Params: spec (config/watches/bulova-98a227.json). Frame as watch_hamilton_scuba_pioneer: mm, origin = hand pivot, dial faces
+z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, strap built at final depth
with the house curl. Parts from the official render: a rose-gold case with faceted lugs and crown guards (one body from
the traced head outline); a blue 24-sided outer ring with a V notch at every vertex; a brushed rose-gold bezel with six blue
screws; applied rose-gold numerals and logo (traced outlines); rose-gold rings round the sub-seconds and the open heart;
sword hands with lume and an open slot; a red sub-seconds hand; a fluted crown. Photo maps (pipeline/bulova_98a227_dial.py):
the dial and the strap. Rebuild with --force after regenerating the maps (not part of the fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_hamilton_scuba_pioneer import circle, sloped_plate
from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled
from pipeline.steps.watch_speedmaster import Geo, ROOT, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    coll = bpy.data.collections.new("WATCH | %s front relief" % cfg["model"])
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    maps = {}
    for key, pm in cfg["photo_maps"].items():
        mats[key] = photo_material(key, ROOT / pm["image"], pm["roughness"])
        maps[key] = json.loads((ROOT / pm["image"]).with_suffix(".json").read_text())
    textured = cfg.get("brushed_textures", {})
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
    S, (px0, py0) = tr["scale_px_per_mm"], tr["origin_px"]
    dm = maps["dial"]

    def dial_uv(x, y, z):
        H = dm["half_size_mm"]
        return (0.5 + x / (2 * H), 0.5 + y / (2 * H))

    def add(name, geo, mat, bevel=None, polished_bevel=False, uv_of=None, smooth=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured:  # planar UV in mm / tile
            uv, tile = me.uv_layers.new(name="UVMap"), textured[mat]["tile_mm"]
            for loop in me.loops:
                x, y, _ = me.vertices[loop.vertex_index].co
                uv.data[loop.index].uv = (y / tile, -x / tile)
        if mat in maps:
            f = uv_of or dial_uv
            uv = me.uv_layers.new(name="UVMap")
            for loop in me.loops:
                uv.data[loop.index].uv = f(*me.vertices[loop.vertex_index].co)
        if bevel:
            if polished_bevel:
                me.materials.append(mats[polished_bevel])
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            if polished_bevel:
                m.material = 1
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if not name.startswith("strap"):
            o.scale = (1, 1, ds)
        return o

    def upward(me):  # lathe discs: top faces up
        if me.polygons[0].normal.z < 0:
            for poly in me.polygons:
                poly.flip()
            me.update()
        return me

    rg, c, d, cr = tr["rings_mm"], cfg["case"], cfg["dial"], cfg["crystal"]

    # ---- case with lugs and crown guards: one body from the traced head outline, sloped lug tops ----
    lg = cfg["lug"]
    tip, xi = tr["lug"]["tip_mm"], tr["lug"]["inner_x_mm"]
    rows = tr["head_rows_y_left_right_mm"]
    rn = c["notch_radius"]
    yc = math.sqrt(rn * rn - xi * xi)
    arc = lambda sy: [(-xi + 2 * xi * k / 16, sy * math.sqrt(rn * rn - (-xi + 2 * xi * k / 16) ** 2)) for k in range(17)]
    right = [(max(xr, xi + 0.3), y) for y, _, xr in rows]  # top tip -> bottom tip
    left = [(min(xl, -xi - 0.3), y) for y, xl, _ in rows[::-1]]  # bottom tip -> top tip
    outline = right + [(xi, -tip), (xi, -yc)] + arc(-1)[::-1] + [(-xi, -yc), (-xi, -tip)] + left + [(-xi, tip), (-xi, yc)] + arc(1) + [(xi, yc), (xi, tip)]
    clean = [outline[0]]
    for q in outline[1:]:
        if math.hypot(q[0] - clean[-1][0], q[1] - clean[-1][1]) > 0.08:
            clean.append(q)
    top = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * min(1.0, max(0.0, (abs(y) - lg["slope_from_y"]) / (tip - lg["slope_from_y"])))
    sf = lg["slope_from_y"]
    cuts = [sy * (sf + (tip - sf) * k / 8) for sy in (1, -1) for k in range(8)]
    add("case", sloped_plate(clean, 0.0, top, P + "case", [circle(rg["bezel_in"] - 0.3, 192)], cuts), "gold_brushed", bevel=lg["bevel"],
        polished_bevel="gold_polished")

    # ---- blue outer ring (24-gon outside); brushed rose-gold bezel whose outer edge has a V notch at every ring vertex ----
    bl, nt = cfg["blue_ring"], tr["ring_notch_mm"]
    n = nt["count"]
    outer = [(rg["ring_out"] * math.sin(2 * math.pi * k / n), rg["ring_out"] * math.cos(2 * math.pi * k / n)) for k in range(n)]
    add("blue_ring", plate([{"outer": outer, "holes": [circle(rg["bezel_out"] - 0.25, 192)]}], bl["z0"], bl["top_z"], P + "blue_ring"), "blue_ring", bevel=bl["bevel"])
    bz = cfg["bezel"]
    ro = rg["bezel_out"]
    edge = []
    for k in range(n):
        a0, hw = 2 * math.pi * k / n, nt["half_width"] / ro
        edge.append(((ro - nt["depth"]) * math.sin(a0), (ro - nt["depth"]) * math.cos(a0)))
        for j in range(8):  # arc to the next notch
            a = a0 + hw + (2 * math.pi / n - 2 * hw) * j / 7
            edge.append((ro * math.sin(a), ro * math.cos(a)))
    add("bezel", plate([{"outer": edge, "holes": [circle(rg["bezel_in"] + bz["chamfer"], 256)]}], bz["z0"], bz["top_z"], P + "bezel"), "gold_brushed",
        bevel=bz["edge_bevel"], polished_bevel="gold_polished")
    add("bezel_chamfer", Geo().lathe([(rg["bezel_in"], bz["z0"]), (rg["bezel_in"] + bz["chamfer"] + 0.02, bz["z0"]), (rg["bezel_in"] + bz["chamfer"] + 0.02, bz["top_z"]),
                                      (rg["bezel_in"], bz["inner_z"]), (rg["bezel_in"], bz["z0"])], segs=256), "gold_polished", smooth=True)
    sw = tr["screws_mm"]
    for a in sw["angles"]:
        cx, cy = sw["r"] * math.sin(math.radians(a)), sw["r"] * math.cos(math.radians(a))
        m = Matrix.Translation((cx, cy, 0))
        rr = sw["radius"]
        add("screw_well_%d" % a, Geo().lathe([(0, bz["top_z"] - 0.4), (rr, bz["top_z"] - 0.4), (rr, bz["top_z"] + 0.02), (0, bz["top_z"] + 0.02)], segs=48, m=m),
            "gasket_black", smooth=True)
        add("screw_%d" % a, Geo().lathe([(0, bz["top_z"] + 0.38), (rr * 0.55, bz["top_z"] + 0.34), (rr * 0.82, bz["top_z"] + 0.2), (rr * 0.86, bz["top_z"] - 0.1),
                                         (0, bz["top_z"] - 0.1)], segs=48, m=m), "blue_screw", smooth=True)

    # ---- dial flat to the chapter ring, sloped rehaut up to the bezel (photo map); crystal ----
    add("dial", upward(Geo().lathe([(0, d["z"]), (rg["dial"], d["z"]), (rg["bezel_in"], d["rehaut_z"])], segs=256).mesh(P + "dial", True)), "dial")
    add("crystal", Geo().lathe([(0, cr["z0"]), (rg["bezel_in"] + 0.02, cr["z0"]), (rg["bezel_in"] + 0.02, cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- applied rose-gold numerals and logo (traced), rings round the sub-seconds and the open heart ----
    ix = cfg["applied"]
    shapes = [{"outer": [tuple(q) for q in sh["outer"]], "holes": [[tuple(q) for q in h] for h in sh["holes"]]} for sh in tr["applied_shapes_mm"]]
    add("numerals", plate(shapes, d["z"], d["z"] + ix["height"], P + "numerals"), "gold_polished", bevel=ix["bevel"])
    for key, data in (("sub_ring", tr["sub"]), ("aperture_ring", tr["aperture"])):
        (cx, cy), (r0, r1) = data["centre_mm"], data["ring_mm"]
        h = ix["ring_height"]
        add(key, Geo().lathe([(r0, d["z"]), (r1, d["z"]), (r1, d["z"] + h), (r0 + (r1 - r0) * 0.45, d["z"] + h), (r0, d["z"] + h * 0.3), (r0, d["z"])],
                             segs=128, m=Matrix.Translation((cx, cy, 0))), "gold_polished", smooth=True)

    # ---- hands at the render's time: rose-gold sword frame with an open slot, lume window; red sub-seconds hand ----
    hs, th = cfg["hands"], cfg["hands"]["thickness"]
    for name in ("hour", "minute"):
        h, z = tr["hands"][name], hs["z"][name]
        deg = h["angle_deg"]
        loop = lambda prof: [rot(v, r, deg) for r, v in prof] + [rot(-v, r, deg) for r, v in prof[::-1][1:-1]]
        r0, r1, sh = h["slot_mm"]
        slot = [rot(x, y, deg) for x, y in [(sh, r0), (-sh, r0), (-sh, r1), (sh, r1)]]
        add("hand_" + name, plate([{"outer": loop(h["outline_mm"]), "holes": [slot]}], z, z + th, P + "hand_" + name), "gold_polished", bevel=0.02)
        add("hand_%s_lume" % name, Geo().prism(loop(h["lume_mm"]), z + th * 0.5, z + th + hs["lume_raise"]), "lume")
    hub_r, cap_r = tr["hub_radius_mm"]
    zt = hs["z"]["minute"] + th
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, zt), (hub_r - 0.1, zt + 0.06), (0, zt + 0.06)], segs=64), "gold_polished", smooth=True)
    add("hub_cap", Geo().lathe([(0, zt + 0.06), (cap_r, zt + 0.06), (cap_r, zt + 0.16), (cap_r * 0.6, zt + 0.22), (0, zt + 0.22)], segs=48), "steel_polished", smooth=True)
    sb = tr["sub"]
    (cx, cy), deg, z = sb["centre_mm"], sb["angle_deg"], hs["z"]["sub"]
    pts = [(-sb["tail_half_mm"], -sb["tail_mm"]), (sb["tail_half_mm"], -sb["tail_mm"]), (sb["half_mm"] * 1.6, 0.6), (sb["half_mm"], sb["length_mm"] - 0.15),
           (0, sb["length_mm"]), (-sb["half_mm"], sb["length_mm"] - 0.15), (-sb["half_mm"] * 1.6, 0.6)]
    add("hand_sub", Geo().prism([(cx + x, cy + y) for x, y in (rot(px, py, deg) for px, py in pts)], z, z + th), "hand_red", bevel=0.01)
    add("hub_sub", Geo().lathe([(0, d["z"]), (sb["hub_mm"], d["z"]), (sb["hub_mm"], z + th + 0.05), (0, z + th + 0.05)], segs=48,
                               m=Matrix.Translation((cx, cy, 0))), "hand_red", smooth=True)

    # ---- crown at 3: collar and fluted cylinder on a radial axis ----
    cw_, crn = cfg["crown"], tr["crown"]
    a = math.radians(crn["angle_deg"])
    R0, teeth = crn["radius_mm"], crn["teeth"]
    star = [((R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.cos(math.pi * i / teeth), (R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.sin(math.pi * i / teeth))
            for i in range(teeth * 2)]
    u_, dr_ = (math.cos(a), -math.sin(a), 0), (math.sin(a), math.cos(a), 0)
    m = Matrix((u_, (0, 0, 1), dr_)).transposed().to_4x4()
    m.translation = (0, 0, cw_["z"])
    r0, r1 = crn["r_mm"]
    add("crown_collar", Geo().lathe([(0, r0 - 1.0), (R0 * 0.6, r0 - 1.0), (R0 * 0.6, r0 + 0.4), (0, r0 + 0.4)], segs=48, m=m), "gold_polished", bevel=0.08)
    add("crown", Geo().prism(star, r0 + 0.4, r1 - cw_["end"], m), "gold_polished", bevel=0.15)
    add("crown_end", Geo().lathe([(0, r1 - cw_["end"]), (R0 - 0.1, r1 - cw_["end"]), (R0 - 0.6, r1 - 0.2), (R0 - 1.2, r1), (0, r1)], segs=64, m=m),
        "gold_polished", smooth=True)

    # ---- strap: house curl from the lug tips; each side samples the photo's own straight strap ----
    st = cfg["strap"]
    hw = xi
    zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], tip + st["bend_after_tip"]
    box = curl(bend_y, R, zm)
    g = Geo()
    end_y = bend_y + R * st["arc_over_radius"]
    for sy in (1, -1):
        box(g, -hw, hw, st["start_y"], end_y, ds * st["z0"], ds * st["z1"], sy)
    sm = maps["strap"]
    (ox, oy), (w, h_) = sm["crop_px"], sm["size_px"]
    photo = {sy: tr["strap_mm"][k] for sy, k in ((1, "top"), (-1, "bottom"))}

    def strap_uv(x, y, z):
        p = photo[1 if y > 0 else -1]
        ptip, pend = p["tip_y"], p["end_y"]
        u = min(max((x + hw) / (2 * hw), st["uv_inset"]), 1 - st["uv_inset"])  # side walls take the strap's own edge pixels
        s = abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
        sp = ptip + (s - tip)
        if sp > pend:  # past the photo's full-width strap (rolled under, out of the front view): fold back
            sp = 2 * pend - sp
        k = min(max((sp - ptip) / (pend - ptip), 0.0), 1.0)  # the photo's strap tapers: its edges at this row
        x0, x1 = (a + (b - a) * k for a, b in zip(p["x"], p["x_end"]))
        X, Y = x0 + u * (x1 - x0), math.copysign(sp, y)
        return ((px0 + X * S - ox) / w, 1 - (py0 - Y * S - oy) / h_)
    add("strap", g, "strap", bevel=st["bevel"], uv_of=strap_uv)

    # ---- checks against the anchors ----
    out = {"width_flats": round(2 * rg["ring_out"] * math.cos(math.pi / n), 3), "lug_width": round(2 * xi, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.4, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "strap_end_y_mm": round(end_y, 2),
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
