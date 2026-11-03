"""Stamp the 'perhaps' wordmark into the lid wrap as a continuous depth field (no Boolean cuts).

Params (mm): svg, width_mm, center_z_mm, front_y_mm, depth_mm, shoulder_mm, shoulder_round (fillet fraction, 0.3), floor_color_factor, floor_normal_factor,
floor_roughness_offset, uv_tile_mm, wrap, lid_shell, coarse_mm (0.2), fine_div (4), pad_mm (0.8).

How: the SVG outlines are flattened and a signed distance (inside positive, counters handled by even-odd) is evaluated on a
local grid. Depth = D * cosine S-curve over `shoulder_mm` centred on the outline, so the silhouette stays the SVG outline while
surface and floor both round over. The grid is adaptive: 0.2 mm blocks where the surface is flat (surface or floor), refined
to fine_div x fine_div only within the shoulder band. A rectangular opening is cut in the wrap's front face (planar bisect, no
Boolean) and the patch fills it with identical vertices on the border. The patch shares the wrap's transform and UV rule, and
uses a copy of the substrate material whose colour / grain strength / roughness blend with a per-vertex `press` attribute, so
the texture stays the same material at a different depth.
"""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def flatten(subpaths, scale, cx, cy, zc, n=16):
    """-> (M, 4) segments (x0, z0, x1, z1) in mm, world x / z."""
    import numpy as np
    from pipeline.steps.logo_deboss import polygon
    out = []
    for segs in subpaths:
        pts = [((x - cx) * scale, zc - (y - cy) * scale) for x, y in polygon(segs, n)]
        out += [(a[0], a[1], b[0], b[1]) for a, b in zip(pts, pts[1:] + pts[:1])]
    return np.array(out, dtype=np.float64)


def signed_distance(points, seg):
    """points (N, 2) mm -> signed distance to the outline, inside (even-odd) positive."""
    import numpy as np
    x, z = points[:, 0], points[:, 1]
    best, parity = np.full(len(points), 1e9), np.zeros(len(points), bool)
    for x0, z0, x1, z1 in seg:
        dx, dz = x1 - x0, z1 - z0
        t = np.clip(((x - x0) * dx + (z - z0) * dz) / (dx * dx + dz * dz + 1e-18), 0, 1)
        best = np.minimum(best, np.hypot(x - (x0 + t * dx), z - (z0 + t * dz)))
        if dz != 0:
            hit = ((z0 > z) != (z1 > z)) & (x < x0 + (z - z0) * dx / dz)
            parity ^= hit
    return np.where(parity, best, -best)


def profile(sd, depth, shoulder, rnd=0.3):
    """Stamped cross-section over `shoulder` mm centred on the outline: rounded top corner, straight slope, rounded floor
    corner. rnd = fillet fraction at each end (0 = straight ramp, 0.5 = fully rounded); quadratic fillets joined to a linear slope."""
    import numpy as np
    if shoulder <= 0:
        return np.where(sd > 0, depth, 0.0)
    u = np.clip((sd + shoulder / 2) / shoulder, 0, 1)
    r = max(min(rnd, 0.5), 1e-6)
    m = 1 / (1 - r)
    g = np.where(u < r, m * u * u / (2 * r), np.where(u > 1 - r, 1 - m * (1 - u) ** 2 / (2 * r), m * (u - r / 2)))
    return depth * g


def build_patch(seg, x0, x1, z0, z1, p):
    """Adaptive grid over [x0,x1]x[z0,z1] (mm). Returns (verts xz, depth, quads)."""
    import numpy as np
    c, div, D, S = p["coarse_mm"], p["fine_div"], p["depth_mm"], p["shoulder_mm"]
    nx, nz = int(math.ceil((x1 - x0) / c)), int(math.ceil((z1 - z0) / c))
    gx, gz = x0 + c * np.arange(nx + 1), z0 + c * np.arange(nz + 1)
    X, Z = np.meshgrid(gx, gz, indexing="ij")
    sd = signed_distance(np.stack([X.ravel(), Z.ravel()], 1), seg).reshape(X.shape)
    reach = S / 2 + c * 0.7072  # 1-Lipschitz: a block whose corners are all farther than this is flat everywhere
    near = np.abs(sd) <= reach
    fine_block = np.zeros((nx, nz), bool)
    for dx in (0, 1):
        for dz in (0, 1):
            fine_block |= near[dx:nx + dx, dz:nz + dz]
    index, verts, quads = {}, [], []

    def vid(fi, fj):
        k = (fi, fj)
        if k not in index:
            index[k] = len(verts)
            verts.append(k)
        return index[k]
    for i in range(nx):
        for j in range(nz):
            if fine_block[i, j]:
                for a in range(div):
                    for b in range(div):
                        f0, g0 = i * div + a, j * div + b
                        quads.append((vid(f0, g0), vid(f0 + 1, g0), vid(f0 + 1, g0 + 1), vid(f0, g0 + 1)))
            else:
                quads.append((vid(i * div, j * div), vid((i + 1) * div, j * div), vid((i + 1) * div, (j + 1) * div), vid(i * div, (j + 1) * div)))
    ij = np.array(verts, dtype=np.float64)
    xz = np.stack([x0 + ij[:, 0] * c / div, z0 + ij[:, 1] * c / div], 1)
    return xz, profile(signed_distance(xz, seg), D, S, p.get("shoulder_round", 0.3)), quads


def press_material(substrate, p):
    """Substrate copy: same images / mapping; colour, roughness and grain strength blend with the `press` vertex attribute."""
    m = substrate.copy()
    m.name = substrate.name + " | stamped"
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_type, attr.attribute_name = "GEOMETRY", "press"
    t = attr.outputs["Fac"]

    def lerp(a, b, name):  # a + (b - a) * t  as nodes
        n = nt.nodes.new("ShaderNodeMath"); n.operation = "MULTIPLY_ADD"; n.label = name
        n.inputs[1].default_value, n.inputs[2].default_value = b - a, a
        nt.links.new(t, n.inputs[0])
        return n.outputs[0]
    f, r, k = p.get("floor_color_factor", 1.0), p.get("floor_roughness_offset", 0.0), p.get("floor_normal_factor", 1.0)
    if f != 1.0:
        link = bsdf.inputs["Base Color"].links[0]
        mix = nt.nodes.new("ShaderNodeMix"); mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        nt.links.new(link.from_socket, mix.inputs["A"]); nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
        g = lerp(1.0, f, "stamp colour")
        comb = nt.nodes.new("ShaderNodeCombineColor")
        for ch in ("Red", "Green", "Blue"):
            nt.links.new(g, comb.inputs[ch])
        nt.links.new(comb.outputs[0], mix.inputs["B"])
    if r:
        link = bsdf.inputs["Roughness"].links[0]
        add = nt.nodes.new("ShaderNodeMath"); add.operation = "ADD"
        nt.links.new(link.from_socket, add.inputs[0]); nt.links.new(lerp(0.0, r, "stamp roughness"), add.inputs[1])
        nt.links.new(add.outputs[0], bsdf.inputs["Roughness"])
    if k != 1.0:
        for n in [n for n in nt.nodes if n.type in ("NORMAL_MAP", "BUMP")]:
            base = n.inputs["Strength"].default_value
            nt.links.new(lerp(base, base * k, "stamp grain"), n.inputs["Strength"])
    return m


def run(params):
    import bmesh
    import bpy
    import numpy as np
    from mathutils import Vector
    from pipeline import reference_finish
    from pipeline.steps.logo_deboss import parse_svg
    mm = 0.001
    p = {"coarse_mm": 0.2, "fine_div": 4, "pad_mm": 0.8, **params}
    subpaths = parse_svg((ROOT / p["svg"]).read_text())
    xs = [q[0] for s in subpaths for seg in s for q in seg]
    ys = [q[1] for s in subpaths for seg in s for q in seg]
    scale = p["width_mm"] / (max(xs) - min(xs))  # mm per SVG unit
    cx, cy, zc = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, p["center_z_mm"]
    seg = flatten(subpaths, scale, cx, cy, zc)
    half_w, half_h = p["width_mm"] / 2 + p["pad_mm"], (max(ys) - min(ys)) * scale / 2 + p["pad_mm"]
    x0, x1, z0, z1 = -half_w, half_w, zc - half_h, zc + half_h
    front = p["front_y_mm"]

    old = bpy.data.objects[p["wrap"]]
    collection = old.users_collection[0]
    new, _ = reference_finish.render_wrap(bpy.data.objects[p["lid_shell"]], collection)
    new.name = "NEW wrap"
    slots = list(old.data.materials)
    new.data.materials.clear()
    for m in slots:
        new.data.materials.append(m)
    bpy.context.view_layer.update()
    M = new.matrix_world.copy()
    Mi, R = M.inverted(), M.to_3x3()

    # 1. open a rectangle in the planar front face (planar bisect + face removal; no Boolean)
    bm = bmesh.new()
    bm.from_mesh(new.data)
    for co, no in (((x0, 0, 0), (1, 0, 0)), ((x1, 0, 0), (1, 0, 0)), ((0, 0, z0), (0, 0, 1)), ((0, 0, z1), (0, 0, 1))):
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=Mi @ (Vector(co) * mm + Vector((0, front * mm, 0))),
                               plane_no=(R.transposed() @ Vector(no)).normalized())
    gone = []
    for f in bm.faces:
        c = M @ f.calc_center_median()
        if abs(c.y - front * mm) < 1e-6 and abs((R @ f.normal).y) > 0.999 and x0 * mm < c.x < x1 * mm and z0 * mm < c.z < z1 * mm:
            gone.append(f)
    if not gone:
        raise RuntimeError("front face region not found; check front_y_mm / center_z_mm")
    bmesh.ops.delete(bm, geom=gone, context="FACES")
    bm.to_mesh(new.data)
    bm.free()

    # 2. depth-field patch in the wrap's own local space (same transform, same UV rule)
    xz, depth, quads = build_patch(seg, x0, x1, z0, z1, p)
    world = [Vector((a * mm, (front + d) * mm, b * mm)) for (a, b), d in zip(xz, depth)]
    local = [Mi @ w for w in world]
    mesh = bpy.data.meshes.new("PE wordmark stamp")
    mesh.from_pydata([tuple(v) for v in local], [], quads)
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.attributes.new("press", "FLOAT", "POINT").data.foreach_set("value", (depth / max(p["depth_mm"], 1e-9)).astype(np.float32))
    tile = p["uv_tile_mm"] * mm
    uv = mesh.uv_layers.new(name="PE metric wrap")  # reference_finish.metric_uv rule for front faces: (x, z) in wrap-local metres
    for loop in mesh.loops:
        co = mesh.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (co.x / tile, co.z / tile)
    mesh.materials.append(press_material(slots[0], p))
    patch = bpy.data.objects.new(p["wrap"] + " | stamp", mesh)
    collection.objects.link(patch)
    patch.parent, patch.matrix_basis, patch.matrix_parent_inverse = old.parent, new.matrix_basis.copy(), old.matrix_parent_inverse.copy()

    # 3. wrap shading as before (flat front plane avoids fan normals), UV, weighted normals; replace the old wrap
    for face in new.data.polygons:
        face.use_smooth = True
    new.data.set_sharp_from_angle(angle=0.60)
    for face in new.data.polygons:
        if abs((R @ face.normal).y) > 0.9995 and all(abs((M @ new.data.vertices[i].co).y - front * mm) < 1e-5 for i in face.vertices):
            face.use_smooth = False
    reference_finish.metric_uv(new.data, p["uv_tile_mm"] * mm)
    weighted = new.modifiers.new("Leather wrap surface normals", "WEIGHTED_NORMAL")
    weighted.keep_sharp = True
    parent, inverse = old.parent, old.matrix_parent_inverse.copy()
    bpy.data.objects.remove(old, do_unlink=True)
    new.name = p["wrap"]
    new.parent, new.matrix_parent_inverse = parent, inverse
    fonts = len(bpy.data.fonts)
    for f in list(bpy.data.fonts):
        bpy.data.fonts.remove(f)
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)
    return {"patch_verts": len(mesh.vertices), "patch_quads": len(quads), "segments": int(len(seg)), "mm_per_svg_unit": round(scale, 5),
            "max_depth_mm": round(float(depth.max()), 4), "shoulder_mm": p["shoulder_mm"], "fonts_removed": fonts}
