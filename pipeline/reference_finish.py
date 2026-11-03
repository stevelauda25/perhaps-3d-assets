"""Nonstructural render wraps copied exactly from evaluated, locked surfaces."""
import hashlib
import json
import math
import random
import bpy
from mathutils import Vector
from .finishing import attach, text_object
from .materials import material


def vertex_digest(mesh):
    return hashlib.sha256(json.dumps([list(v.co) for v in mesh.vertices]).encode()).hexdigest()


def metric_uv(mesh, tile):
    uv = mesh.uv_layers.get("PE metric wrap") or mesh.uv_layers.new(name="PE metric wrap")
    width = max(v.co.x for v in mesh.vertices)-min(v.co.x for v in mesh.vertices)
    depth = max(v.co.y for v in mesh.vertices)-min(v.co.y for v in mesh.vertices)
    top = max(v.co.z for v in mesh.vertices)
    for face in mesh.polygons:
        axis = max(range(3), key=lambda i: abs(face.normal[i]))
        for index in face.loop_indices:
            co = mesh.vertices[mesh.loops[index].vertex_index].co
            # All projections share one metric scale; top and vertical wrap panels
            # meet at the same manufactured edge, rather than normalized bounds.
            if axis == 2:
                u, v = co.x, co.y+depth/2+top
            elif axis == 1:
                u, v = co.x if face.normal.y < 0 else -co.x+width+depth, co.z
            else:
                u, v = -co.y-(width+depth)/2 if face.normal.x < 0 else co.y+(width+depth)/2, co.z
            uv.data[index].uv = (u/tile, v/tile)
    return uv.name


def render_wrap(source, collection):
    depsgraph = bpy.context.evaluated_depsgraph_get()
    mesh = bpy.data.meshes.new_from_object(source.evaluated_get(depsgraph), preserve_all_data_layers=True, depsgraph=depsgraph)
    before = vertex_digest(mesh)
    obj = source.copy()
    obj.data = mesh
    obj.name = "PE6 | Continuous "+("lid" if "Lid" in source.name else "base")+" leather wrap"
    obj.modifiers.clear()
    collection.objects.link(obj)
    del obj["export_product"]
    obj["finishing_only"] = True
    obj["approved_surface_source"] = source.name
    # Normals are improved only on this removable appearance layer. No vertex
    # positions, bevel widths or structural normals are edited on the source.
    for face in mesh.polygons:
        face.use_smooth = True
    mesh.set_sharp_from_angle(angle=0.60)
    assert vertex_digest(mesh) == before
    source.hide_render = True
    source.hide_set(True)
    obj.hide_render = False
    obj.hide_set(False)
    return obj, before


def add_stitches(config, canonical, collection):
    s = config["stitching"]
    g = canonical["geometry_mm"]
    w, d, h = (g[k]/1000 for k in ("width", "depth", "height"))
    inset = s["edge_inset_mm"]/1000
    a, b, z = w/2-inset, d/2-inset, h
    paths = [(Vector(p), Vector(q), Vector((0, 0, 1))) for p, q in [
        ((-a,-b,z),(a,-b,z)), ((a,-b,z),(a,b,z)), ((a,b,z),(-a,b,z)), ((-a,b,z),(-a,-b,z))]]
    low = (g["base_front"]+g["reveal"])/1000+0.0015
    for x in (-a, a):
        paths.append((Vector((x,-d/2,low)), Vector((x,-d/2,h-0.0015)), Vector((0,-1,0))))
    data = bpy.data.curves.new("PE6 | Inset leather stitching", "CURVE")
    data.dimensions = "3D"
    data.resolution_u = 4
    data.bevel_depth = s["radius_mm"]/1000
    data.bevel_resolution = 2
    rng = random.Random(96)
    count = 0
    pitch, length = s["pitch_mm"]/1000, s["length_mm"]/1000
    for p, q, normal in paths:
        distance, direction = (q-p).length, (q-p).normalized()
        for i in range(int(distance/pitch)):
            start = p+direction*(i*pitch+(pitch-length)/2+rng.uniform(-0.01,0.01)*pitch)
            spline = data.splines.new("BEZIER")
            spline.bezier_points.add(4)
            for j, point in enumerate(spline.bezier_points):
                f = j/4
                pressure = (s["crown_um"]*math.sin(math.pi*f)**2-s["sink_um"])*1e-6
                point.co = start+direction*(length*f)+normal*pressure
                point.handle_left_type = point.handle_right_type = "AUTO"
                point.radius = 0.2+0.8*math.sin(math.pi*f)
            count += 1
    obj = bpy.data.objects.new(data.name, data)
    collection.objects.link(obj)
    attach(obj, collection, bpy.data.objects["CTRL | Lid lift-off"])
    data.materials.append(material("PE6 | Black waxed thread", {"color":s["color_linear"],"roughness":s["roughness"]}))
    return count


def build(config, canonical, materials):
    collection = bpy.data.collections.get("FINISHING | Private Edition removable details")
    if collection is None:
        collection = bpy.data.collections.new("FINISHING | Private Edition removable details")
        bpy.context.scene.collection.children.link(collection)
    checks = {}
    for name in ("Box | Base shell", "Box | Lid shell"):
        source = bpy.data.objects[name]
        obj, original = render_wrap(source, collection)
        checks[name] = {"evaluated_vertices_sha256": original, "copy_exact_before_stamp": True}
        if "Lid" in name:
            settings = config["branding"]
            font = bpy.data.fonts.load(settings["font"], check_existing=True)
            font.use_fake_user = True
            font.pack()
            front = -canonical["geometry_mm"]["depth"]/2000
            depth = settings["deboss_depth_mm"]/1000
            extension = 0.00015
            cutter = text_object("TEMP | Pressing die", settings, font, front-extension+depth, extension)
            for mat in obj.data.materials:
                cutter.data.materials.append(mat)
            for face in cutter.data.polygons:
                face.material_index = 3
            boolean = obj.modifiers.new("Deboss only in nonstructural leather wrap", "BOOLEAN")
            boolean.operation, boolean.solver, boolean.object = "DIFFERENCE", "EXACT", cutter
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier=boolean.name)
            bpy.data.objects.remove(cutter, do_unlink=True)
            weights = obj.data.attributes.new("bevel_weight_edge", "FLOAT", "EDGE")
            for edge in obj.data.edges:
                coords = [obj.matrix_world @ obj.data.vertices[i].co for i in edge.vertices]
                if all(abs(v.x) < 0.045 and 0.03 < v.z < 0.08 and abs(v.y-front) < 0.00025 for v in coords):
                    weights.data[edge.index].value = 1
            lip = obj.modifiers.new("Soft compressed die lip only", "BEVEL")
            lip.limit_method = "WEIGHT"
            lip.width = settings["edge_radius_mm"]/1000
            lip.segments = 3
            lip.harden_normals = True
        metric_uv(obj.data, config["leather"]["source_maps"]["tile_width_mm"]/1000)
        weighted = obj.modifiers.new("Leather wrap surface normals", "WEIGHTED_NORMAL")
        weighted.keep_sharp = True
        # Local deboss is inward; all silhouette bounds remain those of the master.
        reference = source.evaluated_get(bpy.context.evaluated_depsgraph_get())
        ref_mesh = reference.to_mesh()
        for axis in range(3):
            before = (min(v.co[axis] for v in ref_mesh.vertices), max(v.co[axis] for v in ref_mesh.vertices))
            after = (min(v.co[axis] for v in obj.data.vertices), max(v.co[axis] for v in obj.data.vertices))
            assert all(abs(x-y) < 1e-7 for x,y in zip(before,after)), "Wrap silhouette bounds changed"
        reference.to_mesh_clear()
    count = add_stitches(config, canonical, collection)
    return {"surface_wraps": checks, "stitch_segments": count,
            "canonical_meshes_edited": False, "canonical_shells_retained_hidden_for_wrap_render": True,
            "branding": "Didot provisional; physical blind deboss cut into continuous removable wrap"}
