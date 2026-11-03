"""watch_speedmaster: build the Omega Speedmaster Moonwatch Professional 310.30.42.50.01.001 into the Casio studio base.

Params: spec (config/watches/*.json). Input scene = assets/watches/baseline/casio_studio_base.blend (Casio's upright
studio, ground, lights, cameras, world, colour management; no watch). The watch is plain mesh data in mm under one pose
empty with the same convention as the Casio asset (scale 0.001, rotated 90 deg about X: dial faces the -Y camera, bracelet
loop stands behind it). The bracelet row mesh is one shared datablock instanced along the loop. Asserts the verified Omega
dimensions before saving.
"""
import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
P = "OMG | "


def rot(x, y, deg):
    """Rotate (x, y) clockwise by deg seen from +Z with 0 deg at +Y (dial angles)."""
    t = math.radians(deg)
    return (x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t))


class Geo:
    """Vertex/face accumulator: lathes (hard corners split) and prisms, optionally transformed."""

    def __init__(self):
        self.v, self.f, self.smooth = [], [], []

    def lathe(self, profile, segs=96, hard=35, m=None):
        area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(profile, profile[1:] + profile[:1]))
        pts = profile if area > 0 else profile[::-1]  # counter-clockwise in (r, z) -> outward normals
        runs, cur = [], [pts[0]]
        for i in range(1, len(pts) - 1):
            a, b = (pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]), (pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1])
            turn = abs(math.degrees(math.atan2(a[0] * b[1] - a[1] * b[0], a[0] * b[0] + a[1] * b[1])))
            cur.append(pts[i])
            if turn > hard:
                runs.append(cur)
                cur = [pts[i]]
        cur.append(pts[-1])
        runs.append(cur)
        for run in runs:
            rings = []
            for r, z in run:
                if r < 1e-9:
                    self.v.append(self._t((0, 0, z), m))
                    rings.append([len(self.v) - 1] * segs)
                else:
                    base = len(self.v)
                    for k in range(segs):
                        a = 2 * math.pi * k / segs
                        self.v.append(self._t((r * math.cos(a), r * math.sin(a), z), m))
                    rings.append(list(range(base, base + segs)))
            for j in range(len(run) - 1):
                for k in range(segs):
                    quad = (rings[j][k], rings[j][(k + 1) % segs], rings[j + 1][(k + 1) % segs], rings[j + 1][k])
                    face = tuple(q for i, q in enumerate(quad) if q != quad[i - 1])
                    if len(face) >= 3:
                        self.f.append(face)
                        self.smooth.append(True)
        return self

    def prism(self, poly, z0, z1, m=None):
        area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))
        poly = poly if area > 0 else poly[::-1]
        n, base = len(poly), len(self.v)
        for z in (z0, z1):
            self.v += [self._t((x, y, z), m) for x, y in poly]
        self.f.append(tuple(range(base + n - 1, base - 1, -1)))
        self.f.append(tuple(range(base + n, base + 2 * n)))
        for i in range(n):
            j = (i + 1) % n
            self.f.append((base + i, base + j, base + n + j, base + n + i))
        self.smooth += [False] * (n + 2)  # flat: prisms share vertices across 90 degree edges (bevel modifier smooths)
        return self

    @staticmethod
    def _t(p, m):
        return tuple(m @ Vector(p)) if m is not None else p

    def mesh(self, name, smooth=None):
        me = bpy.data.meshes.new(name)
        me.from_pydata(self.v, [], self.f)
        me.validate()
        me.update()
        flags = self.smooth if smooth is None else [smooth] * len(self.f)
        if len(flags) == len(me.polygons):
            me.polygons.foreach_set("use_smooth", flags)
        return me


def rect(cx, cy, w, h):
    return [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]


def principled(name, p):
    m = bpy.data.materials.new(P + name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    values = {"Base Color": (*p["color"], 1), "Metallic": p["metallic"], "Roughness": p["roughness"],
              "Anisotropic": p.get("anisotropic"), "Coat Weight": p.get("coat"),
              "Transmission Weight": p.get("transmission"), "IOR": p.get("ior")}
    for key, value in values.items():
        if value is not None and key in b.inputs:
            b.inputs[key].default_value = value
    return m


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    scene = bpy.context.scene
    coll = bpy.data.collections.new("WATCH | Speedmaster 310.30.42.50.01.001")
    scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    parts = {}

    # Loop path (y, z) of the bracelet centre line, right half, resampled by arc length.
    b = cfg["bracelet"]
    ctrl = [Vector(p) for p in b["path_yz"]]
    ctrl = [ctrl[0] * 2 - ctrl[1]] + ctrl + [ctrl[-1] * 2 - ctrl[-2]]
    dense = []
    for i in range(1, len(ctrl) - 2):
        p0, p1, p2, p3 = ctrl[i - 1], ctrl[i], ctrl[i + 1], ctrl[i + 2]
        for s in range(20):
            t = s / 20
            dense.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    dense.append(ctrl[-2])
    cum = [0.0]
    for a, c in zip(dense, dense[1:]):
        cum.append(cum[-1] + (c - a).length)
    half_len = cum[-1]

    def at(u):
        u = min(max(u, 0), half_len)
        i = max(k for k in range(len(cum) - 1) if cum[k] <= u)
        f = (u - cum[i]) / max(cum[i + 1] - cum[i], 1e-9)
        pos = dense[i].lerp(dense[i + 1], f)
        tan = (dense[i + 1] - dense[i]).normalized()
        return pos, tan

    pose = bpy.data.objects.new(P + "pose", None)
    coll.objects.link(pose)
    pose.rotation_euler = (math.pi / 2, 0, cfg["pose"]["yaw_rad"])
    pose.scale = (0.001,) * 3
    pose.location = (cfg["pose"]["x_m"], 0, (max(p.x for p in dense) + b["thickness"] / 2) * 0.001)  # loop rests on the Casio ground plane
    pose["role"] = "presentation pose: dial faces -Y camera, bracelet loop behind"

    def add(name, geo_or_mesh, mat, bevel=None, loc=None):
        me = geo_or_mesh.mesh(name, True if bevel else None) if isinstance(geo_or_mesh, Geo) else geo_or_mesh
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if bevel:
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            m = o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
            m.keep_sharp = True
        if loc:
            o.location = loc
        parts[name] = o
        return o

    # --- case, caseback, lugs ---
    c = cfg["case"]
    add("case", Geo().lathe([tuple(p) for p in c["profile_rz"]]), "steel_brushed")
    add("medallion", Geo().lathe([(0, 0.35), (c["caseback"]["medallion_radius"], 0.35), (c["caseback"]["medallion_radius"] - 0.3, 0.02), (0, 0.02)]), "steel_polished")
    lug = c["lug"]
    to_yz = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # local (u, v, w) -> world (w, u, v)
    for sy in (1, -1):
        for sx in (1, -1):
            poly = [(sy * y, z) for y, z in lug["profile_yz"]]
            x0, x1 = (lug["inner_x"], lug["outer_x"]) if sx > 0 else (-lug["outer_x"], -lug["inner_x"])
            add("lug_%+d%+d" % (sx, sy), Geo().prism(poly, x0, x1, to_yz), "steel_brushed", bevel=lug["bevel"])

    # --- bezel + tachymeter, crystal ---
    z = cfg["bezel"]
    add("bezel", Geo().lathe([tuple(p) for p in z["profile_rz"]] + [tuple(z["profile_rz"][0])]), "bezel_black")
    cr = cfg["crystal"]
    h = cr["apex_z"] - cr["rim_top_z"]
    big_r = (cr["rim_radius"] ** 2 + h * h) / (2 * h)
    arc = []
    for i in range(1, cr["segments"] + 1):
        a = math.asin(cr["rim_radius"] / big_r) * (1 - i / cr["segments"])
        arc.append((big_r * math.sin(a), cr["apex_z"] - big_r * (1 - math.cos(a))))
    add("crystal_hesalite", Geo().lathe([(0, cr["base_z"]), (cr["rim_radius"], cr["base_z"]), (cr["rim_radius"], cr["rim_top_z"])] + arc, segs=128), "hesalite")

    # --- dial ---
    d = cfg["dial"]
    add("dial", Geo().lathe([(0, 8.0), (d["outer_radius"], 8.0), (d["outer_radius"], d["outer_z"]), (d["inner_radius"], d["outer_z"]),
                             (d["inner_radius"] - 0.3, d["inner_z"]), (0, d["inner_z"])]), "dial_black")
    sub = d["subdial"]
    g = Geo()
    for cx, cy in sub["centers"]:
        g.lathe([(0, d["inner_z"] - 0.05), (sub["radius"], d["inner_z"] - 0.05), (sub["radius"] - 0.12, sub["z"]), (0, sub["z"])], segs=64, m=Matrix.Translation((cx, cy, 0)))
    add("subdials", g, "subdial_black")
    ix = d["index"]
    g, top = Geo(), d["inner_z"]
    for hour in range(12):
        ang = hour * 30
        pts = [rot(x, y, ang) for x, y in rect(0, ix["radius"], ix["width"], ix["length"])]
        g.prism(pts, top, top + ix["height"])
        if hour == 0:  # dot pair beside the 12 bar
            for sx in (-1.5, 1.5):
                g.lathe([(0, top), (0.5, top), (0.5, top + ix["height"]), (0, top + ix["height"])], segs=16, m=Matrix.Translation((sx, ix["radius"] + 1.0, 0)))
    add("indices_lume", g, "lume")
    mt = d["minute_track"]
    g = Geo()
    for i in range(mt["count"]):
        long_tick = i % 5 == 0
        pts = [rot(x, y, i * 360 / mt["count"]) for x, y in rect(0, (mt["r_in"] + mt["r_out"]) / 2, mt["width"] * (1.8 if long_tick else 1), mt["r_out"] - mt["r_in"] - (0 if long_tick else 0.45))]
        g.prism(pts, d["outer_z"], d["outer_z"] + 0.04)
    add("minute_track", g, "print_white")

    def text(name, body, x, y, size, zpos, deg=0):
        cu = bpy.data.curves.new(P + name, "FONT")
        cu.body, cu.size, cu.align_x, cu.align_y = body, size, "CENTER", "CENTER"
        o = bpy.data.objects.new(P + name, cu)
        coll.objects.link(o)
        o.parent = pose
        o.location, o.rotation_euler = (x, y, zpos), (0, 0, math.radians(-deg))
        cu.materials.append(mats["print_white"])
        return o

    def join_texts(objs, name):
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.convert(target="MESH")
        bpy.ops.object.join()
        bpy.context.active_object.name = P + name
        parts[name] = bpy.context.active_object

    texts = [text("t_" + k, k, v[0], v[1], v[2], d["inner_z"] + 0.03) for k, v in d["text"].items()]
    for (cx, cy), labels in zip(sub["centers"], [[("60", 0), ("20", 120), ("40", 240)], [("30", 0), ("10", 120), ("20", 240)], [("12", 0), ("3", 90), ("6", 180), ("9", 270)]]):
        for label, ang in labels:
            px, py = rot(0, sub["radius"] - 1.25, ang)
            texts.append(text("s_%s_%d_%d" % (label, cx, ang), label, cx + px, cy + py, 0.95, sub["z"] + 0.03))
    join_texts(texts, "dial_print")
    texts = []
    for n in z["numerals"]:
        theta = (360 * 60 / n) % 360
        px, py = rot(0, z["numeral_radius"], theta)
        texts.append(text("b_%d" % n, str(n), px, py, z["numeral_size"], z["profile_rz"][4][1] + 0.02, theta))
    join_texts(texts, "bezel_numerals")

    # --- hands ---
    hz, th = cfg["hands"]["z"], cfg["hands"]["thickness"]
    time_ = cfg["hands"]["time"]

    def hand(name, poly, deg, z0, lume_scale=None, center=(0, 0)):
        pts = [(center[0] + rot(x, y, deg)[0], center[1] + rot(x, y, deg)[1]) for x, y in poly]
        add(name, Geo().prism(pts, z0, z0 + th), "hand_white", bevel=0.03)
        if lume_scale:
            inner = [(x * lume_scale[0], y * lume_scale[1] + lume_scale[2]) for x, y in poly]
            add(name + "_lume", Geo().prism([(center[0] + rot(x, y, deg)[0], center[1] + rot(x, y, deg)[1]) for x, y in inner], z0 + th, z0 + th + 0.04), "lume")

    hand("hand_hour", [(-0.5, -2), (0.5, -2), (0.6, 0), (1.2, 3.5), (0, 9.6), (-1.2, 3.5), (-0.6, 0)], time_["hour_deg"], hz["hour"], (0.5, 0.62, 0.6))
    hand("hand_minute", [(-0.45, -2), (0.45, -2), (0.6, 0), (1.0, 6.0), (0, 14.8), (-1.0, 6.0), (-0.6, 0)], time_["minute_deg"], hz["minute"], (0.5, 0.7, 0.8))
    hand("hand_chrono", [(-0.18, -4.5), (0.18, -4.5), (0.18, 16.0), (0, 16.8), (-0.18, 16.0)], time_["chrono_deg"], hz["chrono"])
    hand("hand_chrono_tail", [(-0.55, -4.9), (0.55, -4.9), (0.55, -2.6), (-0.55, -2.6)], time_["chrono_deg"], hz["chrono"])
    for i, (cx, cy) in enumerate(sub["centers"]):
        hand("hand_sub%d" % i, [(-0.12, -0.8), (0.12, -0.8), (0.12, sub["radius"] - 0.9), (0, sub["radius"] - 0.6), (-0.12, sub["radius"] - 0.9)], 0, sub["z"] + 0.05, center=(cx, cy))
    add("hand_hub", Geo().lathe([(0, hz["hour"] - 0.1), (1.05, hz["hour"] - 0.1), (1.05, hz["chrono"] + th), (0.55, hz["chrono"] + th + 0.25), (0, hz["chrono"] + th + 0.3)], segs=48), "steel_polished")

    # --- crown, pushers (along +X) ---
    cw = cfg["crown"]
    star = [((cw["radius"] if i % 2 == 0 else cw["radius"] - 0.4) * math.cos(math.pi * i / cw["teeth"]),
             (cw["radius"] if i % 2 == 0 else cw["radius"] - 0.4) * math.sin(math.pi * i / cw["teeth"])) for i in range(cw["teeth"] * 2)]
    along_x = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))  # local (u, v, w) -> (w, u, v)
    add("crown", Geo().prism(star, cw["x0"], cw["x1"], Matrix.Translation((0, cw["y"], cw["z"])) @ along_x), "steel_polished", bevel=0.2)
    pu = cfg["pushers"]
    g = Geo()
    for y in pu["y"]:
        tr = Matrix.Translation((0, y, pu["z"])) @ Matrix(((0, 0, 1, 0), (0, 1, 0, 0), (-1, 0, 0, 0), (0, 0, 0, 1)))
        g.lathe([(0, 0), (pu["radius"] * 0.8, 0), (pu["radius"] * 0.8, 1.2), (pu["radius"], 1.2), (pu["radius"], (pu["x1"] - pu["x0"]) - 0.4), (pu["radius"] - 0.4, pu["x1"] - pu["x0"]), (0, pu["x1"] - pu["x0"])],
                segs=40, m=Matrix.Translation((pu["x0"], 0, 0)) @ tr)
    add("pushers", g, "steel_polished")

    # --- bracelet: one row mesh instanced along the loop ---
    widths, gap_off = b["link_widths"], [0, 0.5, 0, 0.5, 0]
    g, x = Geo(), -sum(widths) / 2
    for w, off in zip(widths, gap_off):
        g.prism(rect(x + w / 2, off * b["pitch"], w - 0.1, b["row_length"]), -b["thickness"] / 2, b["thickness"] / 2)
        x += w
    row_mesh = g.mesh(P + "bracelet_row", True)
    mats_row = mats["steel_brushed"]
    row_mesh.materials.append(mats_row)
    usable = half_len - b["clasp_half"]
    rows = int(usable // b["pitch"])
    pitch = usable / rows
    for side in (1, -1):
        for k in range(rows):
            pos, tan = at((k + 0.5) * pitch)
            n = Vector((-tan.y, tan.x))
            yaxis, zaxis = Vector((0, side * tan.x, tan.y)), Vector((0, side * n.x, n.y))
            xaxis = yaxis.cross(zaxis)
            m = Matrix((xaxis, yaxis, zaxis)).transposed().to_4x4()
            m.translation = (0, side * pos.x, pos.y)
            o = bpy.data.objects.new(P + "row_%+d_%02d" % (side, k), row_mesh)
            coll.objects.link(o)
            o.parent = pose
            for mod in (("Edge radius", "BEVEL"), ("Weighted normals", "WEIGHTED_NORMAL")):
                md = o.modifiers.new(*mod)
                if mod[1] == "BEVEL":
                    md.width, md.segments, md.limit_method, md.angle_limit = b["bevel"], 2, "ANGLE", math.radians(35)
                else:
                    md.keep_sharp = True
            o.matrix_basis = m @ Matrix.Diagonal((1 - (1 - b["end_width"] / b["width"]) * (k + 0.5) / rows, 1, 1, 1))
    end, _ = at(half_len)
    clasp = Geo().prism(rect(0, 0, b["end_width"] + 0.6, 2 * b["clasp_half"]), -b["thickness"] / 2 - 0.6, b["thickness"] / 2 + 0.4)
    add("clasp", clasp, "steel_brushed", bevel=0.5, loc=(0, 0, end.y))

    # --- verified dimensions ---
    def extent(names, axis):
        vals = [v.co[axis] for n in names for v in parts[n].data.vertices]
        return min(vals), max(vals)
    lugs = [n for n in parts if n.startswith("lug_")]
    out = {}
    out["lug_to_lug"] = round(extent(lugs, 1)[1] - extent(lugs, 1)[0], 3)
    out["diameter"] = round(extent(["bezel"], 0)[1] - extent(["bezel"], 0)[0], 3)
    out["thickness"] = round(extent(["crystal_hesalite"], 2)[1] - min(extent(["case", "medallion"], 2)[0], 0), 3)
    out["lug_width"] = round(2 * lug["inner_x"], 3)
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.02, "%s %.3f != %.3f" % (key, out[key], want)

    # --- studio comes from the Casio base: assert it is there instead of rebuilding it ---
    for name in cfg["base_requires"]:
        assert name in bpy.data.objects, "base scene lacks " + name
    scene.camera = bpy.data.objects["CAM | Hero"]
    bpy.context.view_layer.update()
    return {"verified_mm": out, "objects": len(coll.objects), "bracelet_rows": rows * 2, "loop_half_len_mm": round(half_len, 1),
            "loop_circumference_mm": round(2 * half_len + 2 * b["start_y"], 1)}
