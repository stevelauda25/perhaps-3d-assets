"""watch_fossil_fs4812: build the Fossil Grant chronograph FS4812 (steel, black dial with Roman numerals, three sub-dials,
black leather strap) as a flat-backed front relief.

Params: spec (config/watches/fossil-fs4812.json). Same frame as watch_zeppelin_z96903: mm, origin = hand pivot, dial faces
+z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, strap built at final depth
with the house curl. Own construction: round case with a wide polished sloped bezel (one lathe), plain polished lugs from
the traced left-flank silhouette, the crown-side lobe between the pushers from the right silhouette, two round chrono pushers
at 2 and 4, knurled crown at 3, flat dial plus the minute-track flange as a cone with the photo map, polished sword hour and
minute hands with white lume inserts, polished chrono seconds needle with a tail, three polished sub-dial needles.
One photo map (pipeline/fossil_fs4812_dial.py) serves the dial and the strap. Rebuild with --force after regenerating it.
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT
from pipeline.steps.watch_zeppelin_z70363 import axis_matrix


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    pm = json.loads((ROOT / cfg["photo_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Fossil FS4812 front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    for key, rough in cfg["photo_roughness"].items():  # one image, two surfaces
        mats[key] = photo_material(key, ROOT / cfg["photo_map"], rough)

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location, pose.scale = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"]), (0.001,) * 3
    ds = cfg["pose"].get("depth_scale", 1.0)
    photo_uv = lambda x, y: (0.5 + x / (2 * pm["half_w_mm"]), 0.5 + (y - pm["centre_y_mm"]) / (2 * pm["half_h_mm"]))

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
    tip, y_from = lg_t["tip_mm"]["mean"], lg_t["from_y_mm"]
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}
    tips = lg_t["tip_mm"]
    q = lambda v: round(round(v * 4) / 4, 2)  # silhouette rows are 0.25 mm apart
    # lug rows from the left flank (the right carries the pushers), top and bottom lug each stretched to the mean tip
    half = lambda y: sum(sil[k][1] for k in (q(y_from + (y - y_from) * (tips["top"] - y_from) / (tip - y_from)),
                                             -q(y_from + (y - y_from) * (tips["bottom"] - y_from) / (tip - y_from)))) / 2

    # ---- round case with the wide polished sloped bezel, one lathe ----
    c = cfg["case"]
    R_case = c["profile"][2][0]
    add("case", Geo().lathe([tuple(p) for p in c["profile"]], segs=192), "steel_polished")

    # ---- plain polished lugs: outline from the traced silhouette, sloped top ----
    lg = cfg["lug"]
    inner = lg_t["inner_x_mm"] + lg["gap"]
    y0 = y_from - lg["into_case"]
    steps = [y_from + k * 0.25 for k in range(int((tip - y_from) / 0.25) + 1)]
    edge = [max(half(y), inner + 0.3) for y in steps]
    edge = [min(edge[:k + 1]) for k in range(len(edge))]  # the lugs only narrow toward the tip: drop strap noise
    edge = [sum(edge[max(k - 2, 0):k + 3]) / len(edge[max(k - 2, 0):k + 3]) for k in range(len(edge))]
    outline = [(inner, y0), (math.sqrt(R_case ** 2 - y0 ** 2) - 0.2, y0)] + list(zip(edge, steps)) + [(inner, tip)]
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * max(abs(y) - y_from, 0) / (tip - y_from)
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "steel_polished", bevel=lg["bevel"])

    # ---- crown-side lobe between the pushers: right silhouette outside, case flank inside ----
    lb = cfg["lobe"]
    pts = tr["lobe_right_mm"]  # (y, x), y from +12 side down
    outer = [(max(x, math.sqrt(max(R_case ** 2 - y * y, 0)) + 0.05), y) for y, x in pts]
    inner_side = [(math.sqrt(R_case ** 2 - y * y) - lb["into_case"], y) for y, _ in reversed(pts)]
    add("lobe", slab(Geo(), outer + inner_side, 0.0, lambda x, y: lb["top_z"]), "steel_polished", bevel=lb["bevel"])

    # ---- crystal (alpha glass, no transmission); flat dial and the minute-track flange cone with the photo map ----
    cr = cfg["crystal"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (rg["bezel_inner"], cr["z0"]), (rg["bezel_inner"], cr["z1"]), (rg["bezel_inner"] * 0.7, cr["z1"] + cr["dome"] * 0.5),
                                (0, cr["z1"] + cr["dome"])], segs=192), "crystal")
    d = cfg["dial"]
    fr, fz = d["flange_top"]
    me = Geo().lathe([(0, d["z"]), (rg["flange_inner"], d["z"]), (fr, fz), (fr, d["z"] - 0.3)], segs=192).mesh(P + "dial", True)
    add("dial", me, "dial", uv_of=lambda x, y, z: photo_uv(x, y))

    # ---- hands at the photo's time: polished frames, white lume inserts on hour and minute ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute", "seconds"):
        z = hs["z"][name]
        add("hand_" + name, Geo().prism([tuple(p) for p in t[name]["outline_mm"]], z, z + th), "steel_polished", bevel=0.03)
        if "lume_mm" in t[name]:
            add("lume_" + name, Geo().prism([tuple(p) for p in t[name]["lume_mm"]], z + th - 0.02, z + th + hs["lume_raise"]), "lume")
    z = hs["z"]["seconds"]
    add("hand_seconds_tail", Geo().prism([tuple(p) for p in t["seconds"]["tail_mm"]], z, z + th), "steel_polished", bevel=0.03)
    hub_r, pin_r = tr["hub_mm"]["radius"], tr["hub_mm"]["pin"]
    zt = hs["z"]["seconds"] + th
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, zt + 0.1), (hub_r * 0.8, zt + 0.15), (0, zt + 0.15)], segs=64), "steel_polished")
    add("hub_pin", Geo().lathe([(0, zt), (pin_r, zt), (pin_r, zt + 0.3), (0, zt + 0.35)], segs=32), "steel_polished")

    # ---- sub-dial needles on polished hubs ----
    sr, sp, zs = tr["sub_hub_mm"]["radius"], tr["sub_hub_mm"]["pin"], hs["z"]["sub"]
    for k, sd in tr["subdials"].items():
        add("sub_hand_" + k, Geo().prism([tuple(p) for p in sd["hand_mm"]], zs, zs + th), "steel_polished", bevel=0.02)
        m = Matrix.Translation((*sd["centre_mm"], 0))
        add("sub_hub_" + k, Geo().lathe([(0, d["z"]), (sr, d["z"]), (sr, zs + th + 0.1), (0, zs + th + 0.1)], segs=48, m=m), "steel_polished")
        add("sub_pin_" + k, Geo().lathe([(0, zs + th + 0.1), (sp, zs + th + 0.1), (sp, zs + th + 0.25), (0, zs + th + 0.28)], segs=24, m=m), "steel_polished")

    # ---- knurled crown at 3: neck and knurled body with a flat end ----
    cw, tc = cfg["crown"], tr["crown"]
    m = axis_matrix(tc["angle_deg"], cw["z"])
    r0, r1, r2 = tc["r_from_to_mm"]
    R0 = tc["radius_mm"]
    add("crown_neck", Geo().lathe([(0, r0 - 0.8), (tc["neck_radius_mm"], r0 - 0.8), (tc["neck_radius_mm"], r1), (0, r1)], segs=48, m=m), "steel_polished")
    star = [((R0 if i % 2 == 0 else R0 - cw["knurl_depth"]) * math.cos(math.pi * i / cw["teeth"]),
             (R0 if i % 2 == 0 else R0 - cw["knurl_depth"]) * math.sin(math.pi * i / cw["teeth"])) for i in range(cw["teeth"] * 2)]
    add("crown", Geo().prism(star, r1, r2, m), "steel_polished", bevel=0.08)

    # ---- chrono pushers at 2 and 4: stem and a round cap with a chamfered end ----
    pu = tr["pushers"]
    pa, pb = pu["r_from_to_mm"]
    for k, ang in enumerate(pu["angles_deg"]):
        m = axis_matrix(ang, cfg["pushers"]["z"])
        add("pusher_stem_%d" % k, Geo().lathe([(0, R_case - 0.8), (pu["stem_radius_mm"], R_case - 0.8), (pu["stem_radius_mm"], pa), (0, pa)], segs=32, m=m), "steel_polished")
        Rp = pu["radius_mm"]
        add("pusher_%d" % k, Geo().lathe([(0, pa), (Rp, pa), (Rp, pb - 0.25), (Rp - 0.25, pb), (0, pb)], segs=48, m=m), "steel_polished")

    # ---- leather strap: the photo's own strap (grain, stitching) along its length, house curl from the lug tips ----
    st = cfg["strap"]
    hw = lg_t["inner_x_mm"] - st["edge_inset"]
    zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], tip + st["bend_after_tip"]
    s_of = lambda y, z: abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
    ends = pm["strap_end_mm"]  # last straightened strap row; the rolled-under strap past it reuses that row
    box = curl(bend_y, R, zm)
    g = Geo()
    start = math.sqrt(R_case ** 2 - hw ** 2) - st["under_case"]
    for sy in (1, -1):
        box(g, -hw, hw, start, st["end_y"], ds * st["z0"], ds * st["z1"], sy)
    add("strap", g, "strap_leather", bevel=st["bevel"],
        uv_of=lambda x, y, z: photo_uv(x, math.copysign(min(s_of(y, z), ends["top" if y > 0 else "bottom"]), y)))

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * max(p[0] for p in c["profile"]), 3), "strap_width": round(2 * lg_t["inner_x_mm"], 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.4, "%s %.3f != %.3f" % (key, out[key], want)
    assert abs(st["end_y"] - (bend_y + 2.2 * R)) < 0.2, "strap end_y should be tip + 2.2 x radius"
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "strap_end_y_mm": st["end_y"],
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
