"""watch_orient_ra_ak0705r10b: build the Orient RA-AK0705R10B (polished steel case, burgundy sunburst dial with day and 24-hour
sub-dials, gold-tone hands and applied numerals, brown croc leather strap) as a flat-backed front relief.

Params: spec (config/watches/orient-ra-ak0705r10b.json). Frame as watch_orient_re_at0007n00b: mm, origin = hand pivot, dial
faces +z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, strap built at final
depth with the house curl. House method: case, bezel, rehaut, lugs and crown in the house polished steel, house glass, modelled
faceted gold hands and gold applied numerals and bars; one photo map (pipeline/orient_ra_ak0705r10b_dial.py, hands removed)
serves only the dial print, the raised ORIENT letters and the leather strap. The case is round about the pivot; the photo's
case centre sits 0.38 mm below the pivot, so the dial UVs move from the pivot (centre) to the photo's rings (rim).
Rebuild with --force after regenerating the photo map.
"""
import json
import math

import bpy

from pipeline.steps.watch_orient_re_at0007n00b import loft
from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rot
from mathutils import Matrix


def ridge(g, st, z, th, ef, deg, c=(0.0, 0.0)):
    """Faceted hand: stations [(r, half width)] along the hand axis (r < 0 toward the tail, half width 0 only at the ends),
    two top facets meeting at a ridge on the axis (height th, edges ef * th), flat bottom at z, turned to deg (clockwise
    from 12) about c."""
    za, ze = z + th, z + th * ef
    Pt = lambda x, y, zz: (*(a + b for a, b in zip(rot(x, y, deg), c)), zz)
    idx = []
    for r, w in st:
        i = len(g.v)
        if w <= 1e-6:
            g.v += [Pt(0, r, ze), Pt(0, r, z)]
            idx.append((i, i, i, i + 1, i + 1))
        else:
            g.v += [Pt(w, r, ze), Pt(0, r, za), Pt(-w, r, ze), Pt(w, r, z), Pt(-w, r, z)]
            idx.append((i, i + 1, i + 2, i + 3, i + 4))

    def face(*q):
        f = []
        for v in q:
            if not f or f[-1] != v:
                f.append(v)
        if len(f) > 1 and f[0] == f[-1]:
            f.pop()
        if len(f) >= 3:
            g.f.append(tuple(f))
            g.smooth.append(False)
    for (L0, A0, R0, Lb0, Rb0), (L1, A1, R1, Lb1, Rb1) in zip(idx, idx[1:]):
        face(L0, L1, A1, A0)
        face(A0, A1, R1, R0)
        face(Lb0, Lb1, L1, L0)
        face(R0, R1, Rb1, Rb0)
        face(Lb0, Rb0, Rb1, Lb1)
    face(*(idx[0][k] for k in (0, 1, 2, 4, 3)))
    face(*(idx[-1][k] for k in (3, 4, 2, 1, 0)))
    return g


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    pm = json.loads((ROOT / cfg["photo_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Orient RA-AK0705R10B front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    for key, rough in cfg["photo_roughness"].items():  # one image, two surfaces: dial (and the raised letters) and strap
        mats[key] = photo_material(key, ROOT / cfg["photo_map"], rough)

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location, pose.scale = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"]), (0.001,) * 3
    ds = cfg["pose"]["depth_scale"]
    S, (px0, py0) = tr["scale_px_per_mm"], tr["origin_px"]
    k_map, (mw, mh), (cx0, cy0) = pm["scale"], pm["size_px"], pm["crop_px"]
    photo_uv = lambda x, y: ((px0 + x * S - cx0) * k_map / mw, 1 - (py0 - y * S - cy0) * k_map / mh)

    def add(name, geo, mat, bevel=None, uv_of=None, smooth=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in cfg["photo_roughness"]:
            f = uv_of or (lambda x, y, z: photo_uv(x, y))
            uv = me.uv_layers.new(name="UVMap")
            for loop in me.loops:
                uv.data[loop.index].uv = f(*me.vertices[loop.vertex_index].co)
        if bevel:
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if not name.startswith("strap"):
            o.scale = (1, 1, ds)
        return o

    # ---- round case about the pivot; dial UVs: pivot -> photo pivot, rim -> the photo's rings about its case centre ----
    (ex, ey), R_open, R_case, R_dial = tr["case_centre_mm"], tr["crystal_open_mm"], cfg["case"]["radius"], tr["dial_edge_mm"]
    angs = [math.radians(cfg["case"]["step_deg"] * i) for i in range(int(round(360 / cfg["case"]["step_deg"])))]
    ring = lambda r, z: [(r * math.sin(a), r * math.cos(a), z) for a in angs]

    def dial_uv(x, y, z):
        f = min(1.0, math.hypot(x, y) / R_open)
        return photo_uv(x + ex * f, y + ey * f)

    c = cfg["case"]
    add("case", loft([ring((R_case if k == "case" else R_open) + v, z) for k, v, z in c["rings"]]), "steel_polished")

    # ---- lugs: one outline (mean of the four photo lugs) mirrored to all four, top sloping to the tip ----
    lg, lm = cfg["lug"], tr["lug_mean"]
    tip, xi = lm["tip_y"], lm["inner_x"]
    outer = [(xi + off, tip - d) for d, off in lm["outer_offset_by_depth"]]
    poly = [(xi, tip)] + outer + [(outer[-1][0] - lg["into_case"], outer[-1][1] - lg["into_case"]), (xi, outer[-1][1] - lg["into_case"])]
    top = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * min(1.0, max(0.0, (abs(y) - lg["slope_from_y"]) / (tip - lg["slope_from_y"])))
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in poly], 0.0, top)
    add("lugs", g, "steel_polished", bevel=lg["bevel"])

    # ---- rehaut, dial, crystal ----
    rh, d, cr = cfg["rehaut"], cfg["dial"], cfg["crystal"]
    add("rehaut", loft([ring(R_dial - 0.05, rh["z0"] - 0.4), ring(R_dial - 0.05, rh["z0"]), ring(R_open - 0.3, rh["z1"])]), "steel_polished")  # cap below the dial
    add("dial", loft([ring(R_dial, d["z"] - 0.3), ring(R_dial, d["z"])], top_cap=True), "dial", uv_of=dial_uv)
    dome = [ring(R_open, cr["z0"]), ring(R_open, cr["z1"])]
    dome += [ring(R_open * f, cr["z1"] + cr["dome"] * (1 - f * f)) for f in (0.92, 0.8, 0.65, 0.48, 0.3, 0.12)]
    add("crystal", loft(dome, top_cap=True), "crystal")

    # ---- applied: gold Roman numerals and bars, raised ORIENT letters with the photo on them ----
    ap = cfg["applied"]
    add("numerals", plate(tr["numerals"], d["z"], d["z"] + ap["height"], P + "numerals"), "gold_polished", bevel=ap["bevel"])
    add("logo", plate(tr["logo"], d["z"], d["z"] + ap["logo_height"], P + "logo"), "dial", uv_of=dial_uv)

    # ---- hands at the photo's time: faceted gold, ridge on the axis ----
    hs, th, ef = cfg["hands"], cfg["hands"]["thickness"], cfg["hands"]["edge_fraction"]
    for name in ("hour", "minute", "seconds"):
        h = tr["hands"][name]
        tail = [(-r, w) for r, w in h["tail_mm"]]
        if h["tail_round_mm"]:  # counterweight: half circle about the last tail station
            rr, rc = h["tail_round_mm"], tail[-1][0]
            tail = tail[:-1] + [(rc - rr * math.sin(a), rr * math.cos(a)) for a in [i * math.pi / 16 for i in range(9)]]
        st = sorted(tail + [tuple(s) for s in h["stations_mm"]] + [(h["length_mm"], 0.0)])
        add("hand_" + name, ridge(Geo(), st, hs["z"][name], th, ef, h["angle_deg"]), "gold_polished", bevel=0.02)
    for name in ("sub_day", "sub_h24"):
        h, z = tr["hands"][name], hs["z"][name]
        hub, hr, hw, L = h["hub_mm"], h["head_r_mm"], h["half_mm"], h["length_mm"]
        g = ridge(Geo(), [(hr * 0.5, hw), (hr * 0.9, hw * 0.95), (L * 0.75, hw * 0.55), (L, 0.0)], z, th, ef, h["angle_deg"], hub)
        m = Matrix.Translation((hub[0], hub[1], 0.0))
        g.lathe([(0, z), (hr, z), (hr, z + th * 0.8), (0, z + th * 0.8)], segs=48, m=m)
        g.lathe([(0, z), (0.2, z), (0.2, z + th + 0.12), (0, z + th + 0.16)], segs=24, m=m)
        add("hand_" + name, g, "gold_polished", bevel=0.02)
    zt, hub_r = hs["z"]["seconds"] + th, cfg["hands"]["hub_radius"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, zt + 0.06), (hub_r * 0.6, zt + hs["hub_height"]), (0, zt + hs["hub_height"])], segs=48),
        "gold_polished", smooth=True)

    # ---- crown on the 3 o'clock axis: neck, fluted body, rounded end ----
    cw = cfg["crown"]
    m = Matrix(((0, -1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_4x4()  # local z along +x, local y up
    m.translation = (0.0, 0.0, cw["z"])
    R0, r1 = cw["radius"], R_case + cw["gap"]
    r2 = r1 + cw["length"]
    add("crown_neck", Geo().lathe([(0, R_case - 1.0), (R0 * cw["neck_fraction"], R_case - 1.0), (R0 * cw["neck_fraction"], r1 + 0.1), (0, r1 + 0.1)], segs=48, m=m),
        "steel_polished", smooth=True)
    star = [((R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.cos(math.pi * i / cw["teeth"]),
             (R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.sin(math.pi * i / cw["teeth"])) for i in range(cw["teeth"] * 2)]
    add("crown", Geo().prism(star, r1, r2 - 0.5, m), "steel_polished", bevel=0.08)
    add("crown_end", Geo().lathe([(0, r2 - 0.5), (R0 - 0.15, r2 - 0.5), (R0 - 0.8, r2), (0, r2)], segs=48, m=m), "steel_polished", smooth=True)

    # ---- leather strap: straight, house curl from the lug tips; UVs from the photo's straight strap (case edge to past the
    #      tip, folded back and forth so the curled part keeps the leather grain without a seam) ----
    st = cfg["strap"]
    hw = xi - st["edge_inset"]
    zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], tip + st["bend_after_tip"]
    box = curl(bend_y, R, zm)
    g = Geo()
    for sy in (1, -1):
        box(g, -hw, hw, st["start_y"], bend_y + R * st["arc_over_radius"], ds * st["z0"], ds * st["z1"], sy)
    ends = pm["strap_end_mm"]
    photo = {sy: (tr["strap_mm"][k]["x"], tr["strap_mm"][k]["tip_y"], tr["strap_mm"][k]["case_y"], ends[k]) for sy, k in ((1, "top"), (-1, "bottom"))}

    def strap_uv(x, y, z):
        (x0, x1), ptip, pedge, end = photo[1 if y > 0 else -1]
        u = min(max((x + hw) / (2 * hw), st["uv_inset"]), 1 - st["uv_inset"])
        s = abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
        lo, hi = pedge, min(ptip + st["photo_past_tip"], end)
        k, w = divmod(ptip + (s - tip) - lo, hi - lo)
        sp = lo + w if int(k) % 2 == 0 else hi - w
        return photo_uv(x0 + u * (x1 - x0), math.copysign(sp, y))
    add("strap", g, "strap_leather", bevel=st["bevel"], uv_of=strap_uv)

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * R_case, 3), "strap_width": round(2 * hw + 2 * st["edge_inset"], 3),
           "photo_case_diameter": round(2 * tr["case_radius_mm"], 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.4, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "crystal_mm": round(2 * R_open, 3),
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
