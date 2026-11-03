"""Replace lighting independently while retaining every approved camera preset."""
import bpy
from .materials import material
from .studio import aim


def apply(config, settings):
    scene = bpy.context.scene
    for obj in bpy.data.objects:
        if obj.type == "LIGHT":
            obj.hide_render = True
    collection = bpy.data.collections.new("STUDIO | Private Edition softboxes")
    scene.collection.children.link(collection)
    for spec in settings["lights"]:
        data = bpy.data.lights.new("PE light | " + spec["name"], "AREA")
        data.energy = spec["power"]
        data.shape = "RECTANGLE"
        data.size, data.size_y = spec["size"]
        obj = bpy.data.objects.new(data.name, data)
        collection.objects.link(obj)
        aim(obj, spec["position"], spec["target"])
    world = bpy.data.worlds.new("PE | Black studio world")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0
    scene.world = world
    floor = material("PE | Black studio floor", {"color": settings["floor_color"], "roughness": settings["floor_roughness"]})
    floor.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = settings["floor_specular_level"]
    bpy.data.objects["Studio | Ground"].data.materials[0] = floor
    for name, spec in config["macros"].items():
        if bpy.data.objects.get("CAM | "+name):
            continue
        data = bpy.data.cameras.new("CAM | " + name)
        data.type = "ORTHO"
        data.ortho_scale = spec["ortho_scale_mm"]/1000
        data.clip_start, data.clip_end = 0.001, 10
        obj = bpy.data.objects.new(data.name, data)
        collection.objects.link(obj)
        aim(obj, spec["position"], spec["target"])
