"""watch_orient_re_at0007n00b: build the Orient Star RE-AT0007N00B (polished steel case, grey open-heart dial with power
reserve, rose-gold dauphine hands, black croc leather strap) as a flat-backed front relief.

Params: spec (config/watches/orient-re-at0007n00b.json). Frame as watch_fossil_fs4735: mm, origin = hand pivot, dial faces
+z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, strap built at final depth
with the house curl. House method: case, bezel, lugs and crown in the house polished steel, house glass, modelled faceted
rose-gold hands; one photo map (pipeline/orient_re_at0007n00b_dial.py, hands removed) serves only the dial and the leather
strap. The model is the real round watch: 39.3 mm case and crystal ring about the pivot, four mirrored lugs (outline from the
straight front photo of round 1), crown on the 3 o'clock axis, 20 mm strap. The photo is taken a little from the right, so the
dial UVs and the hands go through the photo's crystal ellipse, and the strap samples the photo's slanted strap (flat part only).
Rebuild with --force after regenerating the photo map.
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT


def loft(rings, top_cap=False):
    """Solid through rings of equal-length point lists [(x, y, z), ...] (same angles, clockwise from 12): flat cap on the
    first ring, optional flat cap on the last."""
    N, g = len(rings[0]), Geo()
    for lo, hi in zip(rings, rings[1:]):
        base = len(g.v)
        g.v += lo + hi
        for k in range(N):
            kk = (k + 1) % N
            g.f.append((base + kk, base + k, base + N + k, base + N + kk))
            g.smooth.append(True)
    caps = [(rings[0], False)] + ([(rings[-1], True)] if top_cap else [])
    for pts, flip in caps:
        base = len(g.v)
        g.v += pts
        f = tuple(range(base, base + N))
        g.f.append(f[::-1] if flip else f)
        g.smooth.append(False)
    return g


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    pm = json.loads((ROOT / cfg["photo_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Orient Star RE-AT0007N00B front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    for key, rough in cfg["photo_roughness"].items():  # one image, two surfaces: dial and strap
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
        if mat in cfg["photo_roughness"]:  # photo map: planar from the front, or the strap's own mapping
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

    # ---- model frame: round case and crystal about the pivot. The photo is taken a little from the right, so its crystal
    #      ring is an ellipse; dial UVs and the hands go through that ellipse (photo <-> model) ----
    ce = tr["crystal_ellipse_mm"]
    (ex, ey), erx, ery = ce["centre"], ce["rx"], ce["ry"]
    R_open, R_case = (erx + ery) / 2, cfg["case"]["radius"]
    angs = [math.radians(cfg["case"]["step_deg"] * i) for i in range(int(round(360 / cfg["case"]["step_deg"])))]
    ring = lambda r, z: [(r * math.sin(a), r * math.cos(a), z) for a in angs]

    def dial_uv(x, y, z):  # model circle -> photo ellipse; the pivot stays on the photo's pivot, the rim on the photo's rim
        f = min(1.0, math.hypot(x, y) / R_open)
        return photo_uv(x * erx / R_open + ex * f, y * ery / R_open + ey * f)
    to_model = lambda p: (p[0] * R_open / erx, p[1] * R_open / ery)

    # ---- case and bezel: one loft of round rings ("case" = offset from the case radius, "crystal" = offset from the opening) ----
    c = cfg["case"]
    add("case", loft([ring((R_case if k == "case" else R_open) + v, z) for k, v, z in c["rings"]]), "steel_polished")

    # ---- lugs: one outline (straight front photo, mean of three lugs) mirrored to all four, top sloping to the tip ----
    lg = cfg["lug"]
    tip, xi = lg["tip_y"], lg["inner_x"]
    outer = [(xi + off, tip - d) for d, off in lg["outer_offset_by_depth"]]  # depth from the tip -> offset out from the inner edge
    poly = [(xi, tip)] + outer + [(outer[-1][0] - lg["into_case"], outer[-1][1] - lg["into_case"]), (xi, outer[-1][1] + 1.0)]
    top = lambda x, y: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * min(1.0, max(0.0, (abs(y) - lg["slope_from_y"]) / (tip - lg["slope_from_y"])))
    g = Geo()
    for sx in (1, -1):
        for sy in (1, -1):
            slab(g, [(sx * x, sy * y) for x, y in poly], 0.0, top)
    add("lugs", g, "steel_polished", bevel=lg["bevel"])

    # ---- crystal (alpha glass, no transmission); dial with the minute track rising to the crystal ring ----
    cr, d = cfg["crystal"], cfg["dial"]
    add("crystal", loft([ring(R_open, cr["z0"]), ring(R_open, cr["z1"]), ring(R_open * 0.7, cr["z1"] + cr["dome"] * 0.5),
                         ring(R_open * 0.4, cr["z1"] + cr["dome"] * 0.85)], top_cap=True), "crystal")
    add("dial", loft([ring(R_open + 0.05, d["z"] - 0.3), ring(R_open + 0.05, d["track_z"]), ring(tr["dial_flat_mm"] * R_open / erx, d["z"])], top_cap=True),
        "dial", smooth=True, uv_of=dial_uv)

    # ---- hands at the photo's time: faceted dauphine plates, ridge on the tip-tail axis, rose gold ----
    hs, th = cfg["hands"], cfg["hands"]["thickness"]
    for name, z in hs["z"].items():
        p = [to_model(q) for q in tr["hands"][name]["outline_mm"]]  # tip, base, hub, tail, hub, base (trace order)
        axis = {p[0], p[3]}
        top = lambda x, y, z=z, axis=axis: z + (th if (x, y) in axis else th * hs["edge_fraction"])
        g = Geo()
        slab(g, p[0:4], z, top)
        slab(g, p[3:6] + [p[0]], z, top)
        add("hand_" + name, g, "rose_gold", bevel=0.02)
    zt, hub_r = max(hs["z"].values()) + th, tr["hub_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, zt + 0.06), (hub_r * 0.7, zt + 0.1), (0, zt + 0.11)], segs=48), "rose_gold", smooth=True)

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

    # ---- leather strap: 20 mm, straight down the middle, house curl from the lug tips. Each side samples the photo's own
    #      strap (slanted in the photo): model x across [-hw, hw] -> photo strap x range; model s -> photo s with the lug tips
    #      aligned, folded back and forth over the photo's flat leather (case edge to just past the tip) ----
    st = cfg["strap"]
    hw = lg["inner_x"] - st["edge_inset"]
    zm, R, bend_y = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"], tip + st["bend_after_tip"]
    box = curl(bend_y, R, zm)
    g = Geo()
    for sy in (1, -1):
        box(g, -hw, hw, st["start_y"], bend_y + R * st["arc_over_radius"], ds * st["z0"], ds * st["z1"], sy)
    ends = pm["strap_end_mm"]
    photo = {sy: (tr["strap_mm"][k]["x"], tr["strap_mm"][k]["tip_y"], st["photo_case_edge"][k], ends[k]) for sy, k in ((1, "top"), (-1, "bottom"))}

    def strap_uv(x, y, z):
        (x0, x1), ptip, pedge, end = photo[1 if y > 0 else -1]
        u = min(max((x + hw) / (2 * hw), st["uv_inset"]), 1 - st["uv_inset"])  # side walls take the strap's own edge pixels
        s = abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
        lo, hi = pedge, min(ptip + st["photo_past_tip"], end)  # flat leather in the photo: past it the strap turns away (lighter, glossy)
        k, w = divmod(ptip + (s - tip) - lo, hi - lo)  # same scale, tips aligned; folded back and forth into [lo, hi]: no seam, no streaks
        sp = lo + w if int(k) % 2 == 0 else hi - w
        return photo_uv(x0 + u * (x1 - x0), math.copysign(sp, y))
    add("strap", g, "strap_leather", bevel=st["bevel"], uv_of=strap_uv)

    # ---- checks against the anchors ----
    out = {"diameter": round(2 * R_case, 3), "strap_width": round(2 * hw + 2 * st["edge_inset"], 3),
           "photo_case_width": round((tr["case_row_px"][1] - tr["case_row_px"][0] + 1) / S, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.4, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": tip, "lug_to_lug_mm": round(2 * tip, 2), "crystal_mm": round(2 * R_open, 3),
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
