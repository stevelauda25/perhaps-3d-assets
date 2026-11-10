"""watch_orient_ra_ac0f06l10b: build the Orient RA-AC0F06L10B (polished round case with a wide sloped bezel, blue sunburst dial,
faceted batons, blue croc leather strap) as a flat-backed front relief.

Params: spec (config/watches/orient-ra-ac0f06l10b.json). Same frame, pose, 2.5D depth scale, materials and strap curl as
watch_orient_re_at0007n00b and watch_orient_re_au0107e, whose methods it follows. Parts from the photo: one lathe for the
polished case and its wide sloped bezel, four polished lugs (outline by depth from the tip, top and bottom averaged), applied
faceted tapered batons (the 12 a pair of them), a polished date frame, faceted dauphine-like hour and minute hands, a thin
seconds needle with a short wide tail, a fluted crown and a 22 mm strap with the house curl. Photo maps: the dial (hands
removed) and the strap leather resampled row by row (pipeline/orient_ra_ac0f06l10b_dial.py). Rebuild with --force after
regenerating the maps (they are not part of the stage fingerprint).
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rot


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    dm = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    sm = json.loads((ROOT / cfg["strap_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Orient RA-AC0F06L10B front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    d, st = cfg["dial"], cfg["strap"]
    mats["dial"] = photo_material("dial_photo", ROOT / cfg["dial_map"], d["roughness"])
    mats["strap_leather"] = photo_material("strap_photo", ROOT / cfg["strap_map"], st["roughness"])

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location, pose.scale = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"]), (0.001,) * 3
    ds = cfg["pose"]["depth_scale"]

    def add(name, geo, mat, bevel=None, smooth=None, uv_of=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if uv_of:
            uv = me.uv_layers.new(name="UVMap")
            for loop in me.loops:
                uv.data[loop.index].uv = uv_of(*me.vertices[loop.vertex_index].co)
        if bevel:
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if not name.startswith("strap"):
            o.scale = (1, 1, ds)
        return o

    # ---- polished case with the wide sloped bezel, dark line at the crystal edge, crystal ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]], segs=192), "steel_polished", smooth=True)
    gk = cfg["gasket"]
    add("gasket", Geo().lathe([(gk["r_in"], gk["z0"]), (gk["r_out"], gk["z0"]), (gk["r_out"], gk["z1"]), (gk["r_in"], gk["z1"])], segs=192), "gasket_black")
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (cr["radius"], cr["z0"]), (cr["radius"], cr["z1"]), (0, cr["z1"])], segs=192), "crystal")

    # ---- dial + grey inner slope (rehaut) to the crystal ring, photo map on a planar UV about the index ring centre ----
    H = dm["half_size_mm"]
    me = Geo().lathe([(0, d["z"]), (tr["rehaut_mm"], d["z"]), (d["rehaut_r"], d["rehaut_z"])], segs=192).mesh(P + "dial", True)
    if me.polygons[0].normal.z < 0:
        for poly in me.polygons:
            poly.flip()
        me.update()
    add("dial", me, "dial", uv_of=lambda x, y, z: (0.5 + x / (2 * H), 0.5 + y / (2 * H)))

    # ---- applied faceted tapered batons (ridge on the centre line); the 12 is a pair; the 3 shortened by the date ----
    ix, ti = cfg["indices"], tr["indices"]
    z0, top = d["z"], d["z"] + ix["height"]
    g = Geo()

    def baton(r0, r1, h0, h1, deg):
        for sx in (1, -1):
            pts = [(0.0, r0), (sx * h0, r0), (sx * h1, r1), (0.0, r1)]
            ridge = {rot(x, y, deg) for x, y in pts if x == 0.0}
            slab(g, [rot(x, y, deg) for x, y in pts], z0, lambda x, y, ridge=ridge: top + ix["ridge"] * ((x, y) in ridge))

    b = ti["baton_mm"]
    for hour in range(1, 12):
        r0 = ti["index_3_inner_mm"] if hour == 3 else b["inner"]
        h0 = b["half_inner"] + (b["half_outer"] - b["half_inner"]) * (r0 - b["inner"]) / (b["outer"] - b["inner"])
        baton(r0, b["outer"], h0, b["half_outer"], hour * 30)
    q = ti["index_12_mm"]
    for sx in (1, -1):  # two batons side by side, each half the trapezoid, ridges on their centre lines
        xc0, xc1 = sx * q["half_inner"] / 2, sx * q["half_outer"] / 2
        hw0, hw1 = q["half_inner"] / 2, q["half_outer"] / 2
        for side in (1, -1):
            pts = [(xc0, q["inner"]), (xc0 + side * hw0, q["inner"]), (xc1 + side * hw1, q["outer"]), (xc1, q["outer"])]
            ridge = {pts[0], pts[3]}
            slab(g, pts, z0, lambda x, y, ridge=ridge: top + ix["ridge"] * ((x, y) in ridge))
    add("indices", g, "steel_polished", bevel=0.03)

    # ---- polished date frame (the window and its numeral stay in the dial map) ----
    dw = tr["date_window"]
    x0, y0, x1, y1 = dw["x0_y0_x1_y1_mm"]
    k = dw["frame_mm"]
    outer = [(x0, y1), (x1, y1), (x1, y0), (x0, y0)]
    inner = [(x0 + k, y1 + k), (x1 - k, y1 + k), (x1 - k, y0 - k), (x0 + k, y0 - k)]
    g = Geo()
    for i in range(4):
        j = (i + 1) % 4
        g.prism([outer[i], outer[j], inner[j], inner[i]], d["z"], d["z"] + ix["date_frame_height"])
    add("date_frame", g, "steel_polished", bevel=0.04)

    # ---- hands at the photo's time: faceted (ridge on the axis), seconds needle with a short wide tail ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute"):
        h, z = t[name], hs["z"][name]
        prof = h["outline_mm"]
        g = Geo()
        for sx in (1, -1):
            half = [(0.0, prof[0][0])] + [(sx * w, r) for r, w in prof if w > 0] + [(0.0, prof[-1][0])]
            deg = h["angle_deg"]
            ridge = {rot(0.0, prof[0][0], deg), rot(0.0, prof[-1][0], deg)}
            slab(g, [rot(x, y, deg) for x, y in half], z, lambda x, y, z=z, ridge=ridge: z + th + hs["ridge"] * ((x, y) in ridge))
        add("hand_" + name, g, "steel_polished", bevel=0.02)
    h = t["seconds"]
    L, tail, deg, z = h["length_mm"], h["tail_mm"], h["angle_deg"], hs["z"]["seconds"]
    nw, cw = h["half_width_mm"], h["tail_half_width_mm"]
    add("hand_seconds", Geo().prism([rot(x, y, deg) for x, y in [(nw, 0), (nw, L - 0.3), (0, L), (-nw, L - 0.3), (-nw, 0)]], z, z + th),
        "steel_polished", bevel=0.02)
    add("hand_seconds_tail", Geo().prism([rot(x, y, deg) for x, y in [(cw, -tail), (cw, 0.5), (-cw, 0.5), (-cw, -tail)]], z, z + th),
        "steel_polished", bevel=0.03)
    collar_r, cap_r = tr["hub_radius_mm"]
    zh = hs["z"]["hour"]
    add("hub", Geo().lathe([(0, d["z"]), (collar_r, d["z"]), (collar_r, zh + th), (0, zh + th)], segs=64), "steel_polished")
    zc = z + th
    add("hub_cap", Geo().lathe([(0, zh), (cap_r, zh), (cap_r, zc + 0.1), (cap_r * 0.6, zc + 0.18), (0, zc + 0.18)], segs=48), "steel_polished")

    # ---- crown on the 3 o'clock axis: fluted body, smooth end cap ----
    cw_ = cfg["crown"]
    R0, teeth = tr["crown"]["radius_mm"], tr["crown"]["teeth"]
    star = [((R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.cos(math.pi * i / teeth),
             (R0 if i % 2 == 0 else R0 - cw_["flute_depth"]) * math.sin(math.pi * i / teeth)) for i in range(teeth * 2)]
    m = Matrix(((0, -1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_4x4()  # local z along +x, local y up
    m.translation = (0.0, 0.0, cw_["z"])
    r1, r2 = cw_["r_from"], tr["crown"]["to_mm"] - cw_["cap"]
    add("crown_neck", Geo().lathe([(0, c["profile_rz"][2][0] - 1.0), (R0 * 0.6, c["profile_rz"][2][0] - 1.0), (R0 * 0.6, r1 + 0.1), (0, r1 + 0.1)], segs=48, m=m),
        "steel_polished", smooth=True)
    add("crown", Geo().prism(star, r1, r2, m), "steel_polished", bevel=0.1)
    add("crown_cap", Geo().lathe([(0, r2), (R0 * 0.9, r2), (R0 * 0.9, r2 + cw_["cap"]), (0, r2 + cw_["cap"])], segs=48, m=m), "steel_polished", bevel=0.08)

    # ---- lugs: outline by depth from the tip (top and bottom averaged), mirrored to all four, top sloping to the tip ----
    lg, tl = cfg["lug"], tr["lug"]
    tip, xi = tl["tip_mm"], tl["inner_x_mm"]
    R_case = c["profile_rz"][2][0]
    outer = [(w, tip - dd) for dd, w in tl["half_width_by_depth_mm"] if math.hypot(w, tip - dd) > R_case - lg["into_case"]]  # until it runs into the case
    outer = [(lg["tip_outer_x"], tip)] + outer
    last = outer[-1]
    poly = [(xi, tip)] + outer + [(xi, last[1])]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * min(1.0, max(0.0, (abs(y) - lg["slope_from_y"]) / (tip - lg["slope_from_y"])))
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in poly], 0.0, slope)
    add("lugs", g, "steel_polished", bevel=lg["bevel"])

    # ---- leather strap: straight between the lugs, house curl from the tips; both sides sample the photo's bottom strap
    #      (the longer one), lug tips aligned, folded back and forth over its flat leather ----
    hw = xi - st["edge_inset"]
    zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], tip + st["bend_after_tip"]
    box = curl(bend_y, R, zm)
    g = Geo()
    for sy in (1, -1):
        box(g, -hw, hw, st["start_y"], bend_y + R * st["arc_over_radius"], ds * st["z0"], ds * st["z1"], sy)
    rows, Sp = sm["rows_px"]["bottom"], sm["scale_px_per_mm"]
    tip_px, n_rows = sm["lug_tips_px"][1], sm["size_px"][1]
    lo, hi = tip + (rows[0] - tip_px) / Sp, tip + (rows[-1] - tip_px) / Sp  # flat leather in the photo, model s

    def strap_uv(x, y, z):
        u = min(max((x + hw) / (2 * hw), st["uv_inset"]), 1 - st["uv_inset"])  # side walls take the strap's own edge pixels
        s = abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
        s = max(s, lo)
        k_, w = divmod(s - lo, hi - lo)
        sp = lo + w if int(k_) % 2 == 0 else hi - w
        row = (sp - lo) / (hi - lo) * (len(rows) - 1)
        return 0.5 + 0.5 * u, 1 - (row + 0.5) / n_rows
    add("strap", g, "strap_leather", bevel=st["bevel"], uv_of=strap_uv)

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(r for r, _ in c["profile_rz"]), 3), "lug_to_lug": round(2 * tip, 3),
           "strap_width": round(2 * hw, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.35, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
