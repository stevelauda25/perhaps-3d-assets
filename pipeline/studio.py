"""Reusable area-light studio and product-relative cameras."""
import bpy
from mathutils import Vector

from .materials import material
from .geometry.box import set_opened


def aim(obj, position, target):
    obj.location = position
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def create(config):
    scene = bpy.context.scene
    studio = bpy.data.collections.new("STUDIO | Cameras and lights")
    scene.collection.children.link(studio)
    world = bpy.data.worlds.new("Studio | Pure black")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = config["studio"]["world_strength"]
    scene.world = world
    target = (0, 0, config["geometry_mm"]["height"] / 2000)
    for spec in config["studio"]["lights"]:
        data = bpy.data.lights.new("Studio | " + spec["name"], "AREA")
        data.energy = spec["power"]
        data.shape = "RECTANGLE"
        data.size, data.size_y = spec["size"]
        obj = bpy.data.objects.new(data.name, data)
        studio.objects.link(obj)
        aim(obj, spec["position"], target)
    mesh = bpy.data.meshes.new("Studio | Ground")
    mesh.from_pydata([(-2, -2, -0.0004), (2, -2, -0.0004), (2, 2, -0.0004), (-2, 2, -0.0004)], [], [(0, 1, 2, 3)])
    floor = bpy.data.objects.new(mesh.name, mesh)
    studio.objects.link(floor)
    floor.data.materials.append(material("Studio | Black ground", {
        "color": config["studio"]["floor_color"], "roughness": config["studio"]["floor_roughness"]}))
    directions = {"hero": (-1.1, -1.5, 0.95), "front": (0, -1, 0), "left": (-1, 0, 0),
                  "right": (1, 0, 0), "top": (0, 0, 1), "rear": (0, 1, 0),
                  "bottom": (0, 0, -1), "opened": (-1.1, -1.8, 1.3)}
    extent = max(config["geometry_mm"][key] for key in ("width", "depth", "height")) / 1000
    for name, direction in directions.items():
        data = bpy.data.cameras.new("CAM | " + name)
        data.type = "PERSP" if name in ("hero", "opened") else "ORTHO"
        data.lens = config["studio"]["camera_lens_mm"]
        data.ortho_scale = extent * config["studio"]["orthographic_margin"]
        data.clip_start, data.clip_end = 0.001, 20
        camera = bpy.data.objects.new(data.name, data)
        studio.objects.link(camera)
        aim(camera, Vector(target) + Vector(direction).normalized() * extent * 4.3, target)
    set_opened(True)
    product = [o for o in bpy.data.objects if o.get("export_product")]
    points = [o.matrix_world @ Vector(corner) for o in product for corner in o.bound_box]
    camera = bpy.data.objects["CAM | opened"]
    center = sum(points, Vector()) / len(points)
    camera.location = center + Vector(directions["opened"]).normalized()
    aim(camera, camera.location, center)
    bpy.context.view_layer.update()
    # Blender computes perspective framing from the actual opened product bounds.
    position, _ = camera.camera_fit_coords(bpy.context.evaluated_depsgraph_get(), [v for p in points for v in p])
    camera.location = center + (position - center) * 1.18
    set_opened(False)
    scene.camera = bpy.data.objects["CAM | hero"]
    return studio
