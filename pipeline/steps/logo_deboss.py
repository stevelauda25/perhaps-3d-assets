"""Re-deboss the 'perhaps' wordmark from the official SVG outlines on the lid leather/paper wrap.

Params (all lengths mm): svg, width_mm, center_z_mm, front_y_mm, depth_mm, lip_radius_mm, lip_segments, lip_profile,
outset_mm (uniform outline growth per side, 0 = exact SVG), uv_tile_mm, wrap, lid_shell, branding_slot.
Replaces only the removable wrap object (same parent/materials/UV); canonical geometry is not touched.
Glyph subpaths are classified into solids and counters; each solid + its counters becomes one filled Bezier curve
(exact outlines, even-odd fill), all cutters are joined and subtracted in one exact boolean.
"""
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def parse_svg(text):
    """-> list of subpaths; each is a list of cubic segments (p0, c1, c2, p1) in SVG units. Absolute M C H V L Z only."""
    subpaths = []
    for d in re.findall(r'\sd="([^"]+)"', text):
        cur = start = None
        segs = None
        for cmd, args in re.findall(r"([MCHVLZ])([^MCHVLZ]*)", d):
            n = [float(v) for v in re.findall(r"-?\d*\.?\d+(?:e-?\d+)?", args)]
            if cmd == "M":
                cur = start = (n[0], n[1]); segs = []
            elif cmd == "C":
                for i in range(0, len(n), 6):
                    p = [(n[i], n[i + 1]), (n[i + 2], n[i + 3]), (n[i + 4], n[i + 5])]
                    segs.append((cur, *p)); cur = p[2]
            elif cmd in "HVL":
                pts = [(n[i], cur[1]) for i in range(len(n))] if cmd == "H" else [(cur[0], n[i]) for i in range(len(n))] if cmd == "V" \
                    else [(n[i], n[i + 1]) for i in range(0, len(n), 2)]
                for p in pts:
                    segs.append((cur, lerp(cur, p, 1 / 3), lerp(cur, p, 2 / 3), p)); cur = p  # line as a cubic with real handles (zero-length handles break curve offset)
            elif cmd == "Z":
                if cur != start:
                    segs.append((cur, lerp(cur, start, 1 / 3), lerp(cur, start, 2 / 3), start))
                subpaths.append(segs); cur = start
    return subpaths


def polygon(segs, n=12):
    pts = []
    for p0, c1, c2, p1 in segs:
        for i in range(n):
            t = i / n
            a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
            pts.append((a * p0[0] + b * c1[0] + c * c2[0] + d * p1[0], a * p0[1] + b * c1[1] + c * c2[1] + d * p1[1]))
    return pts


def inside(pt, poly):
    x, y, hit = pt[0], pt[1], False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def solids_with_holes(subpaths):
    polys = [polygon(s) for s in subpaths]
    hole_of = {}
    for i, p in enumerate(polys):
        for j, q in enumerate(polys):
            if i != j and sum(inside(pt, q) for pt in p) >= 0.9 * len(p):  # fully contained => counter
                hole_of[i] = j
    groups = {i: [] for i in range(len(subpaths)) if i not in hole_of}
    for h, s in hole_of.items():
        groups[s].append(h)
    return [[subpaths[i]] + [subpaths[h] for h in hs] for i, hs in groups.items()]


def pressed_floor(substrate, p):
    """Copy of the substrate material (same images, same texture coordinates) with a little compression:
    multiply colour, roughness offset, scale bump/normal strength. Floors keep the surrounding grain."""
    m = substrate.copy()
    m.name = substrate.name + " | pressed floor"
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    f, r, k = p.get("floor_color_factor", 1.0), p.get("floor_roughness_offset", 0.0), p.get("floor_normal_factor", 1.0)
    if f != 1.0:
        link = bsdf.inputs["Base Color"].links[0]
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
        mix.inputs["Factor"].default_value, mix.inputs["B"].default_value = 1.0, (f, f, f, 1)
        nt.links.new(link.from_socket, mix.inputs["A"]); nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
    if r:
        link = bsdf.inputs["Roughness"].links[0]
        add = nt.nodes.new("ShaderNodeMath"); add.operation = "ADD"; add.inputs[1].default_value = r
        nt.links.new(link.from_socket, add.inputs[0]); nt.links.new(add.outputs[0], bsdf.inputs["Roughness"])
    if k != 1.0:
        for n in nt.nodes:
            if n.type in ("NORMAL_MAP", "BUMP"):
                n.inputs["Strength"].default_value *= k
    if p.get("front_projection", False):
        # Box projection switches axis on tilted shoulders and smears; project from the front (x, z) instead.
        for n in [n for n in nt.nodes if n.type == "TEX_IMAGE" and n.projection == "BOX"]:
            src = n.inputs["Vector"].links[0].from_socket
            sep, com = nt.nodes.new("ShaderNodeSeparateXYZ"), nt.nodes.new("ShaderNodeCombineXYZ")
            nt.links.new(src, sep.inputs[0])
            nt.links.new(sep.outputs["X"], com.inputs["X"]); nt.links.new(sep.outputs["Z"], com.inputs["Y"])
            nt.links.new(com.outputs[0], n.inputs["Vector"])
            n.projection = "FLAT"
    return m


def run(params):
    import bmesh
    import bpy
    from pipeline import reference_finish
    mm = 0.001
    subpaths = parse_svg((ROOT / params["svg"]).read_text())
    xs = [p[0] for s in subpaths for seg in s for p in seg]
    ys = [p[1] for s in subpaths for seg in s for p in seg]
    scale = params["width_mm"] * mm / (max(xs) - min(xs))
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    ext = 0.0005  # cutter half-thickness; it stands 0.5 mm proud of the front plane
    front = params["front_y_mm"] * mm
    old = bpy.data.objects[params["wrap"]]
    collection = old.users_collection[0]

    cutters = []
    for gi, group in enumerate(solids_with_holes(subpaths)):
        curve = bpy.data.curves.new("TEMP wordmark %d" % gi, "CURVE")
        curve.dimensions, curve.fill_mode, curve.resolution_u = "2D", "BOTH", 16
        curve.extrude, curve.offset = ext, params.get("outset_mm", 0) * mm
        for segs in group:
            sp = curve.splines.new("BEZIER")
            sp.use_cyclic_u = True
            sp.bezier_points.add(len(segs) - 1)
            for bp, (p0, c1, c2, p1), prev in zip(sp.bezier_points, segs, [segs[-1]] + segs[:-1]):
                f = lambda p: ((p[0] - cx) * scale, -(p[1] - cy) * scale, 0)  # SVG y is down
                bp.co = f(p0)
                bp.handle_left_type = bp.handle_right_type = "FREE"
                bp.handle_left, bp.handle_right = f(prev[2]), f(c1)
        obj = bpy.data.objects.new("TEMP wordmark %d" % gi, curve)
        bpy.context.scene.collection.objects.link(obj)
        cutters.append(obj)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action="DESELECT")
    for o in cutters:
        o.select_set(True)
    bpy.context.view_layer.objects.active = cutters[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    cutter = bpy.context.view_layer.objects.active
    cutter.name = "TEMP pressing die (SVG)"
    cutter.rotation_euler.x = math.pi / 2
    cutter.location = (0, front - ext + params["depth_mm"] * mm, params["center_z_mm"] * mm)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    slots = list(old.data.materials)
    if "floor_color_factor" in params or params.get("front_projection") or "floor_normal_factor" in params or "floor_roughness_offset" in params:
        slots[params.get("branding_slot", 3)] = pressed_floor(slots[0], params)
    for m in slots:
        cutter.data.materials.append(m)
    for face in cutter.data.polygons:
        face.material_index = params.get("branding_slot", 3)
    zs = [(cutter.matrix_world @ v.co).z for v in cutter.data.vertices]
    xs_w = [(cutter.matrix_world @ v.co).x for v in cutter.data.vertices]

    lid = bpy.data.objects[params["lid_shell"]]
    new, _ = reference_finish.render_wrap(lid, collection)
    new.name = "NEW wrap"
    new.data.materials.clear()
    for m in slots:
        new.data.materials.append(m)
    boolean = new.modifiers.new("Deboss only in nonstructural wrap", "BOOLEAN")
    boolean.operation, boolean.solver, boolean.object = "DIFFERENCE", "EXACT", cutter
    boolean.use_self = True
    bpy.ops.object.select_all(action="DESELECT")
    new.select_set(True)
    bpy.context.view_layer.objects.active = new
    bpy.ops.object.modifier_apply(modifier=boolean.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    for face in new.data.polygons:
        face.use_smooth = True
    new.data.set_sharp_from_angle(angle=0.60)
    pad = 0.003
    if params.get("flat_planes", True):
        # Planar front panel and deboss floors: shade flat so long triangulation slivers cannot fan out vertex normals.
        for face in new.data.polygons:
            if abs((new.matrix_world.to_3x3() @ face.normal).y) > 0.9995:
                face.use_smooth = False
    if params.get("flat_walls", True):
        # Deboss walls are cut into long n-gons; smooth shading across them produces saw-tooth normals, so shade them flat.
        for face in new.data.polygons:
            vs = [new.matrix_world @ new.data.vertices[i].co for i in face.vertices]
            if abs((new.matrix_world.to_3x3() @ face.normal).y) < 0.5 and all(abs(v.y - front) < 0.002 and min(xs_w) - pad < v.x < max(xs_w) + pad and min(zs) - pad < v.z < max(zs) + pad for v in vs):
                face.use_smooth = False
    attr = new.data.attributes.new("bevel_weight_edge", "FLOAT", "EDGE")
    rim = floor_edges = 0
    inner = params.get("inner_radius_mm", 0)
    for edge in new.data.edges:
        co = [new.matrix_world @ new.data.vertices[i].co for i in edge.vertices]
        inbox = all(min(xs_w) - pad < v.x < max(xs_w) + pad and min(zs) - pad < v.z < max(zs) + pad for v in co)
        if inbox and all(abs(v.y - front) < 1e-4 for v in co):
            attr.data[edge.index].value = 1.0
            rim += 1
        elif inbox and inner and all(abs(v.y - (front + params["depth_mm"] * mm)) < 1e-4 for v in co):
            attr.data[edge.index].value = inner / params["lip_radius_mm"]  # bevel width scales with weight
            floor_edges += 1
    if params["lip_radius_mm"] > 0:
        lip = new.modifiers.new("Soft compressed die lip only", "BEVEL")
        lip.limit_method, lip.width = "WEIGHT", params["lip_radius_mm"] * mm
        lip.segments, lip.profile = params.get("lip_segments", 4), params.get("lip_profile", 0.62)
        lip.harden_normals = params.get("lip_harden", True)
        if params.get("shoulder_slot", False):
            lip.material = params.get("branding_slot", 3)
    if params.get("weighted_normals", True):
        weighted = new.modifiers.new("Leather wrap surface normals", "WEIGHTED_NORMAL")
        weighted.keep_sharp = True
    reference_finish.metric_uv(new.data, params["uv_tile_mm"] * mm)
    if params.get("front_uv", True):
        # Floors and walls take the front-plane projection, so texture stays continuous with the surface around the letters
        # (the default per-face dominant-axis projection smears walls and switches axis along curves).
        uv, tile, hi = new.data.uv_layers["PE metric wrap"], params["uv_tile_mm"] * mm, front + params["depth_mm"] * mm + 0.0005
        for face in new.data.polygons:
            vs = [new.matrix_world @ new.data.vertices[i].co for i in face.vertices]
            if all(front - 0.0005 < v.y < hi and min(xs_w) - pad < v.x < max(xs_w) + pad and min(zs) - pad < v.z < max(zs) + pad for v in vs):
                for li in face.loop_indices:
                    co = new.data.vertices[new.data.loops[li].vertex_index].co
                    uv.data[li].uv = (co.x / tile, co.z / tile)

    parent, inverse = old.parent, old.matrix_parent_inverse.copy()
    bpy.data.objects.remove(old, do_unlink=True)
    new.name = params["wrap"]
    new.parent, new.matrix_parent_inverse = parent, inverse
    fonts = len(bpy.data.fonts)
    for f in list(bpy.data.fonts):  # wordmark is geometry now
        bpy.data.fonts.remove(f)
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)
    return {"glyph_solids": len(solids_with_holes(subpaths)), "subpaths": len(subpaths), "rim_edges_weighted": rim, "floor_edges_weighted": floor_edges, "faces": len(new.data.polygons),
            "mm_per_svg_unit": round(scale / mm, 5), "outset_mm": params.get("outset_mm", 0), "depth_mm": params["depth_mm"], "fonts_removed": fonts}
