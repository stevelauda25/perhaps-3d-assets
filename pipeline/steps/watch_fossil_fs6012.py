"""watch_fossil_fs6012: build the Fossil Carraway FS6012 (rectangular steel case, cream sunray dial with Roman numerals, black
hands with lume, brown leather strap) as a flat-backed front relief.

Params: spec (config/watches/fossil-fs6012.json). Same frame as watch_zeppelin_z96903: mm, origin = hand pivot, dial faces +z,
back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, strap built at final depth with
the house curl. Own construction, all plan sizes from the trace: lower outer flank on each side (silhouette edge to the step),
raised brushed brancards that run up into the horns (outer edge = silhouette, inner edge = the dial frame), one polished
bezel slab between the brancards (top bar, bottom bar and the frame) with the dial opening as a hole, dark core under the dial,
flat dial with the photo map, flat alpha crystal, black lozenge hour and minute hands with raised lume inserts, black
seconds needle with a long counterweight tail, black hub with a steel pin, fluted crown at 3 with a rounded end.
One photo map (pipeline/fossil_fs6012_dial.py) serves the dial and the strap. Rebuild with --force after regenerating it.
"""
import json
import math

import bpy

from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT, rect
from pipeline.steps.watch_zeppelin_z70363 import axis_matrix


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    pm = json.loads((ROOT / cfg["photo_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Fossil FS6012 front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    for key, rough in cfg["photo_roughness"].items():  # one image, two surfaces
        mats[key] = photo_material(key, ROOT / cfg["photo_map"], rough)

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location, pose.scale = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"]), (0.001,) * 3
    ds = cfg["pose"].get("depth_scale", 1.0)
    photo_uv = lambda x, y: (0.5 + x / (2 * pm["half_w_mm"]), 0.5 + (y - pm["centre_y_mm"]) / (2 * pm["half_h_mm"]))

    def add(name, geo, mat, bevel=None, uv_of=None, segments=2):
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
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, segments, "ANGLE", math.radians(35)
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if not name.startswith("strap"):
            o.scale = (1, 1, ds)
        return o

    tc, c = tr["case"], cfg["case"]
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}
    edge = lambda y, k: sil[round(round(y * 4) / 4, 2)][k]  # k = 1 left, 2 right (silhouette rows are 0.25 mm apart)
    inner, step = tc["brancard_inner_x_mm"], tc["step_x_mm"]
    tips, fl = tc["horn_tip_mm"], tc["flank_end_mm"]
    rows = lambda up, down: [-down + 0.25 * k for k in range(round((up + down) / 0.25) + 1)]  # y from `down` below the pivot to `up` above

    # ---- lower outer flank (silhouette edge to the step) and the raised brushed brancards running into the horns ----
    for side, k, sx in (("left", 1, -1), ("right", 2, 1)):
        ys = rows(fl["top"], fl["bottom"])
        g = Geo()
        slab(g, [(sx * max(edge(y, k), step - 0.3), y) for y in ys] + [(sx * (step - 0.3), y) for y in reversed(ys)], 0.0, lambda x, y: c["flank_z"])
        add("flank_" + side, g, "steel_polished", bevel=c["flank_bevel"])
        ys = rows(tips["top"], tips["bottom"])
        g = Geo()
        slab(g, [(sx * min(max(edge(y, k), inner + 0.3), step), y) for y in ys] + [(sx * inner, y) for y in reversed(ys)], 0.0, lambda x, y: c["brancard_z"])
        add("brancard_" + side, g, "steel_brushed", bevel=c["brancard_bevel"], segments=3)

    # ---- polished bezel slab between the brancards: top bar, frame and bottom bar, the dial opening as a hole ----
    ov = c["overlap"]
    top, bot = tc["bar_top_y_mm"][0], tc["bar_bottom_y_mm"][1]
    dx0, dy0, dx1, dy1 = tc["dial_rect_mm"]  # x0 < x1, y0 above y1
    outer = rect(0, (top + bot) / 2, 2 * (inner + ov), top - bot)
    hole = rect((dx0 + dx1) / 2, (dy0 + dy1) / 2, dx1 - dx0, dy0 - dy1)
    add("bezel", plate([{"outer": outer, "holes": [hole[::-1]]}], 0.0, c["bar_z"], P + "bezel"), "steel_polished", bevel=c["bar_bevel"], segments=3)
    d, cr = cfg["dial"], cfg["crystal"]
    add("core", Geo().prism(rect((dx0 + dx1) / 2, (dy0 + dy1) / 2, dx1 - dx0 + 1.0, dy0 - dy1 + 1.0), 0.0, d["z"] - 0.05), "case_dark")
    grow = d["under_frame"]  # dial and crystal run a little under the frame so no gap shows at the walls
    me = Geo().prism(rect((dx0 + dx1) / 2, (dy0 + dy1) / 2, dx1 - dx0 + 2 * grow, dy0 - dy1 + 2 * grow), d["z"] - 0.05, d["z"]).mesh(P + "dial", False)
    add("dial", me, "dial", uv_of=lambda x, y, z: photo_uv(x, y))
    add("crystal", Geo().prism(rect((dx0 + dx1) / 2, (dy0 + dy1) / 2, dx1 - dx0 + 2 * grow, dy0 - dy1 + 2 * grow), cr["z0"], cr["z1"]), "crystal")

    # ---- hands at the photo's time (traced, posed outlines): black, raised lume inserts, black hub with a steel pin ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute", "seconds"):
        z = hs["z"][name]
        add("hand_" + name, Geo().prism([tuple(p) for p in t[name]["outline_mm"]], z, z + th), "hand_black", bevel=0.03)
        if "lume_mm" in t[name]:
            add("lume_" + name, Geo().prism([tuple(p) for p in t[name]["lume_mm"]], z + th - 0.02, z + th + hs["lume_raise"]), "lume")
    z = hs["z"]["seconds"]
    add("hand_seconds_tail", Geo().prism([tuple(p) for p in t["seconds"]["tail_mm"]], z, z + th), "hand_black", bevel=0.03)
    hub_r, pin_r = tr["hub_mm"]["radius"], tr["hub_mm"]["pin"]
    zt = hs["z"]["seconds"] + th
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, hs["z"]["minute"] + th), (hub_r * 0.75, zt + 0.1), (0, zt + 0.1)], segs=64), "hand_black")
    add("hub_pin", Geo().lathe([(0, zt + 0.1), (pin_r, zt + 0.1), (pin_r, zt + 0.25), (0, zt + 0.3)], segs=32), "steel_polished")

    # ---- crown: neck, fluted body, rounded end ----
    cw, tk = cfg["crown"], tr["crown"]
    m = axis_matrix(tk["angle_deg"], cw["z"])
    r0, r1, r2, r3 = tk["r_from_to_mm"]
    R0, Re = tk["radius_mm"], tk["end_radius_mm"]
    add("crown_neck", Geo().lathe([(0, r0 - 0.8), (tk["neck_radius_mm"], r0 - 0.8), (tk["neck_radius_mm"], r1), (0, r1)], segs=48, m=m), "steel_polished")
    star = [((R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.cos(math.pi * i / cw["teeth"]),
             (R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.sin(math.pi * i / cw["teeth"])) for i in range(cw["teeth"] * 2)]
    add("crown", Geo().prism(star, r1, r2, m), "steel_polished", bevel=0.12)
    add("crown_end", Geo().lathe([(0, r2 - 0.05), (R0 - cw["flute_depth"], r2 - 0.05)] + [(Re + (R0 - cw["flute_depth"] - Re) * math.cos(a), r2 + (r3 - r2) * math.sin(a))
                                                                                      for a in [k * math.pi / 16 for k in range(1, 9)]] + [(0, r3)], segs=48, m=m), "steel_polished")

    # ---- leather strap: the photo's own strap (grain, stitching) along its length, house curl from the horn tips ----
    st = cfg["strap"]
    hw = inner - st["edge_inset"]
    tip = (tips["top"] + tips["bottom"]) / 2
    zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], tip + st["bend_after_tip"]
    s_of = lambda y, z: abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
    ends = pm["strap_end_mm"]  # last straightened strap row; the rolled-under strap past it reuses that row
    box = curl(bend_y, R, zm)
    g = Geo()
    for sy, bar_edge in ((1, tc["bar_top_y_mm"][0]), (-1, -tc["bar_bottom_y_mm"][1])):
        box(g, -hw, hw, bar_edge - st["under_case"], st["end_y"], ds * st["z0"], ds * st["z1"], sy)
    add("strap", g, "strap_leather", bevel=st["bevel"],
        uv_of=lambda x, y, z: photo_uv(x, math.copysign(min(s_of(y, z), ends["top" if y > 0 else "bottom"]), y)))

    # ---- checks against the anchors ----
    out = {"width": round(tr["case_x_mm"][1] - tr["case_x_mm"][0], 3), "strap_width": round(2 * hw, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.4, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "horn_tip_y_mm": tips, "lug_to_lug_mm": round(tips["top"] + tips["bottom"], 2), "strap_end_y_mm": st["end_y"],
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
