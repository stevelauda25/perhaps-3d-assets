"""Isolated wrap skin, physical deboss, and fine stitching; never edits canonical meshes."""
import math
import random
import bmesh
import bpy
from mathutils import Vector

from .materials import material


def attach(obj, collection, parent):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)
    obj.parent = parent
    obj.matrix_parent_inverse = parent.matrix_world.inverted()
    obj["finishing_only"] = True


def text_object(name, settings, font, y, extrusion):
    data = bpy.data.curves.new(name, "FONT")
    data.body = settings["text"]
    data.font = font
    data.size = 0.025
    data.align_x = "CENTER"
    data.resolution_u = 16
    data.fill_mode = "BOTH"
    data.extrude = extrusion
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.update()
    factor = settings["width_mm"]/1000/obj.dimensions.x
    obj.scale = (factor, factor, 1)
    obj.rotation_euler.x = math.pi/2
    obj.location = (0, y, settings["center_z_mm"]/1000)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    # Center the visible outline, independent of font baseline metrics.
    zs = [v.co.z for v in obj.data.vertices]
    middle = (min(zs)+max(zs))/2
    for v in obj.data.vertices:
        v.co.z -= middle
    return obj


def build(config, canonical_config, materials):
    g = canonical_config["geometry_mm"]
    w, d, h, bevel = (g[k]/1000 for k in ("width", "depth", "height", "bevel"))
    bottom = (g["base_front"]+g["reveal"])/1000
    lid = bpy.data.objects["CTRL | Lid lift-off"]
    collection = bpy.data.collections.get("FINISHING | Private Edition removable details")
    if collection is None:
        collection = bpy.data.collections.new("FINISHING | Private Edition removable details")
        bpy.context.scene.collection.children.link(collection)
    settings = config["branding"]
    font = bpy.data.fonts.load(settings["font"], check_existing=True)
    font.use_fake_user = True
    font.pack()
    front = -d/2
    relief = settings["deboss_depth_mm"]/1000
    inset = bevel + settings.get("edge_clearance_mm", 0.3)/1000
    panel_height = h-bottom-2*inset
    mesh = bpy.data.meshes.new("PE | Deboss wrap skin")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    for vertex in bm.verts:
        vertex.co.x *= w-2*inset
        vertex.co.y = vertex.co.y*(relief+0.00001)+front-(relief-0.00001)/2
        vertex.co.z = vertex.co.z*panel_height+(h+bottom)/2
    bm.to_mesh(mesh)
    bm.free()
    panel = bpy.data.objects.new(mesh.name, mesh)
    collection.objects.link(panel)
    panel.data.materials.append(materials["lid"])
    attach(panel, collection, lid)
    cutter = text_object("TEMP | Deboss cutter", settings, font, front-relief/2, 0.001)
    boolean = panel.modifiers.new("Physical wordmark recess - finish skin only", "BOOLEAN")
    boolean.operation = "DIFFERENCE"
    boolean.solver = "EXACT"
    boolean.object = cutter
    bpy.ops.object.select_all(action="DESELECT")
    panel.select_set(True)
    bpy.context.view_layer.objects.active = panel
    bpy.ops.object.modifier_apply(modifier=boolean.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    edge = panel.modifiers.new("Pressed leather lip radius", "BEVEL")
    edge.width = settings["edge_radius_mm"]/1000
    edge.segments = 3
    panel.modifiers.new("Finishing normals", "WEIGHTED_NORMAL")
    letters = text_object("PE | Recessed perhaps letter floors", settings, font, front-0.000001, 0)
    letters.data.materials.append(materials["pressed"])
    attach(letters, collection, lid)
    panel["deboss_depth_mm"] = settings["deboss_depth_mm"]
    panel["construction"] = "Separate sub-0.1 mm wrap skin above locked front face; original shell is the recess support"
    letters["typography"] = settings["font_description"]

    stitch = config["stitching"]
    data = bpy.data.curves.new("PE | Fine saddle stitches", "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 6 if stitch.get("seated", False) else 1
    data.bevel_depth = stitch["radius_mm"]/1000
    data.bevel_resolution = 2
    offset, pitch, length = (stitch[k]/1000 for k in ("edge_inset_mm", "pitch_mm", "length_mm"))
    paths = []
    topz = h + 0.000008
    a, b = w/2-offset, d/2-offset
    for p, q in [((-a, -b, topz), (a, -b, topz)), ((a, -b, topz), (a, b, topz)),
                 ((a, b, topz), (-a, b, topz)), ((-a, b, topz), (-a, -b, topz))]:
        paths.append((Vector(p), Vector(q), Vector((0, 0, 1))))
    for x in (-w/2+offset, w/2-offset):
        paths.append((Vector((x, front-relief-0.000005, bottom+0.002)),
                      Vector((x, front-relief-0.000005, h-0.002)), Vector((0, -1, 0))))
    for y, seam in [(-d/2+offset, bottom), (d/2-offset, (g["base_rear"]+g["reveal"])/1000)]:
        paths.append((Vector((-w/2-0.000008, y, seam+0.002)),
                      Vector((-w/2-0.000008, y, h-0.002)), Vector((-1, 0, 0))))
    count = 0
    rng = random.Random(71)
    for p, q, normal in paths:
        direction = (q-p).normalized()
        distance = (q-p).length
        for i in range(int(distance/pitch)):
            actual_length = length*(1+rng.uniform(-0.04, 0.04))
            start = p + direction*(i*pitch+(pitch-actual_length)/2+rng.uniform(-0.018, 0.018)*pitch)
            if stitch.get("seated", False):
                spline = data.splines.new("BEZIER")
                spline.bezier_points.add(4)
                for j, point in enumerate(spline.bezier_points):
                    f = j/4
                    height = (stitch["crown_um"]*math.sin(math.pi*f)**2-stitch["sink_um"])*1e-6
                    point.co = start+direction*(actual_length*f)+normal*height
                    point.handle_left_type = point.handle_right_type = "AUTO"
                    point.radius = 0.25+0.75*math.sin(math.pi*f)
            else:
                spline = data.splines.new("POLY")
                spline.points.add(2)
                for point, co in zip(spline.points, (start, start+direction*length/2+normal*0.000012, start+direction*length)):
                    point.co = (*co, 1)
            count += 1
    obj = bpy.data.objects.new(data.name, data)
    collection.objects.link(obj)
    attach(obj, collection, lid)
    data.materials.append(material("PE | Dark matching stitch thread", {
        "color": stitch["color_linear"], "roughness": stitch["roughness"]}))
    return {"font": font.name, "font_resource": settings["font"], "deboss_depth_mm": settings["deboss_depth_mm"],
            "stitch_segments": count, "finishing_collection": collection.name,
            "canonical_geometry_edited": False}
