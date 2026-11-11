"""watch_bulova_96a225: build the Bulova 96A225 (Lunar Pilot, 45 mm chronograph, black dial, black NATO strap) as a
flat-backed front relief.

Params: spec (config/watches/bulova-96a225.json). Same frame, pose, 2.5D depth scale and materials as watch_bulova_96b431 /
watch_tissot_t120407 (strap with the house curl and a photo map). Parts from Bulova's official render: one polished cushion case
slab from the traced silhouette (left and right edges, pushers at 2 and 4 included), a polished bezel ring, house glass, the
photo-mapped dial (black dial, subdials, flange and tachymeter ring), applied indices (polished frame round lume) about the ring
centre, white lume batons in polished frames, a white chrono needle with a lozenge, white subdial needles on polished hubs, a
fluted crown, and the NATO strap (photo map, keepers included) rolled under from the case edges. Maps from
pipeline/bulova_96a225_dial.py; rebuild with --force after regenerating them (they are not part of the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

import numpy as np

from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled
from pipeline.steps.watch_speedmaster import Geo, ROOT, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    coll = bpy.data.collections.new("WATCH | %s front relief" % cfg["model"])
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    maps = {}
    for key, pm in cfg["photo_maps"].items():  # dial and strap
        mats[key] = photo_material(key, ROOT / pm["image"], pm["roughness"])
        maps[key] = json.loads((ROOT / pm["image"]).with_suffix(".json").read_text())
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
    H, (ox, oy) = maps["dial"]["half_size_mm"], maps["dial"]["centre_offset_mm"]
    dial_uv = lambda x, y, z: (0.5 + (x - ox) / (2 * H), 0.5 + (y - oy) / (2 * H))  # planar about the map centre

    def add(name, geo, mat, bevel=None, polished_bevel=False, uv_of=None, smooth=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured:  # planar UV in mm / tile, lines along the 12-6 axis (model Y)
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
                me.materials.append(mats["steel_polished"])
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            if polished_bevel:
                m.material = 1
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        elif smooth:
            for poly in me.polygons:
                poly.use_smooth = True
        if not name.startswith("strap"):
            o.scale = (1, 1, ds)
        return o

    circle = lambda r, n=192, cx=0.0, cy=0.0: [(cx + r * math.sin(2 * math.pi * k / n), cy + r * math.cos(2 * math.pi * k / n)) for k in range(n)]
    cx, cy = tr["ring_centre_mm"]
    rg = tr["rings_mm"]
    centred = Matrix.Translation((cx, cy, 0))

    # ---- polished cushion case: one slab from the silhouette, top sloping down toward the strap ends ----
    cs = cfg["case"]
    co = tr["case_outline_mm"]
    tip = tr["case_edge_mm"]["mean"]
    outline = [(x, y) for y, x in co["right"]] + [(x, y) for y, x in co["left"][::-1]]
    clean = [outline[0]]
    for q in outline[1:]:
        if math.hypot(q[0] - clean[-1][0], q[1] - clean[-1][1]) > 0.05:
            clean.append(q)
    # domed: a polar grid from the bezel out to the silhouette at each angle, full height at the bezel falling to edge_z at the
    # rim along every ray (smooth top), then a short flat wall down to the back
    rb = rg["bezel_out"] - 0.1
    na, nr = 360, 12
    rim = []
    for i in range(na):
        a = 2 * math.pi * i / na
        dx, dy = math.sin(a), math.cos(a)
        best = None
        for (x1, y1), (x2, y2) in zip(clean, clean[1:] + clean[:1]):  # ray from the ring centre against each outline edge
            ex, ey = x2 - x1, y2 - y1
            den = dx * ey - dy * ex
            if abs(den) < 1e-12:
                continue
            t_ = ((x1 - cx) * ey - (y1 - cy) * ex) / den
            u_ = ((x1 - cx) * dy - (y1 - cy) * dx) / den
            if t_ > 0 and 0 <= u_ <= 1 and (best is None or t_ > best):
                best = t_
        rim.append((dx, dy, best))
    g = Geo()
    for i, (dx, dy, R_) in enumerate(rim):
        for k in range(nr + 1):
            f_ = k / nr
            r_ = rb + (R_ - rb) * f_
            g.v.append((cx + dx * r_, cy + dy * r_, cs["top_z"] - (cs["top_z"] - cs["edge_z"]) * f_ ** cs["dome_power"]))
        g.v.append((cx + dx * R_, cy + dy * R_, 0.0))
    st_ = nr + 2
    for i in range(na):
        a0, a1 = i * st_, ((i + 1) % na) * st_
        for k in range(nr):  # top, counter-clockwise seen from +z
            g.f.append((a0 + k, a0 + k + 1, a1 + k + 1, a1 + k))
            g.smooth.append(True)
        g.f.append((a0 + nr, a0 + nr + 1, a1 + nr + 1, a1 + nr))  # outer wall
        g.smooth.append(False)
    me = g.mesh(P + "case", None)
    if sum(1 for poly in me.polygons if poly.normal.z < -0.5) > len(me.polygons) / 3:  # winding came out inverted: flip all
        for poly in me.polygons:
            poly.flip()
        me.update()
    add("case", me, "steel_polished")
    add("case_top", Geo().lathe([(0, 0.0), (rb + 0.1, 0.0), (rb + 0.1, cs["top_z"]), (0, cs["top_z"])], segs=192, m=centred), "steel_polished")

    # ---- polished bezel ring (rounded), crystal ----
    bz, cr = cfg["bezel"], cfg["crystal"]
    ti_, to_ = rg["tach_out"], rg["bezel_out"]
    add("bezel", Geo().lathe([(ti_, bz["z0"]), (to_, bz["z0"]), (to_, bz["outer_z"]), (to_ - 0.5, bz["top_z"]), (ti_ + 0.3, bz["top_z"]), (ti_, bz["inner_z"])],
                             segs=256, m=centred), "steel_polished", smooth=True)
    add("crystal", Geo().lathe([(0, cr["z0"]), (ti_, cr["z0"]), (ti_, cr["z1"]), (0, cr["z1"])], segs=192, m=centred), "crystal")

    # ---- dial, flange and tachymeter ring: one surface, photo map ----
    d = cfg["dial"]
    me = Geo().lathe([(0, d["z"]), (rg["dial_out"], d["z"]), (rg["flange_out"], d["flange_z"]), (rg["flange_out"] + 0.05, d["tach_z"]), (ti_, d["tach_z"])],
                     segs=256, m=centred).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    add("dial", me, "dial")

    # ---- applied indices about the ring centre: polished frame, lume ----
    ix, ti = cfg["indices"], tr["indices"]
    z0, z1, fw = d["z"], d["z"] + ix["height"], ti["frame_mm"]
    frames, lume = [], Geo()
    for v in ti["kinds"].values():
        (r0, r1), hw = v["r_mm"], v["half_mm"]
        for hr in v["hours"]:
            pl = lambda k: [(cx + p[0], cy + p[1]) for p in (rot(x, y, hr * 30) for x, y in ((-hw + k, r0 + k), (hw - k, r0 + k), (hw - k, r1 - k), (-hw + k, r1 - k)))]
            frames.append({"outer": [list(p) for p in pl(0)], "holes": [[list(p) for p in pl(fw)][::-1]]})
            lume.prism(pl(fw), z0, z1 - ix["lume_recess"])
    add("indices", plate(frames, z0, z1, P + "indices"), "steel_polished", bevel=0.03)
    add("index_lume", lume, "lume")

    # ---- hands at the render's time ----
    hs, th = cfg["hands"], cfg["hands"]["thickness"]
    for name, h in tr["hands"].items():
        z, mat, deg = hs["z"][name], hs["material"][name], h["angle_deg"]
        g = Geo()
        for lp in h["body_mm"]:
            g.prism([rot(x, y, deg) for x, y in lp], z, z + th)
        add("hand_" + name, g, mat, bevel=0.02)
        if h["lume_mm"]:
            lg_ = Geo()
            for lp in h["lume_mm"]:
                lg_.prism([rot(x, y, deg) for x, y in lp], z + th, z + th + hs["lume"])
            add("hand_%s_lume" % name, lg_, "lume")
    hub = tr["hub_mm"]
    zt = hs["z"]["chrono"] + th
    add("hub", Geo().lathe([(0, d["z"]), (hub["disc"], d["z"]), (hub["disc"], zt), (0, zt)], segs=64), "steel_polished", smooth=True)
    add("hub_ring", Geo().lathe([(0, zt), (hub["ring"], zt), (hub["ring"], zt + 0.08), (0, zt + 0.08)], segs=64), "steel_polished", smooth=True)
    add("hub_pin", Geo().lathe([(0, zt + 0.08), (hub["pin"], zt + 0.08), (hub["pin"], zt + 0.14), (0, zt + 0.14)], segs=32), "hand_dark")
    zs = hs["z"]["subdial"]
    for key, sd in tr["subdials"].items():  # white needles on small polished hubs
        (sx_, sy_), L, w_, hb = sd["centre_mm"], sd["length_mm"], sd["half_mm"], sd["hub_mm"]
        poly = [(lambda p: (sx_ + p[0], sy_ + p[1]))(rot(x, y, sd["angle_deg"])) for x, y in ((-w_, -0.3), (w_, -0.3), (w_ * 0.6, L), (-w_ * 0.6, L))]
        add("subdial_%s_hand" % key, Geo().prism(poly, zs, zs + th), "hand_white")
        add("subdial_%s_hub" % key, Geo().lathe([(0, d["z"]), (hb, d["z"]), (hb, zs + th + 0.04), (hb * 0.6, zs + th + 0.08), (0, zs + th + 0.08)], segs=48,
                                                m=Matrix.Translation((sx_, sy_, 0))), "steel_polished", smooth=True)

    # ---- fluted crown on the 3 o'clock axis ----
    cw_, tc = cfg["crown"], tr["crown"]
    m = Matrix(((0, -1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_4x4()  # local z along +x, local y up
    m.translation = (0.0, tc["centre_y_mm"], cw_["z"])
    R0, (r1, r2), n_ = tc["radius_mm"] * cw_["radius_factor"], tc["x_from_to_mm"], tc["teeth"]
    star = [((R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.cos(math.pi * i / n_),
             (R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.sin(math.pi * i / n_)) for i in range(n_ * 2)]
    add("crown_collar", Geo().lathe([(0, cw_["collar"][0]), (cw_["collar_r"], cw_["collar"][0]), (cw_["collar_r"], r1 + 0.2), (0, r1 + 0.2)], segs=48, m=m),
        "steel_polished", smooth=True)
    add("crown", Geo().prism(star, r1, r2 - cw_["end"], m), "steel_polished", bevel=0.1)
    add("crown_end", Geo().lathe([(0, r2 - cw_["end"]), (R0 - 0.1, r2 - cw_["end"]), (R0 - 0.4, r2 - cw_["end"] * 0.3), (R0 - 1.0, r2), (0, r2)],
                                 segs=64, m=m), "steel_polished", smooth=True)

    # ---- NATO strap: house curl from the case edges, the render's width, the strap rows (edges aligned) ----
    st, sm = cfg["strap"], maps["strap"]
    zm, R = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"]
    bend_y = tip + st["bend_after_tip"]
    end_y = bend_y + R * st["arc_over_radius"]
    taper = tr["strap"]["half_width_by_s_mm"]
    hw0 = max(q[1] for q in taper)
    hw = lambda s: float(np.interp(max(s - tip, 0.0), [q[0] for q in taper], [q[1] for q in taper]))
    box = curl(bend_y, R, zm)
    g = Geo()
    for sy in (1, -1):
        box(g, -hw0, hw0, st["from_y"], end_y, ds * st["z0"], ds * st["z1"], sy)
    s_of = lambda y, z: abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
    g.v = [(x * hw(s_of(y, z)) / hw0, y, z) for x, y, z in g.v]
    edges = [tr["case_edge_mm"]["top"], tr["case_edge_mm"]["bottom"]]
    rows_h = sm["size_px"][1]

    def strap_uv(x, y, z):
        top_side = y > 0
        side = sm["top"] if top_side else sm["bottom"]
        s = s_of(y, z)
        sp = s - tip + edges[0 if top_side else 1]
        i = (sp - side["first_s_mm"]) * sm["rows_per_mm"]
        i = min(max(i, 0.0), 2 * side["rows"] - 1.0)
        if i > side["rows"] - 1:  # past the render's edge (rolled under, out of the front view): fold back
            i = 2 * (side["rows"] - 1) - i
        row = i + (0 if top_side else sm["top"]["rows"])
        u = min(max((x / hw(s) + 1) / 2, st["uv_inset"]), 1 - st["uv_inset"])
        return (u, 1 - (row + 0.5) / rows_h)
    add("strap", g, "strap", uv_of=strap_uv, smooth=True)

    # ---- checks against the anchors ----
    out = {"case_width": round(2 * max(-x for y, x in co["left"]), 3), "case_length": round(2 * tip, 3), "strap_width": round(2 * hw(tip + 5), 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.5, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "case_edge_y_mm": tip, "strap_end_y_mm": round(end_y, 2), "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
