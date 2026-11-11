"""watch_bulova_98a273: build the Bulova 98A273 (Marine Star Automatic 44 mm, gold tone, black dial, open heart) as a
flat-backed front relief.

Params: spec (config/watches/bulova-98a273.json). Frame as watch_hamilton_scuba_pioneer: mm, origin = hand pivot, dial faces
+z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, bracelet built at final depth
with the house curl. Own construction from the official render: one gold case and lug body from the traced silhouette (crown
guards included), a black polygon ring traced per degree (the gold case shows in its corner notches), a round gold bezel with a
polished inner slope and six black screws, applied gold numerals and logo (traced outlines), gold subdial and open-heart rings,
gold-framed sword hands with lume and an open window, a small seconds hand, a fluted gold crown, and a five-column gold
bracelet. The dial (chapter ring, sunray, prints, subdial, open heart) is the photo map from pipeline/bulova_98a273_dial.py.
Rebuild with --force after regenerating the map (not part of the fingerprint).
"""
import json
import math

import bpy
import numpy as np
from mathutils import Matrix

from pipeline.steps.watch_hamilton_scuba_pioneer import circle, sloped_plate
from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled
from pipeline.steps.watch_speedmaster import Geo, ROOT, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    dm = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | %s front relief" % cfg["model"])
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    mats["dial"] = photo_material("dial_photo", ROOT / cfg["dial_map"], cfg["dial"]["roughness"])
    textured = cfg.get("brushed_textures", {})
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
                me.materials.append(mats[polished_bevel])
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            if polished_bevel:
                m.material = 1
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        elif smooth:
            for poly in me.polygons:
                poly.use_smooth = True
        if not name.startswith("bracelet"):
            o.scale = (1, 1, ds)
        return o

    def upward(me):  # lathe discs: top faces up
        if me.polygons[0].normal.z < 0:
            for poly in me.polygons:
                poly.flip()
            me.update()
        return me

    rg, c, bz, cr, d = tr["rings_mm"], cfg["case"], cfg["bezel"], cfg["crystal"], cfg["dial"]
    lg, tip = cfg["lug"], tr["lug"]["tip_y_mm"]

    # ---- one gold body: case, lugs and crown guards from the traced silhouette; top slopes down toward the lug tips ----
    ho = tr["half_outline_mm"]
    ed = {k: (lambda pts: lambda y: float(np.interp(abs(y), [q[0] for q in pts], [q[1] for q in pts])))(v) for k, v in ho.items()}
    ys = [q[0] for q in ho["right"]]
    right = [(ed["right"](y), y) for y in reversed(ys)] + [(ed["right"](y), -y) for y in ys[1:]]  # top tip -> bottom tip
    left = [(-ed["left"](y), -y) for y in reversed(ys)] + [(-ed["left"](y), y) for y in ys[1:]]  # bottom tip -> top tip
    xi, yc = tr["lug"]["inner_x_mm"], tr["bracelet_mm"]["end_from"]  # between the lugs the case stops where the end link starts
    outline = right + [(xi, -tip), (xi, -yc), (-xi, -yc), (-xi, -tip)] + left + [(-xi, tip), (-xi, yc), (xi, yc), (xi, tip)]
    clean = [outline[0]]
    for q in outline[1:]:
        if math.hypot(q[0] - clean[-1][0], q[1] - clean[-1][1]) > 0.05:
            clean.append(q)
    sf = lg["slope_from_y"]
    top = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * min(1.0, max(0.0, (abs(y) - sf) / (tip - sf)))
    cuts = [sy * (sf + (tip - sf) * k / 8) for sy in (1, -1) for k in range(8)]
    add("case", sloped_plate(clean, 0.0, top, P + "case", (), cuts), "gold_brushed", bevel=lg["bevel"], polished_bevel="gold_polished")

    # ---- black polygon ring (outer edge traced per degree) under the gold bezel, on a gold skirt out to the silhouette ----
    br_ = tr["black_ring_r_mm"]
    sk = [min(max(s_, r), r + c["skirt_max"]) if not 80 <= a <= 100 else r for a, (s_, r) in enumerate(zip(tr["silhouette_r_mm"], br_))]
    add("case_skirt", plate([{"outer": [rot(0, r, a) for a, r in enumerate(sk)][::-1], "holes": [circle(rg["bezel_out"] - 1.0, 192)]}],
                            0.0, c["ring_z"][0] + 0.2, P + "case_skirt"), "gold_brushed", bevel=0.3, polished_bevel="gold_polished")
    ring = [rot(0, r, a) for a, r in enumerate(br_)]
    z0, z1 = c["ring_z"]
    add("black_ring", plate([{"outer": ring[::-1], "holes": [circle(rg["bezel_out"] - 0.4, 192)]}], z0, z1, P + "black_ring"),
        "pvd_black", bevel=c["ring_bevel"])

    # ---- gold bezel: brushed flat top, polished slope down to the crystal; six black screws ----
    zt, zl = bz["top_z"], bz["lip_z"]
    add("bezel_top", Geo().lathe([(rg["bezel_flat"], z1 - 0.2), (rg["bezel_out"], z1 - 0.2), (rg["bezel_out"], zt - 0.25),
                                  (rg["bezel_out"] - 0.25, zt), (rg["bezel_flat"], zt)], segs=256), "gold_satin", smooth=True)
    add("bezel_slope", Geo().lathe([(rg["bezel_in"], z1 - 0.2), (rg["bezel_flat"] + 0.01, z1 - 0.2), (rg["bezel_flat"] + 0.01, zt),
                                    (rg["bezel_in"], zl)], segs=256), "gold_polished", smooth=True)
    sc, sz = tr["screws"], cfg["screws"]
    heads, sockets = Geo(), Geo()
    for a in sc["angles_deg"]:
        x, y = rot(0, sc["r_mm"], a)
        R_ = sc["radius_mm"]
        m = Matrix.Translation((x, y, 0))
        heads.lathe([(0, zt - 0.3), (R_, zt - 0.3), (R_, zt + sz["height"] - 0.12), (R_ - 0.15, zt + sz["height"]), (0, zt + sz["height"])], segs=48, m=m)
        hexa = [(x + sc["socket_mm"] * math.cos(math.pi / 3 * k + math.pi / 6), y + sc["socket_mm"] * math.sin(math.pi / 3 * k + math.pi / 6)) for k in range(6)]
        sockets.prism(hexa, zt + sz["height"] - 0.06, zt + sz["height"] + 0.01)
    add("screws", heads, "pvd_black", smooth=True)
    add("screw_sockets", sockets, "socket_dark")

    # ---- crystal and dial ----
    add("crystal", Geo().lathe([(0, cr["z0"]), (rg["bezel_in"] + 0.05, cr["z0"]), (rg["bezel_in"] + 0.05, cr["z1"]), (0, cr["z1"])], segs=192), "crystal")
    me = upward(Geo().lathe([(0, d["z"]), (rg["bezel_in"] + 0.05, d["z"]), (rg["bezel_in"] + 0.05, d["z"] - 0.3)], segs=256).mesh(P + "dial", True))
    uv = me.uv_layers.new(name="UVMap")
    H = dm["half_size_mm"]
    for loop_ in me.loops:
        x, y, _ = me.vertices[loop_.vertex_index].co
        uv.data[loop_.index].uv = (0.5 + x / (2 * H), 0.5 + y / (2 * H))
    add("dial", me, "dial")

    # ---- applied gold: numerals and logo (traced outlines), subdial and open-heart rings ----
    ap = cfg["applied"]
    shapes = [{"outer": [tuple(q) for q in s["outer"]], "holes": [[tuple(q) for q in h] for h in s["holes"]]} for s in tr["applied_gold_mm"]]
    add("numerals", plate(shapes, d["z"], d["z"] + ap["height"], P + "numerals"), "gold_polished", bevel=ap["bevel"])
    sd, ht = tr["subdial"], tr["heart"]
    for name, (cx, cy), (r0, r1) in (("subdial_ring", sd["centre_mm"], sd["ring_mm"]), ("heart_ring", ht["centre_mm"], (ht["ring_in_mm"], ht["ring_out_mm"]))):
        add(name, Geo().lathe([(r0, d["z"]), (r1, d["z"]), (r1, d["z"] + ap["ring_height"]), (r0 + 0.1, d["z"] + ap["ring_height"])], segs=128,
                              m=Matrix.Translation((cx, cy, 0))), "gold_polished", smooth=True)

    # ---- hands at the render's time: gold frame with an open window, lume inlay ----
    hs, th = cfg["hands"], cfg["hands"]["thickness"]
    for name, h in tr["hands"].items():
        z = hs["z"][name]
        add("hand_" + name, plate([{"outer": [tuple(q) for q in h["outline_mm"]], "holes": [[tuple(q) for q in h["window_mm"]]]}], z, z + th, P + "hand_" + name),
            "gold_polished", bevel=0.02)
        add("hand_%s_lume" % name, plate([{"outer": [tuple(q) for q in h["lume_mm"]], "holes": []}], z + th, z + th + hs["lume"], P + "lume_" + name), "lume")
    hub = tr["hub_mm"]
    zm_ = hs["z"]["minute"] + th
    add("hub", Geo().lathe([(0, d["z"]), (hub["collar"], d["z"]), (hub["collar"], zm_), (hub["collar"] - 0.15, zm_ + 0.05), (0, zm_ + 0.05)], segs=64), "gold_polished", smooth=True)
    add("hub_pin", Geo().lathe([(0, zm_), (hub["pin"], zm_), (hub["pin"], zm_ + 0.1), (hub["pin"] * 0.6, zm_ + 0.15), (0, zm_ + 0.15)], segs=48), "steel_pin", smooth=True)
    # small seconds: needle to the pointer end, paddle tail, hub
    deg, L, tl = sd["hand_angle_deg"], sd["hand_length_mm"], sd["tail_mm"]
    (h0, h1), tw = sd["half_mm"], sd["tail_half_mm"]
    cx, cy = sd["centre_mm"]
    zs = hs["z"]["small_seconds"]
    pts = [(-tw, -tl), (tw, -tl), (h0, 0), (h1, L), (-h1, L), (-h0, 0)]
    add("hand_small_seconds", Geo().prism([(cx + p[0], cy + p[1]) for p in (rot(x, y, deg) for x, y in pts)], zs, zs + th), "gold_polished", bevel=0.01)
    add("hand_small_seconds_hub", Geo().lathe([(0, d["z"]), (sd["hub_mm"], d["z"]), (sd["hub_mm"], zs + th + 0.04), (0, zs + th + 0.04)], segs=32,
                                              m=Matrix.Translation((cx, cy, 0))), "gold_polished", smooth=True)

    # ---- fluted gold crown on the 3 o'clock axis, collar into the case ----
    cw, tc = cfg["crown"], tr["crown"]
    m = Matrix(((0, -1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_4x4()  # local z along +x, local y up
    m.translation = (0.0, tc["centre_y_mm"], cw["z"])
    R0, (r1, r2) = tc["radius_mm"], tc["r_from_to_mm"]
    star = [((R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.cos(math.pi * i / tc["teeth"]),
             (R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.sin(math.pi * i / tc["teeth"])) for i in range(tc["teeth"] * 2)]
    add("crown_collar", Geo().lathe([(0, tc["collar_mm"] - 1.0), (R0 * 0.62, tc["collar_mm"] - 1.0), (R0 * 0.62, r1 + 0.2), (0, r1 + 0.2)], segs=48, m=m),
        "gold_polished", smooth=True)
    add("crown", Geo().prism(star, r1, r2 - cw["end"], m), "gold_polished", bevel=0.1)
    add("crown_end", Geo().lathe([(0, r2 - cw["end"]), (R0 - 0.15, r2 - cw["end"]), (R0 - 0.5, r2 - cw["end"] * 0.3), (R0 - 1.0, r2), (0, r2)], segs=64, m=m),
        "gold_polished", smooth=True)

    # ---- five-column gold bracelet: end links straight to the first joints, links with the house curl from the lug tips ----
    br, bt, el = cfg["bracelet"], tr["bracelet_mm"], cfg["end_link"]
    e0, e1, e2 = bt["edges"]
    gap, pitch = br["gap"], bt["pitch"]
    zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]
    box = curl(tip + br["bend_after_tip"], R, zm)
    end_y = tip + br["bend_after_tip"] + R * br["arc_over_radius"]
    za, zb = ds * br["z0"], ds * br["z1"]
    cols = {"outer": [(e1 + gap, e2), (-e2, -e1 - gap)], "mid": [(e0 + gap, e1), (-e1, -e0 - gap)], "centre": [(-e0, e0)]}
    phase = {"outer": bt["joints_outer"][0], "centre": bt["joints_outer"][0], "mid": bt["joints_mid"][0]}
    raise_ = {"centre": ds * br["centre_raise"], "outer": 0.0, "mid": 0.0}
    links, ends, back = Geo(), Geo(), Geo()
    rows = 0
    for sy in (1, -1):
        for kind, xs in cols.items():
            for x0, x1 in xs:
                box(ends, x0, x1, bt["end_from"], phase[kind] - gap, ds * el["z0"], ds * el["top_z"] + raise_[kind], sy)
                y0 = phase[kind]
                while y0 < end_y - 0.3:
                    y1 = min(y0 + pitch - gap, end_y)
                    box(links, x0, x1, y0, y1, za, zb + raise_[kind], sy)
                    rows += kind == "centre"
                    y0 = y1 + gap
        y0 = min(phase.values())
        while y0 < end_y - 0.3:  # dark backing so the joints read as shadow lines
            y1 = min(y0 + pitch, end_y)
            box(back, -e2 + 0.3, e2 - 0.3, y0 - gap, y1, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
            y0 = y1
    add("bracelet_end_links", ends, "gold_brushed", bevel=el["bevel"], polished_bevel="gold_polished")
    add("bracelet_links", links, "gold_brushed", bevel=br["bevel"], polished_bevel="gold_polished")
    add("bracelet_backing", back, "joint_dark")

    # ---- checks against the official anchors ----
    out = {"case_width": round(2 * float(np.mean([br_[a] for a in list(range(84, 97)) + list(range(264, 277))])), 3),
           "lug_width": round(2 * e2, 3), "case_length": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.6, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "bracelet_end_y_mm": round(end_y, 2), "bracelet_rows": rows,
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
