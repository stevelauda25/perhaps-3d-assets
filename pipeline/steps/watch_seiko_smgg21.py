"""watch_seiko_smgg21: build the Seiko SMGG21P1 (digital, octagon gear bezel, printed insert, five-column bracelet) as a
flat-backed front relief.

Params: spec (config/watches/seiko-smgg21p1.json). Same frame as watch_seiko_ssb479: mm, origin = octagon centre, dial
faces +z, back flat at z = 0, one pose empty `SKO | pose`, watch head depth scaled by pose.depth_scale, bracelet built at
final depth with the house curl. Parts: a case plate from the traced outline (brushed top, polished edges), a polished
octagon bezel with rounded notches along every edge, the printed insert and the LCD dial from one photo map
(pipeline/seiko_smgg21_dial.py), an octagon crystal, two pushers at 4 and 8, and five bracelet columns: brushed outer and
centre links sharing joints at the case ends, polished links whose joints sit nearer the case. No hands.
Rebuild with --force after regenerating the photo map.
"""
import json
import math

import bpy
from mathutils import Matrix

from pipeline.steps.watch_seiko_front import P, curl, photo_material, plate, principled, slab
from pipeline.steps.watch_speedmaster import Geo, ROOT


def octagon(d, inset=0.0):
    """Convex octagon from support distances d[k] at k * 45 deg (0 = 12 o'clock, clockwise), moved in by inset
    (same as pipeline/seiko_smgg21_trace.octagon, which needs OpenCV and cannot be imported inside Blender)."""
    pts = []
    for k in range(8):
        a1, a2 = math.radians(45 * k), math.radians(45 * (k + 1))
        d1, d2 = d[k] - inset, d[(k + 1) % 8] - inset
        det = math.sin(a1) * math.cos(a2) - math.cos(a1) * math.sin(a2)
        pts.append(((d1 * math.cos(a2) - d2 * math.cos(a1)) / det, (d2 * math.sin(a1) - d1 * math.sin(a2)) / det))
    return pts


def clip_x(poly, c, keep_below):
    """Sutherland-Hodgman: the part of poly with x <= c (keep_below) or x >= c."""
    inside = (lambda p: p[0] <= c) if keep_below else (lambda p: p[0] >= c)
    out = []
    for i, cur in enumerate(poly):
        prev = poly[i - 1]
        if inside(cur):
            if not inside(prev):
                t = (c - prev[0]) / (cur[0] - prev[0])
                out.append((c, prev[1] + t * (cur[1] - prev[1])))
            out.append(cur)
        elif inside(prev):
            t = (c - prev[0]) / (cur[0] - prev[0])
            out.append((c, prev[1] + t * (cur[1] - prev[1])))
    return out


def faceted(poly, crease, z0, top, slope, name_geo=None):
    """Case-style solid: flat top at `top` for |x| <= crease, side facets falling by `slope` mm per mm outside it."""
    g = Geo()
    mid = clip_x(clip_x(poly, crease, True), -crease, False)
    slab(g, mid, z0, lambda x, y: top)
    for sx in (1, -1):
        side = clip_x(poly, sx * crease, sx < 0)
        if len(side) >= 3:
            slab(g, side, z0, lambda x, y: top - slope * (abs(x) - crease))
    return g


def notched(poly, pitch, width, depth, end_gap, fillet):
    """Closed polygon (counter-clockwise) with U notches cut inward along every edge, centred on each edge: flat teeth
    with rounded shoulders (fillet) and a round notch bottom, as on the photo's bezel."""
    out = []
    n = len(poly)
    r, f = width / 2, fillet
    for i in range(n):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
        L = math.hypot(x1 - x0, y1 - y0)
        ux, uy = (x1 - x0) / L, (y1 - y0) / L
        nx, ny = -uy, ux  # inward for a counter-clockwise polygon
        pt = lambda s, d: (x0 + ux * s + nx * d, y0 + uy * s + ny * d)
        out.append((x0, y0))
        k = int((L - 2 * end_gap - width - 2 * f) // pitch)
        first = (L - k * pitch) / 2
        for j in range(k + 1):
            t = first + j * pitch
            for q in range(5):  # shoulder: tooth top turns down into the notch
                a = math.pi / 2 * q / 4
                out.append(pt(t - r - f + f * math.sin(a), f - f * math.cos(a)))
            for q in range(9):  # round bottom
                a = math.pi * q / 8
                out.append(pt(t - r * math.cos(a), depth - r + r * math.sin(a)))
            for q in range(5):
                a = math.pi / 2 * q / 4
                out.append(pt(t + r + f - f * math.cos(a), f - f * math.sin(a)))
    return out


def band(d_out, d_in, z_out, z_in, z0, name):
    """Sloped octagon ring: top from octagon(d_out) at z_out down to octagon(d_in) at z_in, walls to z0, flat bottom."""
    o, i_ = octagon(d_out), octagon(d_in)
    n = 8
    verts = [(x, y, z_out) for x, y in o] + [(x, y, z_in) for x, y in i_] + [(x, y, z0) for x, y in o] + [(x, y, z0) for x, y in i_]
    faces = []
    for k in range(n):
        k2 = (k + 1) % n
        faces += [(k, n + k, n + k2, k2),  # top (octagon() runs clockwise seen from +z)
                  (2 * n + k, 2 * n + k2, k2, k),  # outer wall
                  (n + k, 3 * n + k, 3 * n + k2, n + k2),  # inner wall
                  (2 * n + k, 3 * n + k, 3 * n + k2, 2 * n + k2)[::-1]]  # bottom
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.validate()
    me.update()
    if me.polygons[0].normal.z < 0:  # keep the top facing +z
        for poly in me.polygons:
            poly.flip()
        me.update()
    return me


def run(params):
    cfg = json.loads((ROOT / params["spec"]).read_text())
    tr = json.loads((ROOT / cfg["trace"]).read_text())
    pm = json.loads((ROOT / cfg["photo_map"]).with_suffix(".json").read_text())
    coll = bpy.data.collections.new("WATCH | Seiko SMGG21P1 front relief")
    bpy.context.scene.collection.children.link(coll)
    mats = {k: principled(k, v) for k, v in cfg["materials"].items()}
    for key, rough in cfg["photo_roughness"].items():
        mats[key] = photo_material(key, ROOT / cfg["photo_map"], rough)
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
    H = pm["half_mm"]
    photo_uv = lambda x, y, z: (0.5 + x / (2 * H), 0.5 + y / (2 * H))

    def add(name, geo, mat, bevel=None, polished_bevel=False, uv_of=None, smooth=None):
        me = geo.mesh(P + name, True if bevel else smooth) if isinstance(geo, Geo) else geo
        o = bpy.data.objects.new(P + name, me)
        coll.objects.link(o)
        o.parent = pose
        me.materials.append(mats[mat])
        if mat in textured:  # planar UV, lines along the bracelet (model Y)
            uv, tile = me.uv_layers.new(name="UVMap"), textured[mat]["tile_mm"]
            for loop in me.loops:
                x, y, _ = me.vertices[loop.vertex_index].co
                uv.data[loop.index].uv = (y / tile, -x / tile)
        if uv_of:
            uv = me.uv_layers.new(name="UVMap")
            for loop in me.loops:
                uv.data[loop.index].uv = uv_of(*me.vertices[loop.vertex_index].co)
        if bevel:
            if polished_bevel:
                me.materials.append(mats["steel_polished"])
            m = o.modifiers.new("Edge radius", "BEVEL")
            m.width, m.segments, m.limit_method, m.angle_limit = bevel, 2, "ANGLE", math.radians(35)
            if polished_bevel:
                m.material = 1
            o.modifiers.new("Weighted normals", "WEIGHTED_NORMAL").keep_sharp = True
        if not name.startswith("bracelet"):
            o.scale = (1, 1, ds)
        return o

    def upward(me):
        if me.polygons[0].normal.z < 0:
            for poly in me.polygons:
                poly.flip()
            me.update()
        return me

    circle = lambda r, n=192: [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    ccw = lambda pts: pts if sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1])) > 0 else pts[::-1]

    # ---- case: flat brushed top between the creases, side facets falling outward (photo), polished edges ----
    c = cfg["case"]
    outline = [tuple(p) for p in tr["case_outline_mm"]]
    add("case", faceted(outline, c["crease_x"], 0.0, c["top_z"], c["facet_slope"]), "steel_brushed", bevel=c["bevel"], polished_bevel=True)

    # dark gap around the bezel (line outside the tooth tips, floor of the notches), following the case top
    gp = cfg["bezel_gap"]
    add("bezel_gap", faceted([tuple(p) for p in tr["groove_outline_mm"]], c["crease_x"], c["top_z"] - 0.3, c["top_z"] + gp["above_case"],
                             c["facet_slope"]), "bezel_shadow")

    # ---- notched octagon bezel, photo-mapped insert ring and LCD dial, octagon crystal ----
    bz, nt = cfg["bezel"], tr["notch"]
    outer = notched(ccw(octagon(tr["bezel_support_mm"])), nt["pitch_mm"], nt["width_mm"], nt["depth_mm"], bz["notch_end_gap"], bz["tooth_fillet"])
    ins = ccw(octagon(tr["insert_support_mm"]))
    rim_in = [v + bz["lip"] + bz["band_width"] for v in tr["insert_support_mm"]]
    add("bezel", plate([{"outer": outer, "holes": [octagon(rim_in)]}], bz["z0"], bz["z1"], P + "bezel"), "steel_polished", bevel=bz["bevel"])
    # sloped band inside the toothed rim, down to the insert edge (dark in the photo: it faces away from the light)
    add("bezel_band", band(rim_in, [v + bz["lip"] for v in tr["insert_support_mm"]], bz["z1"] - 0.05, bz["band_inner_z"], bz["z0"], P + "bezel_band"),
        "steel_polished")
    d = cfg["dial"]
    add("insert", plate([{"outer": octagon(tr["insert_support_mm"], -bz["lip"]), "holes": [circle(tr["dial_radius_mm"])]}],
                        d["z"], d["insert_z"], P + "insert"), "insert", uv_of=photo_uv)
    add("dial", upward(Geo().lathe([(0, d["z"]), (tr["dial_radius_mm"], d["z"])], segs=192).mesh(P + "dial", True)), "dial", uv_of=photo_uv)
    cr = cfg["crystal"]
    add("crystal", plate([{"outer": ins, "holes": []}], cr["z0"], cr["z1"], P + "crystal"), "crystal")

    # ---- pushers at 4 and 8: plain cylinders on radial axes ----
    pu = cfg["pushers"]
    g = Geo()
    for k, v in tr["pushers"].items():
        a = math.radians(v["angle_deg"])
        m = Matrix(((math.cos(a), -math.sin(a), 0), (0, 0, 1), (math.sin(a), math.cos(a), 0))).transposed().to_4x4()
        m.translation = (0, 0, pu["z"])
        g.prism(circle(pu["radius"], 32), pu["r_from"], abs(v["end_x_mm"] / math.sin(a)), m)
    add("pushers", g, "steel_polished", bevel=0.15)

    # ---- five columns from the case ends ----
    br = cfg["bracelet"]
    fc, fp = tr["bracelet_column_fractions"]["centre_half"], tr["bracelet_column_fractions"]["polished_outer"]
    shift, pitch, gap = tr["bracelet_polished_joint_shift_mm"], tr["bracelet_pitch_mm"], br["gap"]
    tip = tr["case_end_mm"]["mean"]
    sil = {round(p[0], 2): p for p in tr["silhouette_y_left_right_mm"]}
    q = lambda y: round(round(y * 4) / 4, 2)
    sil_max = min(max(sil), -min(sil)) - 0.25
    width = lambda y: (sil[q(y)][2] - sil[q(y)][1] + sil[q(-y)][2] - sil[q(-y)][1]) / 4
    hw_at = lambda y: min(width(min(max(y, tip + 1.0), sil_max)), br["max_half_width"])

    def columns(hw):
        cols = [(-fc * hw, fc * hw, "brushed")]
        for s in (1, -1):
            cols += [tuple(sorted((s * (fc * hw + gap), s * (fp * hw)))) + ("polished",),
                     tuple(sorted((s * (fp * hw + gap), s * hw))) + ("brushed",)]
        return cols

    zm = ds * (br["z0"] + br["z1"]) / 2
    box = curl(tip + br["bend_after_tip"], br["bend_radius"], zm)
    za, zb = ds * br["z0"], ds * br["z1"]
    brushed, polished, back = Geo(), Geo(), Geo()
    rows = 0
    for sy in (1, -1):
        for kind, start in (("brushed", tip - br["under_case"]), ("polished", tip - shift)):
            y0 = start
            while y0 < br["end_y"] - 0.5:
                y1 = min((tip if kind == "brushed" and y0 < tip else y0) + pitch - gap, br["end_y"])
                hw = hw_at((y0 + y1) / 2)
                for x0, x1, k in columns(hw):
                    if k == kind:
                        box(brushed if kind == "brushed" else polished, x0, x1, y0, y1, za, zb, sy)
                if kind == "brushed":
                    box(back, -(hw - 0.3), hw - 0.3, y0, y1 + gap, ds * br["backing_z"][0], ds * br["backing_z"][1], sy)
                    rows += 1
                y0 = y1 + gap
    add("bracelet_links", brushed, "steel_brushed", bevel=br["bevel"], polished_bevel=True)
    add("bracelet_links_polished", polished, "steel_polished", bevel=br["bevel"])
    add("bracelet_backing", back, "steel_gap")

    # ---- checks against the anchors ----
    bs = tr["bezel_support_mm"]
    out = {"width": round(bs[2] + bs[6], 3), "lug_to_lug": round(2 * tip, 3)}
    for key, want in cfg["verified_mm"].items():
        assert abs(out[key] - want) < 0.8, "%s %.3f != %.3f" % (key, out[key], want)
    for o in coll.objects:
        o["export_product"] = True
    bpy.context.view_layer.update()
    return {"measured_mm": out, "case_end_y_mm": tip, "bracelet_rows": rows,
            "objects": len(coll.objects), "polygons": sum(len(o.data.polygons) for o in coll.objects if o.type == "MESH")}
