"""box_logo_stamp: stamp the 'perhaps' wordmark into the -y face of a built box part (logo_stamp's depth field, any mesh).

Params (mm): object, svg, width_mm, center_x_mm (0), center_z_mm, front_y_mm, depth_mm, shoulder_mm, shoulder_round,
floor_color_factor, floor_normal_factor, coarse_mm (0.2), fine_div (4), pad_mm (0.8), uv (metric UV map name).
A rectangle is cut out of the planar front face (bisect, no Boolean) and filled by a child patch `<object> | stamp` with the
same transform, so it shares object-space texture coordinates, follows the part's animation and exports with it.
The patch uses `<exterior> | stamped`: the part's first material with colour / grain blended by the `press` attribute.
"""
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run(params):
    import bmesh
    import bpy
    import numpy as np
    from mathutils import Matrix, Vector
    from pipeline.steps.logo_deboss import parse_svg
    from pipeline.steps.logo_stamp import build_patch, flatten, press_material
    mm = 0.001
    p = {"coarse_mm": 0.2, "fine_div": 4, "pad_mm": 0.8, "center_x_mm": 0.0, **params}
    subpaths = parse_svg((ROOT / p["svg"]).read_text())
    xs = [q[0] for s in subpaths for seg in s for q in seg]
    ys = [q[1] for s in subpaths for seg in s for q in seg]
    scale = p["width_mm"] / (max(xs) - min(xs))
    cx0, zc = p["center_x_mm"], p["center_z_mm"]
    seg = flatten(subpaths, scale, (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, zc)
    seg[:, [0, 2]] += cx0
    half_w, half_h = p["width_mm"] / 2 + p["pad_mm"], (max(ys) - min(ys)) * scale / 2 + p["pad_mm"]
    c = p["coarse_mm"]  # build_patch grids whole coarse blocks: size the cut to match, or the patch overlaps the face
    x0, z0 = cx0 - half_w, zc - half_h
    x1, z1 = x0 + c * math.ceil(2 * half_w / c), z0 + c * math.ceil(2 * half_h / c)
    front = p["front_y_mm"]

    part = bpy.data.objects[p["object"]]
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    M = part.matrix_world.copy()
    Mi, R = M.inverted(), M.to_3x3()
    bm = bmesh.new()
    bm.from_mesh(part.data)
    for co, no in (((x0, 0, 0), (1, 0, 0)), ((x1, 0, 0), (1, 0, 0)), ((0, 0, z0), (0, 0, 1)), ((0, 0, z1), (0, 0, 1))):
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
                               plane_co=Mi @ (Vector(co) * mm + Vector((0, front * mm, 0))), plane_no=(R.transposed() @ Vector(no)).normalized())
    gone = [f for f in bm.faces if (lambda c: abs(c.y - front * mm) < 1e-6 and (R @ f.normal).y < -0.999
                                    and x0 * mm < c.x < x1 * mm and z0 * mm < c.z < z1 * mm)(M @ f.calc_center_median())]
    assert gone, "%s: no front face at y = %s mm inside the logo rectangle" % (part.name, front)
    bmesh.ops.delete(bm, geom=gone, context="FACES")
    bm.to_mesh(part.data)
    bm.free()

    xz, depth, quads = build_patch(seg, x0, x1, z0, z1, p)
    local = [Mi @ Vector((a * mm, (front + d) * mm, b * mm)) for (a, b), d in zip(xz, depth)]
    mesh = bpy.data.meshes.new(part.name + " | stamp")
    mesh.from_pydata([tuple(v) for v in local], [], quads)  # (x, z) counter-clockwise: faces -y like the front face
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.attributes.new("press", "FLOAT", "POINT").data.foreach_set("value", (depth / p["depth_mm"]).astype(np.float32))
    uv = mesh.uv_layers.new(name=p["uv"])  # the build's metric rule for a y-facing face: (x, z) in world metres
    for loop in mesh.loops:
        a, b = xz[loop.vertex_index]
        uv.data[loop.index].uv = (a * mm, b * mm)
    mesh.materials.append(press_material(part.material_slots[0].material, p))
    patch = bpy.data.objects.new(part.name + " | stamp", mesh)
    for c in part.users_collection:
        c.objects.link(patch)
    patch.parent, patch.matrix_parent_inverse, patch.matrix_basis = part, Matrix.Identity(4), Matrix.Identity(4)
    if part.get("export_product"):
        patch["export_product"] = True
    normals = [(R @ f.normal).y for f in mesh.polygons]
    assert sum(n < 0 for n in normals) > 0.9 * len(normals), "stamp faces point inward"
    return {"object": part.name, "patch_verts": len(mesh.vertices), "patch_quads": len(quads), "faces_cut": len(gone),
            "max_depth_mm": round(float(depth.max()), 4), "material": mesh.materials[0].name}
