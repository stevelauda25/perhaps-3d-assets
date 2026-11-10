"""watch_orient_re_at0007n00b: build the Orient Star RE-AT0007N00B (polished steel case, grey open-heart dial with power
reserve, rose-gold hands, black croc leather strap) as a flat-backed front relief.

Params: spec (config/watches/orient-re-at0007n00b.json). Frame as watch_fossil_fs4735: mm, origin = hand pivot, dial faces
+z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, strap built at final depth
with the house curl. As the Rolex Daytona builds, the front photo is projected straight from the front on every part (case,
bezel, lugs, crown, dial, hands, strap), with emission so the photographed shading reads in any viewer light; only the shape
seen from the side is modelled. The photo is taken a little from the right and above, so the case is lofted from the photo
outline (trace.case_polar_mm, per angle about the pivot) into the elliptic crystal ring (trace.crystal_ellipse_mm); lugs are
slabs from the photo outline; hands are raised needle plates at the photo's time; the strap bends at each side's lug tips.
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
    for key, v in cfg["photo"].items():  # one image, own roughness / emission per surface
        m = mats[key] = photo_material(key, ROOT / cfg["photo_map"], v["roughness"])
        b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Specular IOR Level"].default_value = v["specular"]
        m.node_tree.links.new(next(n for n in m.node_tree.nodes if n.type == "TEX_IMAGE").outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = v["emission"]

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
        if mat in cfg["photo"]:  # the photo straight from the front, or the part's own mapping
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

    # ---- ring kinds: "case" = photo outline + offset, "crystal" = crystal ellipse + offset, "pivot" = circle radius ----
    cp, ce = tr["case_polar_mm"], tr["crystal_ellipse_mm"]
    rc = cp["r"]
    angs = [math.radians(cp["step_deg"] * i) for i in range(len(rc))]
    (ex, ey), erx, ery = ce["centre"], ce["rx"], ce["ry"]

    def ring(kind, v, z):
        if kind == "case":
            return [((r + v) * math.sin(a), (r + v) * math.cos(a), z) for a, r in zip(angs, rc)]
        if kind == "crystal":
            return [(ex + (erx + v) * math.sin(a), ey + (ery + v) * math.cos(a), z) for a in angs]
        return [(v * math.sin(a), v * math.cos(a), z) for a in angs]

    def r_case(a):  # photo outline radius at angle a (rad, clockwise from 12)
        f = (math.degrees(a) % 360) / cp["step_deg"]
        i = int(f)
        return rc[i % len(rc)] + (rc[(i + 1) % len(rc)] - rc[i % len(rc)]) * (f - i)

    # ---- case and bezel ----
    c = cfg["case"]

    def case_uv(x, y, z):  # flank vertices sample the photo just inside the outline, not the background past it
        r, a = math.hypot(x, y), math.atan2(x, y)
        f = min(1.0, (r_case(a) - c["uv_inset"]) / r) if r > 1e-6 else 1.0
        return photo_uv(x * f, y * f)
    add("case", loft([ring(*r) for r in c["rings"]]), "steel_photo", uv_of=case_uv)

    # ---- lugs: photo outline, top sloping from the case down to the tip ----
    lg = cfg["lug"]
    g = Geo()
    for t in tr["lugs"].values():
        d0, d1 = lg["slope_from_r"], t["r_max_mm"]
        top = lambda x, y, d0=d0, d1=d1: lg["top_z_at_case"] + (lg["top_z_at_tip"] - lg["top_z_at_case"]) * min(1.0, max(0.0, (math.hypot(x, y) - d0) / (d1 - d0)))
        slab(g, [tuple(p) for p in t["outline_mm"]], 0.0, top)
    add("lugs", g, "steel_photo", bevel=lg["bevel"])

    # ---- crystal (alpha glass, no transmission); dial with the minute track rising to the crystal ring ----
    cr, d = cfg["crystal"], cfg["dial"]
    add("crystal", loft([ring("crystal", 0.0, cr["z0"]), ring("crystal", 0.0, cr["z1"]), ring("crystal", -erx * 0.3, cr["z1"] + cr["dome"] * 0.5),
                         ring("crystal", -erx * 0.6, cr["z1"] + cr["dome"] * 0.85)], top_cap=True), "crystal")
    add("dial", loft([ring("crystal", 0.05, d["z"] - 0.3), ring("crystal", 0.05, d["track_z"]), ring("pivot", tr["dial_flat_mm"], d["z"])], top_cap=True),
        "dial_photo", smooth=True)

    # ---- hands at the photo's time: raised plates showing the photographed hands ----
    hs, th = cfg["hands"], cfg["hands"]["thickness"]
    for name, z in hs["z"].items():
        add("hand_" + name, slab(Geo(), [tuple(p) for p in tr["hands"][name]["outline_mm"]], z, lambda x, y, z=z: z + th), "dial_photo", bevel=0.02)
    zt, hub_r = max(hs["z"].values()) + th, tr["hub_mm"]
    add("hub", Geo().lathe([(0, d["z"]), (hub_r, d["z"]), (hub_r, zt + 0.06), (hub_r * 0.7, zt + 0.1), (0, zt + 0.11)], segs=48), "dial_photo", smooth=True)

    # ---- crown on the 3 o'clock axis: neck, fluted body, rounded end ----
    cw, tc = cfg["crown"], tr["crown"]
    m = Matrix(((0, -1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_4x4()  # local z along +x, local y up
    m.translation = (0.0, tc["centre_y_mm"], cw["z"])
    R0, (r1, r2) = tc["radius_mm"], tc["x_from_to_mm"]
    add("crown_neck", Geo().lathe([(0, r1 - 1.5), (R0 * cw["neck_fraction"], r1 - 1.5), (R0 * cw["neck_fraction"], r1 + 0.1), (0, r1 + 0.1)], segs=48, m=m),
        "steel_photo", smooth=True)
    star = [((R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.cos(math.pi * i / tc["teeth"]),
             (R0 if i % 2 == 0 else R0 - cw["flute_depth"]) * math.sin(math.pi * i / tc["teeth"])) for i in range(tc["teeth"] * 2)]
    add("crown", Geo().prism(star, r1, r2 - 0.5, m), "steel_photo", bevel=0.08)
    add("crown_end", Geo().lathe([(0, r2 - 0.5), (R0 - 0.15, r2 - 0.5), (R0 - 0.8, r2), (0, r2)], segs=48, m=m), "steel_photo", smooth=True)

    # ---- leather strap: the photo's strap along its length, house curl from each side's lug tips ----
    st = cfg["strap"]
    zm, R = ds * (st["z0"] + st["z1"]) / 2, st["bend_radius"]
    g = Geo()
    ends, maps = pm["strap_end_mm"], {}
    for side, sy in (("top", 1), ("bottom", -1)):
        s = tr["strap_mm"][side]
        bend_y = s["tip_y"] + st["bend_after_tip"]
        box = curl(bend_y, R, zm)
        box(g, s["x"][0] + st["edge_inset"], s["x"][1] - st["edge_inset"], st["start_y"], bend_y + R * st["arc_over_radius"], ds * st["z0"], ds * st["z1"], sy)
        maps[sy] = (bend_y, ends[side], s["x"][0] + st["uv_inset"], s["x"][1] - st["uv_inset"])

    def strap_uv(x, y, z):
        bend_y, end, xa, xb = maps[1 if y > 0 else -1]
        x = min(max(x, xa), xb)  # side walls take the strap's own edge pixels
        s = abs(y) if abs(y) <= bend_y + 1e-6 else bend_y + R * math.atan2(abs(y) - bend_y, z - (zm - R))
        return photo_uv(x, math.copysign(s if s <= end else max(2 * end - s, 0.0), y))  # past the photo's strap end: mirrored back, no streaks
    add("strap", g, "strap_photo", bevel=st["bevel"], uv_of=strap_uv)

    # ---- checks against the anchors ----
    out = {"diameter": round((tr["case_row_px"][1] - tr["case_row_px"][0] + 1) / S, 3),
           "strap_width": round(sum(v["x"][1] - v["x"][0] for v in tr["strap_mm"].values()) / 2, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.4, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "lug_tip_y_mm": {k: v["tip_y"] for k, v in tr["strap_mm"].items()},
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
