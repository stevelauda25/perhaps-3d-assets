"""watch_zeppelin_z96645: build the Zeppelin Mediterranee 1921 Z96645 (steel, cream dial, day-date, brown leather strap)
as a flat-backed front relief.

Params: spec (config/watches/zeppelin-z96645.json). Copied from watch_zeppelin_z96643 (same case, own file): mm,
origin = dial centre, dial faces +z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by
pose.depth_scale, strap built at final depth with the house curl. Own construction: round polished case with a wide polished
bezel (one lathe), stepped lugs (an outer polished part and an inner rail beside the strap, from the traced silhouette), flat
cream dial with a sloped minute ring (photo map: applied numerals, logo, print, day-date window), black hour hand with a
bulb, black lance minute hand, black seconds needle with a black counterweight, stacked black hub, fluted crown with a domed
end at 3. Two photo maps (pipeline/zeppelin_z96645_dial.py): the dial, and the strap leather from the photo's 12 o'clock strap,
used on both sides. Rebuild with --force after regenerating them.
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT


def axis_matrix(angle_deg, z):
    """Local z -> radial direction at a clock angle (dial plane), local origin at height z."""
    a = math.radians(angle_deg)
    m = Matrix(((math.cos(a), -math.sin(a), 0), (0, 0, 1), (math.sin(a), math.cos(a), 0))).transposed().to_4x4()
    m.translation = (0, 0, z)
    return m


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    pm = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Zeppelin Z96645 front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    mats["dial"] = photo_material("dial", ROOT / cfg["dial_map"], cfg["photo_roughness"]["dial"])
    mats["strap_leather"] = photo_material("strap_leather", ROOT / cfg["strap_map"], cfg["photo_roughness"]["strap_leather"])

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location, pose.scale = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"]), (0.001,) * 3
    ds = cfg["pose"].get("depth_scale", 1.0)
    photo_uv = lambda x, y: (0.5 + x / (2 * pm["dial_half_mm"]), 0.5 + y / (2 * pm["dial_half_mm"]))
    s0, s1 = pm["strap_s_from_to_mm"]
    strap_uv = lambda x, s: (0.5 + x / (2 * pm["strap_half_w_mm"]), 1 - min(max((s - s0) / (s1 - s0), 0.0), 1.0))

    def add(name, geo, mat, bevel=None, uv_of=None):
        me = geo.mesh(P + name, True if bevel else None) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if uv_of:  # photo map: uv_of(x, y, z) -> map coordinates
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

    rg, lg_t = tr["rings_mm"], tr["lug"]
    tip = lg_t["tip_mm"]["mean"]
    ol = lg_t["outline_half_mm"]  # (y, half width) along the lug, traced about the case centre
    half = lambda y: next(h0 + (h1 - h0) * (y - y0_) / (y1_ - y0_) for (y0_, h0), (y1_, h1) in zip(ol, ol[1:]) if y <= y1_ + 1e-6)

    # ---- round polished case with the thin sloped bezel, one lathe ----
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile"]], segs=192), "steel_polished")

    # ---- stepped polished lugs: an outer part from the traced silhouette and a lower inner rail beside the strap ----
    lg = cfg["lug"]
    inner, groove = lg_t["inner_x_mm"] + lg["gap"], lg_t["groove_x_mm"]
    y0 = lg_t["from_y_mm"] - lg["into_case"]
    steps = [lg_t["from_y_mm"] + k * 0.25 for k in range(int((tip - lg_t["from_y_mm"]) / 0.25) + 1)]
    outer = [(groove + lg["groove"] / 2, y0), (math.sqrt(c["profile"][2][0] ** 2 - y0 ** 2) - 0.2, y0)]
    outer += [(max(half(y), groove + lg["groove"] / 2 + 0.3), y) for y in steps] + [(groove + lg["groove"] / 2, tip)]
    rail = [(inner, y0), (groove - lg["groove"] / 2, y0), (groove - lg["groove"] / 2, tip - lg["rail_short"]), (inner, tip - lg["rail_short"])]
    for part, poly in (("lugs", outer), ("lug_rails", rail)):
        za, zb = lg[part]
        slope = lambda x, y, za=za, zb=zb: za + (zb - za) * max(abs(y) - lg_t["from_y_mm"], 0) / (tip - lg_t["from_y_mm"])
        g = Geo()
        for sx in (1, -1):
            for sy in (1, -1):
                slab(g, [(sx * x, sy * y) for x, y in poly], 0.0, slope)
        add(part, g, "steel_polished", bevel=lg["bevel"])

    # ---- crystal (alpha glass, no transmission) and the dial with the photo map ----
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (rg["bezel_inner"], cr["z0"]), (rg["bezel_inner"], cr["z1"]), (rg["bezel_inner"] * 0.7, cr["z1"] + cr["dome"] * 0.5),
                                (0, cr["z1"] + cr["dome"])], segs=192), "crystal")
    d = cfg["dial"]
    me = Geo().lathe([(0, d["z"]), (rg["dial_edge"], d["z"]), (rg["bezel_inner"] + 0.05, d["flange_z"]), (rg["bezel_inner"] + 0.05, d["z"] - 0.3)],
                     segs=192).mesh(P + "dial", True)  # flat dial and the sloped minute ring, one photo map
    add("dial", me, "dial", uv_of=lambda x, y, z: photo_uv(x, y))

    # ---- hands at the photo's time (traced, posed outlines) ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute", "seconds"):
        z = hs["z"][name]
        add("hand_" + name, Geo().prism([tuple(p) for p in t[name]["outline_mm"]], z, z + th), "hand_black", bevel=0.03)
    z = hs["z"]["seconds"]
    add("hand_seconds_tail", Geo().prism([tuple(p) for p in t["seconds"]["tail_mm"]], z, z + th), "hand_black", bevel=0.03)
    hub_r, pin_r = tr["hub_radius_mm"]
    zt = hs["z"]["seconds"] + th
    steps_ = hs["hub_steps"]  # stacked rings: (radius fraction, top height above the dial)
    prof = [(0, d["z"])] + [p for k, (f, h) in enumerate(steps_) for p in ((hub_r * f, d["z"] if k == 0 else d["z"] + steps_[k - 1][1]), (hub_r * f, d["z"] + h))]
    prof += [(0, prof[-1][1])]
    add("hub", Geo().lathe([(r, min(z_, zt + 0.15)) for r, z_ in prof], segs=64), "hand_black")

    # ---- crown: conical collar, then a fluted cylinder with a domed end ----
    cw, tc = cfg["crown"], tr["crown"]
    m = axis_matrix(tc["angle_deg"], cw["z"])
    r0, r1, r2 = tc["r_from_to_mm"]
    R0 = tc["radius_mm"]
    add("crown_collar", Geo().lathe([(0, r0 - 0.6), (tc["collar_radius_mm"], r0 - 0.6), (tc["collar_radius_mm"], r0), (R0 * 0.85, r1), (0, r1)], segs=48, m=m),
        "steel_polished")
    cw = dict(cw, teeth=tc.get("teeth", cw["teeth"]))
    star = [((R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.cos(math.pi * i / cw["teeth"]),
             (R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.sin(math.pi * i / cw["teeth"])) for i in range(cw["teeth"] * 2)]
    add("crown", Geo().prism(star, r1, r2 - 0.4, m), "steel_polished", bevel=0.12)
    add("crown_end", Geo().lathe([(0, r2 - 0.4), (R0 - 0.1, r2 - 0.4), (R0 - 0.5, r2), (0, r2)], segs=48, m=m), "steel_polished")

    # ---- leather strap: the photo's 12 o'clock strap (grain, stitching) along its length on both sides, house curl from the lug tips ----
    st = cfg["strap"]
    hw = lg_t["inner_x_mm"] - st["edge_inset"]
    zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], tip + st["bend_after_tip"]
    s_of = lambda y, z: abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
    box = curl(bend_y, R, zm)
    g = Geo()
    start = math.sqrt(c["profile"][2][0] ** 2 - hw ** 2) - st["under_case"]
    for sy in (1, -1):
        box(g, -hw, hw, start, st["end_y"], ds * st["z0"], ds * st["z1"], sy)
    add("strap", g, "strap_leather", bevel=st["bevel"],
        uv_of=lambda x, y, z: strap_uv(x if y > 0 else -x, s_of(y, z)))  # 6 o'clock side: the map turned round, past its end the last row

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(p[0] for p in c["profile"]), 3), "strap_width": round(2 * lg_t["inner_x_mm"], 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.4, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "strap_end_y_mm": st["end_y"],
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
