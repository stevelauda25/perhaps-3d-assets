"""Continuous diagonal lift-off shell. All dimensions are supplied in mm."""
import bmesh
import bpy
from mathutils import Vector


def ring(width, depth, height):
    return [(x, y, height(y)) for x, y in
            [(-width / 2, -depth / 2), (width / 2, -depth / 2),
             (width / 2, depth / 2), (-width / 2, depth / 2)]]


def part(name, rings, collection, parent, materials, bevel, cap=False, outer_slot="exterior"):
    vertices = [v for row in rings for v in row]
    faces, slots = [], []
    for layer in range(len(rings) - 1):
        for i in range(4):
            j = (i + 1) % 4
            faces.append((layer * 4 + i, layer * 4 + j, (layer + 1) * 4 + j, (layer + 1) * 4 + i))
            slots.append(outer_slot if layer == 0 else "interior")
    if cap:
        faces.extend([(3, 2, 1, 0), tuple(range(len(vertices) - 4, len(vertices)))])
        slots.extend([outer_slot, "interior"])
    else:
        last = len(vertices) - 4
        for i in range(4):
            j = (i + 1) % 4
            faces.append((last + i, last + j, j, i))
            slots.append("interior")
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.parent = parent
    # Keep parent translations out of the mesh's closed world-space construction.
    obj.matrix_parent_inverse = parent.matrix_world.inverted()
    keys = list(materials)
    for key in keys:
        mesh.materials.append(materials[key])
    for polygon, slot in zip(mesh.polygons, slots):
        polygon.material_index = keys.index(slot)
    modifier = obj.modifiers.new("Manufactured edge radius", "BEVEL")
    modifier.width = bevel
    modifier.segments = 4
    modifier.harden_normals = True
    normals = obj.modifiers.new("Weighted surface normals", "WEIGHTED_NORMAL")
    normals.keep_sharp = True
    obj["component"] = name
    obj["export_product"] = True
    return obj


def control(name, collection, location=(0, 0, 0)):
    obj = bpy.data.objects.new(name, None)
    collection.objects.link(obj)
    obj.location = location
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = 0.025
    bpy.context.view_layer.update()
    return obj


def build(config, materials):
    g = {key: value / 1000 for key, value in config["geometry_mm"].items()}
    w, d, h, t = (g[key] for key in ("width", "depth", "height", "wall"))
    seam = lambda y: g["base_front"] + (y / d + 0.5) * (g["base_rear"] - g["base_front"])
    constant = lambda value: lambda y: value
    collection = bpy.data.collections.new("PRODUCT | Perhaps canonical box")
    bpy.context.scene.collection.children.link(collection)
    base = control("CTRL | Base", collection)
    lid = control("CTRL | Lid lift-off", collection, (0, 0, h - t / 2))
    lid["opening"] = "Translate upward before moving aside; free removable lid, no hinge"
    lid["safe_lift_mm"] = config["geometry_mm"]["height"] + 20
    base_shell = part("Box | Base shell", [ring(w, d, constant(0)), ring(w, d, seam),
                       ring(w - 2*t, d - 2*t, seam), ring(w - 2*t, d - 2*t, constant(t))],
                      collection, base, materials, g["bevel"], cap=True)
    lid_shell = part("Box | Lid shell", [ring(w, d, constant(h)), ring(w, d, lambda y: seam(y) + g["reveal"]),
                      ring(w - 2*t, d - 2*t, lambda y: seam(y) + g["reveal"]),
                      ring(w - 2*t, d - 2*t, constant(h - t))],
                     collection, lid, materials, g["bevel"], cap=True)
    cw, cd = w - 2*(t + g["collar_clearance"]), d - 2*(t + g["collar_clearance"])
    ct = g["collar_wall"]
    collar = part("Box | Interior collar and reveal", [ring(cw, cd, constant(t)),
                  ring(cw, cd, lambda y: seam(y) + g["reveal"] + g["collar_engagement"]),
                  ring(cw - 2*ct, cd - 2*ct, lambda y: seam(y) + g["reveal"] + g["collar_engagement"]),
                  ring(cw - 2*ct, cd - 2*ct, constant(t))],
                  collection, base, materials, min(g["bevel"], ct / 4), outer_slot="band")
    iw, idepth = cw - 2*ct - 0.0004, cd - 2*ct - 0.0004
    tray = part("Box | Interior tray floor", [ring(iw, idepth, constant(t)),
                ring(iw, idepth, constant(t + g["tray_thickness"]))],
                collection, base, materials, min(g["bevel"], g["tray_thickness"] / 4),
                cap=True, outer_slot="interior")
    # A non-rendering placement guide reserves branding without inventing artwork.
    area = control("GUIDE | Front branding area", collection)
    area.parent = lid
    area.matrix_parent_inverse = lid.matrix_world.inverted()
    area.location = (0, -d/2 - 0.0001, g["base_front"] + g["reveal"] + 0.025)
    area.empty_display_type = "CUBE"
    area.scale = (w * 0.30, 0.0001, 0.009)
    area["purpose"] = "Front lower-lid branding placement; 60% width x 18 mm height; no final logo"
    lid_shell["branding_slot"] = "Perhaps | branding"
    lid_shell["top_surface"] = "Blank; no branding"
    bpy.context.view_layer.update()
    # Bake parent inverses into local coordinates so mesh transforms remain unit/identity.
    for obj in [base_shell, lid_shell, collar, tray]:
        matrix = obj.matrix_world.copy()
        origin = obj.parent.matrix_world.translation
        for vertex in obj.data.vertices:
            vertex.co = matrix @ vertex.co - origin
        obj.matrix_parent_inverse.identity()
        obj.location = (0, 0, 0)
        obj.rotation_euler = (0, 0, 0)
        obj.scale = (1, 1, 1)
    bpy.context.view_layer.update()
    return collection


def set_opened(opened):
    lid = bpy.data.objects["CTRL | Lid lift-off"]
    home = lid.get("home_location")
    if home is None:
        lid["home_location"] = list(lid.location)
        home = lid["home_location"]
    lid.location = Vector(home)
    lid.rotation_euler = (0, 0, 0)
    if opened:
        # Fully clear the fitted collar before presenting the free lid beside the base.
        lid.location += Vector((-0.15, 0.015, 0.17))
        lid.rotation_euler = (0, -0.40, -0.12)
    bpy.context.view_layer.update()
