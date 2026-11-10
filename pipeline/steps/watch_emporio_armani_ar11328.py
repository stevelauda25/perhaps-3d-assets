"""watch_emporio_armani_ar11328: build the Emporio Armani Matteo AR11328 (blue anodised aluminium, green-to-black dial, blue
Milanese mesh) as a flat-backed front relief.

Params: spec (config/watches/emporio-armani-ar11328.json). Same frame as watch_fossil_fs5305: mm, origin = hand pivot, dial
faces +z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, bracelet built at final
depth with the house curl. Own construction: round case with a wide domed bezel (one lathe), open lug arms (outer edge from
the traced silhouette, inner edge along the window), flat dial with the photo map, light blue baton hands and hub, fluted
black crown at 3, solid end cap between the arms at each end, Milanese mesh (photo map, pipeline/emporio_armani_ar11328_dial.py)
from under the case through the cap and curled from the cap's outer end. Rebuild with --force after regenerating the maps.
"""
import json
import math

import bpy

from pipeline.steps.watch_seiko_front import P, curl, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT
from pipeline.steps.watch_zeppelin_z70363 import axis_matrix


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    dm = json.loads((ROOT / cfg["dial_map"]).with_suffix(".json").read_text())
    br = cfg["bracelet"]
    coll = bpy.data.collections.new("WATCH | %s front relief" % cfg["model"])
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    mats["dial"] = photo_material("dial_photo", ROOT / cfg["dial_map"], cfg["dial"]["roughness"])
    mats["mesh"] = photo_material("mesh_photo", ROOT / cfg["mesh_map"], br["mesh_roughness"])
    next(n for n in mats["mesh"].node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Metallic"].default_value = br["mesh_metallic"]

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler, pose.location, pose.scale = (math.pi / 2, 0, 0), (0, 0, cfg["pose"]["z_m"]), (0.001,) * 3
    ds = cfg["pose"].get("depth_scale", 1.0)

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
        if not name.startswith("bracelet"):
            o.scale = (1, 1, ds)
        return o

    rg, lg_t, cap = tr["rings_mm"], tr["lug"], tr["cap_mm"]
    tip = lg_t["tip_mm"]["mean"]
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}
    tips, y_from = lg_t["tip_mm"], lg_t["from_y_mm"]
    q = lambda v: round(round(v * 4) / 4, 2)  # silhouette rows are 0.25 mm apart
    # outer edge rows: both sides, top and bottom arm each stretched to the mean tip
    half = lambda y: sum((sil[k][1] + sil[k][2]) / 2 for k in (q(y_from + (y - y_from) * (tips["top"] - y_from) / (tip - y_from)),
                                                               -q(y_from + (y - y_from) * (tips["bottom"] - y_from) / (tip - y_from)))) / 2

    # ---- round case with the wide domed bezel, one lathe ----
    c = cfg["case"]
    r_case = max(p[0] for p in c["profile"])
    add("case", Geo().lathe([tuple(p) for p in c["profile"]], segs=192), "blue_alu")
    rbk = c["profile"][0][0] + 0.2  # flat back cover: the dial does not show through from behind
    add("caseback", Geo().lathe([(0, 0), (rbk, 0), (rbk, 0.4), (0, 0.4)], segs=96), "blue_alu")

    # ---- open lug arms: traced outer edge, straight window edge, beside the end cap up to the tip ----
    lg = cfg["lug"]
    k_, b_ = lg_t["inner_edge_x_of_y"]
    win_x = lambda y: k_ * y + b_
    y_win = lg_t["inner_edge_y_mm"][1]
    y0 = y_from - lg["into_case"]
    steps = [y_from + k * 0.25 for k in range(int((tip - y_from) / 0.25) + 1)]
    edge = [max(half(y), cap["half_width"] + lg["gap"] + 0.4) for y in steps]
    edge = [sum(edge[max(k - 2, 0):k + 3]) / len(edge[max(k - 2, 0):k + 3]) for k in range(len(edge))]
    yi = lg["inner_into_case_y"]
    outline = ([(math.sqrt((r_case - 0.2) ** 2 - y0 ** 2), y0)] + list(zip(edge, steps)) +
               [(cap["half_width"] + lg["gap"], tip), (cap["half_width"] + lg["gap"], y_win + 0.1), (win_x(y_win), y_win), (win_x(yi), yi)])
    slope = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * max(abs(y) - y_from, 0) / (tip - y_from)
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in outline], 0.0, slope)
    add("lugs", g, "blue_alu", bevel=lg["bevel"])

    # ---- crystal (alpha glass, no transmission); flat dial with the photo map ----
    cr = cfg["crystal"]
    rb = rg["bezel_inner"]
    add("crystal", Geo().lathe([(0, cr["z0"]), (rb, cr["z0"]), (rb, cr["z1"]), (rb * 0.7, cr["z1"] + cr["dome"] * 0.5), (0, cr["z1"] + cr["dome"])], segs=192), "crystal")
    d = cfg["dial"]
    me = Geo().lathe([(0, d["z"]), (rb + 0.05, d["z"]), (rb + 0.05, d["z"] - 0.3)], segs=192).mesh(P + "dial", True)
    add("dial", me, "dial", uv_of=lambda x, y, z: (0.5 + x / (2 * dm["half_mm"]), 0.5 + y / (2 * dm["half_mm"])))

    # ---- baton hands at the photo's time, hub on top ----
    hs, th, t = cfg["hands"], cfg["hands"]["thickness"], tr["hands"]
    for name in ("hour", "minute", "seconds"):
        z = hs["z"][name]
        add("hand_" + name, Geo().prism([tuple(p) for p in t[name]["outline_mm"]], z, z + th), "hand_blue", bevel=0.02 if name == "seconds" else 0.03)
    zt = hs["z"]["seconds"] + th
    hub_r = tr["hub_mm"]["radius"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, zt + 0.1), (hub_r * 0.8, zt + 0.2), (0, zt + 0.22)], segs=64), "hand_blue")

    # ---- fluted black crown: short neck, fluted body with a flat chamfered end ----
    cw, tc = cfg["crown"], tr["crown"]
    m = axis_matrix(tc["angle_deg"], cw["z"])
    r0, r1 = tc["r_from_to_mm"]
    R0 = tc["radius_mm"]
    add("crown_neck", Geo().lathe([(0, r0 - 0.8), (cw["neck_radius"], r0 - 0.8), (cw["neck_radius"], r0 + 0.1), (0, r0 + 0.1)], segs=48, m=m), "crown_black")
    star = [((R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.cos(math.pi * i / tc["teeth"]),
             (R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.sin(math.pi * i / tc["teeth"])) for i in range(tc["teeth"] * 2)]
    add("crown", Geo().prism(star, r0, r1 - 0.3, m), "crown_black", bevel=0.08)
    add("crown_end", Geo().lathe([(0, r1 - 0.3), (R0 - 0.15, r1 - 0.3), (R0 - 0.5, r1), (0, r1)], segs=48, m=m), "crown_black")

    # ---- bracelet: rigid end caps between the arms, Milanese mesh through them, house curl from the cap's outer end ----
    mz = br["mesh_z"]
    zm, R = ds * (mz[0] + mz[1]) / 2, br["bend_radius"]
    bend_y = cap["to_y"] + br["bend_after_cap"]
    end_y = bend_y + 2.2 * R
    box = curl(bend_y, R, zm)
    s_of = lambda y, z: abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
    mhw, rep = tr["mesh_mm"]["half_width"], dm["mesh_repeat_mm"]
    start = math.sqrt((r_case - 0.5) ** 2 - mhw ** 2) - br["mesh_under_case"]
    caps, mesh = Geo(), Geo()
    for sy in (1, -1):
        box(caps, -cap["half_width"], cap["half_width"], cap["from_y"], bend_y, ds * br["cap_z"][0], ds * br["cap_z"][1], sy)
        box(mesh, -mhw, mhw, start, end_y, ds * mz[0], ds * mz[1], sy)
    add("bracelet_caps", caps, "blue_alu", bevel=br["cap_bevel"])
    # map taken at 6 o'clock running away from the case; the 12 o'clock side turned round. v repeats along the bracelet
    add("bracelet_mesh", mesh, "mesh", bevel=br["mesh_bevel"],
        uv_of=lambda x, y, z: (0.5 + (x if y < 0 else -x) / (2 * mhw), -(s_of(y, z) - bend_y) / rep))

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * r_case, 3), "cap_width": round(2 * cap["half_width"], 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.4, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "cap_y_mm": [cap["from_y"], cap["to_y"]], "bend_y_mm": round(bend_y, 2),
            "end_y_mm": round(end_y, 2), "front_end_mm": round(bend_y + R, 2), "mesh_repeat_mm": rep, "objects": len(coll.objects),
            "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
