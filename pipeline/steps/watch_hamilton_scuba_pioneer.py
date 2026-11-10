"""watch_hamilton_scuba_pioneer: build the Hamilton H82395331 (Khaki Navy Scuba, orange rubber) or H76255810 (Khaki Aviation
Pilot Pioneer, green leather) as a flat-backed front relief.

Params: spec (config/watches/hamilton-<sku>.json). Frame as watch_orient_re_at0007n00b: mm, origin = hand pivot, dial faces
+z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, strap built at final depth
with the house curl. House method: modelled brushed case, lugs and crown guards, polished coin-edge bezel and crown, house glass,
modelled hands (and the Scuba's applied indices); two photo maps (pipeline/hamilton_scuba_pioneer_dial.py): the dial with the
bezel insert, and the strap. The photo is a little turned: model mm -> photo px through the trace's photo_rot_deg, so the
maps are used as taken. Rebuild with --force after regenerating the maps.
"""
import json
import math

import bpy
import numpy as np
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rot


def circle(r, n, cx=0.0, cy=0.0):
    return [(cx + r * math.sin(2 * math.pi * k / n), cy + r * math.cos(2 * math.pi * k / n)) for k in range(n)]


def sloped_plate(outline, z0, top, name, holes=(), cuts_y=()):
    """plate() (outline with holes, mm) whose top vertices take z = top(x, y): sloped lug tops. The mesh is first cut along
    each y in cuts_y, so no face spans a break in the slope (a long tessellation triangle would show as a wrong facet)."""
    import bmesh
    me = plate([{"outer": outline, "holes": list(holes)}], z0, 999.0, name)
    bm = bmesh.new()
    bm.from_mesh(me)
    for y in cuts_y:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=(0, y, 0), plane_no=(0, 1, 0))
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges[:])
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    for v in bm.verts:
        if v.co.z > 998:
            v.co.z = top(v.co.x, v.co.y)
    bm.to_mesh(me)
    bm.free()
    me.update()
    return me


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    coll = bpy.data.collections.new("WATCH | %s front relief" % cfg["model"])
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    maps = {}
    for key, pm in cfg["photo_maps"].items():  # dial (+ insert) and strap
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
    S, (px0, py0), pr = tr["scale_px_per_mm"], tr["origin_px"], tr["photo_rot_deg"]

    def photo_uv(key, x, y):  # model mm -> photo px (the photo is turned by pr) -> map uv
        m = maps[key]
        xr, yr = rot(x, y, pr)
        (cx, cy), k, (w, h) = m["crop_px"], m["scale"], m["size_px"]
        return ((px0 + xr * S - cx) * k / w, 1 - (py0 - yr * S - cy) * k / h)

    def add(name, geo, mat, bevel=None, polished_bevel=False, uv_of=None, smooth=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured:  # planar UV, lines along the strap axis (model Y)
            uv, tile = me.uv_layers.new(name="UVMap"), textured[mat]["tile_mm"]
            for loop in me.loops:
                x, y, _ = me.vertices[loop.vertex_index].co
                uv.data[loop.index].uv = (y / tile, -x / tile)
        if mat in maps:
            f = uv_of or (lambda x, y, z: photo_uv(mat, x, y))
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
        if not name.startswith(("strap", "bracelet")):
            o.scale = (1, 1, ds)
        return o

    def upward(me):  # lathe discs: top faces up
        if me.polygons[0].normal.z < 0:
            for poly in me.polygons:
                poly.flip()
            me.update()
        return me

    rg = tr["rings_mm"]
    c, bz, cr, d = cfg["case"], cfg["bezel"], cfg["crystal"], cfg["dial"]

    if "half_outline_mm" in tr:  # one body from the traced head outline: case, lugs and the crown-side flank or guards
        ho, lg = tr["half_outline_mm"], cfg["lug"]
        tip, xi = tr["lug"]["tip_y_mm"], tr["lug"]["inner_x_mm"]
        ed = {k: (lambda pts: lambda y: float(np.interp(abs(y), [q[0] for q in pts], [q[1] for q in pts])))(v) for k, v in ho.items()}
        ys = [k * 0.25 for k in range(int(tip / 0.25) + 1)] + [tip]
        if "notch_y" in c:  # straight case edge between the horns (cushion case, strap through fixed bars)
            yc = c["notch_y"]
            arc = lambda sy: [(-xi, sy * yc), (xi, sy * yc)]
        else:
            rn = c["notch_radius"]
            yc = math.sqrt(rn * rn - xi * xi)
            arc = lambda sy: [(-xi + 2 * xi * k / 16, sy * math.sqrt(rn * rn - (-xi + 2 * xi * k / 16) ** 2)) for k in range(17)]
        right = [(ed["right"](y), y) for y in reversed(ys)] + [(ed["right"](y), -y) for y in ys[1:]]  # top tip -> bottom tip
        left = [(-ed["left"](y), -y) for y in reversed(ys)] + [(-ed["left"](y), y) for y in ys[1:]]  # bottom tip -> top tip
        outline = right + [(xi, -tip), (xi, -yc)] + arc(-1)[::-1] + [(-xi, -yc), (-xi, -tip)] + left + [(-xi, tip), (-xi, yc)] + arc(1) + [(xi, yc), (xi, tip)]
        clean = [outline[0]]
        for q in outline[1:]:
            if math.hypot(q[0] - clean[-1][0], q[1] - clean[-1][1]) > 0.05:
                clean.append(q)
        top = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * min(1.0, max(0.0, (abs(y) - lg["slope_from_y"]) / (tip - lg["slope_from_y"])))
        mat = c.get("material", "steel_brushed")
        sf = lg["slope_from_y"]
        cuts = [sy * (sf + (tip - sf) * k / 8) for sy in (1, -1) for k in range(8)]
        add("case", sloped_plate(clean, 0.0, top, P + "case", [circle(rg["dial"] + 0.02, 192)], cuts), mat, bevel=lg["bevel"], polished_bevel="steel_polished" if mat != "steel_polished" else False)
    else:
        tip, xi = tr["lug"]["tip_y_mm"], tr["lug"]["inner_x_mm"]
    # ---- case under the bezel (brushed), lugs and crown guards from the trace ----
    rc, zc = c.get("radius", 0), c["top_z"]
    if "half_outline_mm" not in tr:
        ri = rg["dial"] + 0.05  # a ring: open over the dial
        add("case", Geo().lathe([(ri, 0), (rc - 0.4, 0), (rc, 0.4), (rc, zc - 0.4), (rc - 0.4, zc), (ri, zc), (ri, 0)], segs=192), "steel_brushed")
        lg, tl = cfg["lug"], tr["lug"]
        tip, xi = tl["tip_y_mm"], tl["inner_x_mm"]
        outer = [(xi + off, tip - dd) for dd, off in tl["outer_offset_by_depth"]]
        last = outer[-1]
        r_in = rg["insert_in"] + 0.3  # close the outline under the bezel insert: never inside the dial opening
        a0, a1 = math.atan2(last[0], last[1]), math.asin(xi / r_in)
        arc = [(r_in * math.sin(a0 + (a1 - a0) * k / 6), r_in * math.cos(a0 + (a1 - a0) * k / 6)) for k in range(7)]
        poly = [(xi, tip)] + outer[1:] + arc
        top = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * min(1.0, max(0.0, (abs(y) - lg["slope_from_y"]) / (tip - lg["slope_from_y"])))
        g = Geo()
        for sx in (1, -1):
            for sy in (1, -1):
                slab(g, [(sx * x, sy * y) for x, y in poly], 0.0, top)
        add("lugs", g, "steel_brushed", bevel=lg["bevel"], polished_bevel="steel_polished")
        if "crown_guard_mm" in tr:
            (ra, za), (rb, zb) = c["guard_top"]  # top falls away outward so the crown stands in front of it
            gtop = lambda x, y: za + (zb - za) * min(1.0, max(0.0, (math.hypot(x, y) - ra) / (rb - ra)))
            add("crown_guards", slab(Geo(), [tuple(p) for p in tr["crown_guard_mm"]], 0.0, gtop), "steel_brushed",
                bevel=lg["bevel"], polished_bevel="steel_polished")

    if "teeth" in tr:
        # ---- bezel: smooth skirt, coin-edge ring (teeth + polished flat to the insert), photo-mapped insert, crystal ring ----
        n, tip_r, notch_r = tr["teeth"], rg["tooth_tip"], rg["notch"]
        star = [(lambda a, f: ((tip_r - (tip_r - notch_r) * (1 - math.sin(math.pi * f)) ** 2) * math.sin(a),
                               (tip_r - (tip_r - notch_r) * (1 - math.sin(math.pi * f)) ** 2) * math.cos(a)))(2 * math.pi * k / (8 * n), (k % 8) / 8)
                for k in range(8 * n)]  # rounded notches between full lobes
        z0, z1 = bz["z0"], bz["top_z"]
        # dark skirt under the teeth: the notches read as shadow; the lobes are rounded so each catches its own highlight
        add("bezel_skirt", Geo().lathe([(notch_r - 0.3, z0), (tip_r, z0), (tip_r, z0 + bz["skirt_h"]), (notch_r - 0.3, z0 + bz["skirt_h"])],
                                       segs=192), "bezel_shadow", smooth=True)
        add("bezel_teeth", plate([{"outer": star, "holes": [circle(notch_r - 0.15, 192)]}], z0 + bz["skirt_h"] * 0.5, z1 - bz["teeth_drop"], P + "bezel_teeth"),
            "steel_polished", bevel=bz["teeth_bevel"])
        add("bezel_rim", Geo().lathe([(rg["rim_in"] - 0.02, z0), (notch_r - 0.1, z0), (notch_r - 0.1, z1 - 0.1), (notch_r - 0.2, z1),
                                      (rg["rim_in"] - 0.02, z1), (rg["rim_in"] - 0.02, z0)], segs=256), "steel_polished", smooth=True)
        zi_in, zi_out = bz["insert_z"]
        add("bezel_insert", Geo().lathe([(rg["insert_in"], z0), (rg["rim_in"], z0), (rg["rim_in"], z1 - bz["chamfer"]), (rg["insert_out"], zi_out),
                                         (rg["insert_in"], zi_in), (rg["insert_in"], z0)], segs=256), "dial", smooth=True)
        add("crystal_ring", Geo().lathe([(rg["crystal"] - 0.05, cr["z0"]), (rg["insert_in"] + 0.02, cr["z0"]), (rg["insert_in"] + 0.02, zi_in - 0.02),
                                         (rg["crystal"] + 0.05, zi_in - 0.06)], segs=192), "steel_polished", smooth=True)
        add("crystal", Geo().lathe([(0, cr["z0"]), (rg["insert_in"], cr["z0"]), (rg["insert_in"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    else:  # smooth polished bezel from the spec profile; black rehaut ring from the dial edge up to the crystal
        add("bezel", Geo().lathe([tuple(q) for q in bz["profile_rz"]], segs=256), bz.get("material", "steel_polished"), smooth=True)
        if "insert_z" in bz:  # photo-mapped insert ring between the polished rings (dial map)
            zi0, zi1 = bz["insert_z"]
            add("bezel_insert", Geo().lathe([(rg["insert_in"], zi0 - 0.3), (rg["insert_out"], zi0 - 0.3), (rg["insert_out"], zi1),
                                             (rg["insert_in"], zi0), (rg["insert_in"], zi0 - 0.3)], segs=256), "dial", smooth=True)
        add("rehaut", Geo().lathe([(rg["dial"] - 0.02, d["z"]), (rg["bezel_in"] + 0.02, cr["z0"] - 0.05), (rg["bezel_in"] + 0.02, cr["z0"])], segs=256),
            d.get("rehaut_material", "gasket_black"), smooth=True)
        add("crystal", Geo().lathe([(0, cr["z0"]), (rg["bezel_in"] + 0.02, cr["z0"]), (rg["bezel_in"] + 0.02, cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial: flat to the crystal ring, short wall up to the crystal seat (photo map) ----
    add("dial", upward(Geo().lathe([(0, d["z"]), (rg["dial"], d["z"]), (rg["dial"], cr["z0"])], segs=256).mesh(P + "dial", True)), "dial")

    # ---- applied indices (traced): polished frames with lume ----
    if "numerals_mm" in tr:  # applied polished numerals (outline with holes)
        shapes = [{"outer": [tuple(q) for q in sh["outer"]], "holes": [[tuple(q) for q in h] for h in sh["holes"]]}
                  for glyph in tr["numerals_mm"].values() for sh in glyph]
        add("numerals", plate(shapes, d["z"], d["z"] + cfg["indices"]["height"], P + "numerals"), "steel_polished", bevel=0.03)
    if "indices" in tr and "outline_mm" in next(iter(tr["indices"].values())):  # applied polished indices without lume
        g = Geo()
        for sh in tr["indices"].values():
            for hr in sh["hours"]:
                g.prism([rot(x, y, 30 * hr) for x, y in sh["outline_mm"]], d["z"], d["z"] + cfg["indices"]["height"])
        add("indices", g, "steel_polished", bevel=0.04)
    elif "indices" in tr:
        ix = cfg["indices"]
        frames, lume = Geo(), Geo()
        for sh in tr["indices"].values():
            for hr in sh["hours"]:
                frames.prism([rot(x, y, 30 * hr) for x, y in sh["frame_mm"]], d["z"], d["z"] + ix["height"])
                lume.prism([rot(x, y, 30 * hr) for x, y in sh["lume_mm"]], d["z"] + ix["height"], d["z"] + ix["height"] + ix["lume_height"])
        add("indices", frames, "steel_polished", bevel=0.03)
        add("index_lume", lume, "lume")

    # ---- hands at the photo's time: traced parts per layer (base plate, thin top inlays) and material role ----
    hs, th = cfg["hands"], cfg["hands"]["thickness"]
    for name, h in tr["hands"].items():
        z = hs["z"][name]
        groups = {}
        for part in h["parts"]:
            groups.setdefault((part["layer"], part["mat"]), []).append(part["poly_mm"])
        for (layer, role), polys in sorted(groups.items()):
            g = Geo()
            za, zb = (z, z + th) if layer == "base" else (z + th, z + th + hs["inlay"][role])
            for poly in polys:
                g.prism([tuple(q) for q in poly], za, zb)
            mat = hs["materials"][role]
            if layer == "base":
                add("hand_%s_%s" % (name, role), g, mat, bevel=0.02, polished_bevel="steel_polished" if role in hs.get("polished_edge", []) else False)
            else:
                add("hand_%s_%s_inlay" % (name, role), g, mat)
    hub, z = tr["hub_mm"], hs["z"]["seconds"]
    add("hub", Geo().lathe([(0, d["z"]), (hub["pin"] * 1.6, d["z"]), (hub["pin"] * 1.6, z), (0, z)], segs=48), "steel_polished", smooth=True)
    add("hub_disc", Geo().lathe([(0, z), (hub["disc"], z), (hub["disc"], z + th), (0, z + th)], segs=96), hs.get("hub_material", "hand_black"),
        bevel=0.03, polished_bevel="steel_polished")
    zt = z + th
    add("hub_pin", Geo().lathe([(0, zt), (hub["pin"], zt), (hub["pin"], zt + 0.12), (hub["pin"] * 0.6, zt + 0.18), (0, zt + 0.18)], segs=48),
        "steel_polished", smooth=True)

    # ---- crown on the 3 o'clock axis: fluted body (lofted along the traced profile when there is one), rounded end ----
    cw, tc = cfg["crown"], tr["crown"]
    m = Matrix(((0, -1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_4x4()  # local z along +x, local y up
    m.translation = (0.0, tc["centre_y_mm"], cw["z"])
    R0, (r1, r2) = tc["radius_mm"], tc["r_from_to_mm"]
    star = [((R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.cos(math.pi * i / cw["teeth"]),
             (R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.sin(math.pi * i / cw["teeth"])) for i in range(cw["teeth"] * 2)]
    cmat = cw.get("material", "steel_polished")
    add("crown_tube", Geo().lathe([(0, r1 - 1.5), (R0 * 0.55, r1 - 1.5), (R0 * 0.55, r1 + 0.2), (0, r1 + 0.2)], segs=48, m=m), cmat, smooth=True)
    prof = tc["profile_mm"][:-1] if "profile_mm" in tc else [[r1, R0], [r2 - cw["end"], R0]]  # traced: its last station is the end
    g = Geo()
    for k, (ax, rad) in enumerate(prof):  # star rings scaled to the profile, flat shaded so each flute catches its own light
        g.v += [Geo._t((x * rad / R0, y * rad / R0, ax), m) for x, y in star]
        if k:
            nst, o = len(star), len(g.v) - 2 * len(star)
            g.f += [(o + i, o + (i + 1) % nst, o + nst + (i + 1) % nst, o + nst + i) for i in range(nst)]
            g.smooth += [False] * nst
    g.f += [tuple(range(len(star) - 1, -1, -1)), tuple(range(len(g.v) - len(star), len(g.v)))]
    g.smooth += [False, False]
    add("crown", g, cmat, bevel=0.08)
    ze, re_ = prof[-1][0], prof[-1][1]
    add("crown_end", Geo().lathe([(0, ze), (re_ - 0.15, ze), (re_ - 0.6, ze + cw["end"] * 0.7), (re_ - 1.2, r2), (0, r2)],
                                 segs=64, m=m), cmat, smooth=True)

    if "bracelet" in cfg:
        br, bt = cfg["bracelet"], tr["bracelet_mm"]
        edges = bt["edges"]  # centre / (middle /) outer column edges (|x| mm)
        gap, pitch = br["gap"], br["pitch"]
        zm, R = ds * (br["z0"] + br["z1"]) / 2, br["bend_radius"]
        j_outer, j_mid = bt["joints_outer"][0], bt["joints_mid"][0]
        bend_y = j_outer
        box = curl(bend_y, R, zm)
        end_y = bend_y + R * br["arc_over_radius"]
        za, zb = ds * br["z0"], ds * br["z1"]
        if len(edges) == 3:  # five columns: polished outer and centre links, brushed middle links half a row nearer the case
            e0, e1, e2 = edges
            cols = {"outer": [(e1 + gap, e2), (-e2, -e1 - gap)], "mid": [(e0 + gap, e1), (-e1, -e0 - gap)], "centre": [(-e0, e0)]}
            phase = {"outer": j_outer, "centre": j_outer, "mid": j_mid}
        else:  # three columns: centre link half a row nearer the case
            e0, e2 = edges
            cols = {"outer": [(e0 + gap, e2), (-e2, -e0 - gap)], "centre": [(-e0, e0)]}
            phase = {"outer": j_outer, "centre": j_mid}
        mats_ = dict({"outer": "steel_polished", "mid": "steel_brushed", "centre": "steel_polished"}, **br.get("materials", {}))
        geos = {k: Geo() for k in cols}
        ends = {k: Geo() for k in cols}
        back = Geo()
        el = cfg["end_link"]
        for sy in (1, -1):
            for kind, xs in cols.items():
                for x0, x1 in xs:  # straight end link from under the case to the first joint
                    ends[kind].prism([(x0, sy * el["from_y"]), (x1, sy * el["from_y"]), (x1, sy * (phase[kind] - gap)), (x0, sy * (phase[kind] - gap))],
                                     0.0, el["top_z"] + (br["centre_raise"] if kind == "centre" else 0.0))
                    y0 = phase[kind]
                    while y0 < end_y - 0.3:
                        y1 = min(y0 + pitch - gap, end_y)
                        box(geos[kind], x0, x1, y0, y1, za, zb + (ds * br["centre_raise"] if kind == "centre" else 0.0), sy)
                        y0 = y1 + gap
            y0 = j_mid
            while y0 < end_y - 0.3:  # dark backing so the joints read as shadow lines
                y1 = min(y0 + pitch, end_y)
                box(back, -e2 + 0.3, e2 - 0.3, y0 - gap, y1, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                y0 = y1
        for kind in cols:
            add("end_links_%s" % kind, ends[kind], mats_[kind], bevel=el["bevel"], polished_bevel="steel_polished" if mats_[kind] == "steel_brushed" else False)
            add("bracelet_%s" % kind, geos[kind], mats_[kind], bevel=br["bevel"], polished_bevel="steel_polished" if mats_[kind] == "steel_brushed" else False)
        add("bracelet_backing", back, "steel_gap")
        hw = e2
        strap_end = end_y
    else:
        # ---- strap: house curl from the lug tips; each side samples the photo's own straight strap (tips aligned) ----
        st = cfg["strap"]
        hw = st["half_width"]
        zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], tip + st["bend_after_tip"]
        box = curl(bend_y, R, zm)
        g = Geo()
        for sy in (1, -1):
            box(g, -hw, hw, st["start_y"], bend_y + R * st["arc_over_radius"], ds * st["z0"], ds * st["z1"], sy)
        rows = maps["strap"]["photo_rows_mm"]
        photo = {sy: (tr["strap_mm"][k]["x"], tr["strap_mm"][k]["tip_y"], rows[i] - 0.3) for i, (sy, k) in enumerate(((1, "top"), (-1, "bottom")))}

        def strap_uv(x, y, z):
            (x0, x1), ptip, end = photo[1 if y > 0 else -1]
            u = min(max((x + hw) / (2 * hw), st["uv_inset"]), 1 - st["uv_inset"])  # side walls take the strap's own edge pixels
            s = abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
            sp = ptip + (s - tip)
            if sp > end:  # past the photo's edge (rolled under, out of the front view): fold back
                sp = 2 * end - sp
            return photo_uv("strap", x0 + u * (x1 - x0), math.copysign(sp, y))
        add("strap", g, "strap", bevel=st["bevel"], uv_of=strap_uv)

        strap_end = bend_y + R * st["arc_over_radius"]

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * rg.get("skirt", rg.get("case", 0)), 3), "lug_width": round(2 * xi, 3), "strap_width": round(2 * hw, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.4, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "strap_end_y_mm": round(strap_end, 2),
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
