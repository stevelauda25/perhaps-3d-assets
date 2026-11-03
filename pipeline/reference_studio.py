"""Reference cameras and reflection-source studio; approved cameras stay untouched."""
import bpy
import math
from .studio import aim


def cameras(config):
    collection = bpy.data.collections.new("STUDIO | Reference photographic cameras")
    bpy.context.scene.collection.children.link(collection)
    specs = {"reference_hero": config["reference_camera"], **config["macros"]}
    for name, spec in specs.items():
        if bpy.data.objects.get("CAM | "+name):
            raise RuntimeError("Reference camera already exists; use a new camera name/version")
        data = bpy.data.cameras.new("CAM | "+name)
        data.type = "PERSP" if name == "reference_hero" else "ORTHO"
        data.lens = spec.get("lens_mm", 100)
        data.sensor_width = 36
        data.clip_start, data.clip_end = 0.001, 20
        if data.type == "ORTHO":
            data.ortho_scale = spec["ortho_scale_mm"]/1000
        obj = bpy.data.objects.new(data.name, data)
        collection.objects.link(obj)
        aim(obj, spec["position"], spec["target"])


def apply(settings):
    scene = bpy.context.scene
    for obj in bpy.data.objects:
        if obj.type == "LIGHT" or obj.get("photography_source"):
            obj.hide_render = True
    collection = bpy.data.collections.new("STUDIO | Reflection softboxes")
    scene.collection.children.link(collection)
    for spec in settings["lights"]:
        width, height = spec["size"]
        data = bpy.data.meshes.new("PE6 | "+spec["name"])
        data.from_pydata([(-width/2,-height/2,0),(-width/2,height/2,0),
                          (width/2,height/2,0),(width/2,-height/2,0)], [], [(0,1,2,3)])
        uv = data.uv_layers.new(name="Diffuser UV")
        for item, value in zip(uv.data, [(0,0),(0,1),(1,1),(1,0)]):
            item.uv = value
        obj = bpy.data.objects.new(data.name, data)
        collection.objects.link(obj)
        aim(obj, spec["position"], spec["target"])
        obj.visible_camera = False
        obj["photography_source"] = True
        source = bpy.data.materials.new(spec["name"]+" | fixed silk diffuser falloff")
        source.use_nodes = True
        nodes, links = source.node_tree.nodes, source.node_tree.links
        nodes.clear()
        coordinates = nodes.new("ShaderNodeTexCoord")
        split = nodes.new("ShaderNodeSeparateXYZ")
        links.new(coordinates.outputs["UV"], split.inputs[0])
        profiles = []
        for axis in ("X", "Y"):
            angle = nodes.new("ShaderNodeMath"); angle.operation = "MULTIPLY"
            links.new(split.outputs[axis], angle.inputs[0]); angle.inputs[1].default_value = math.pi
            sine = nodes.new("ShaderNodeMath"); sine.operation = "SINE"; sine.use_clamp = True
            links.new(angle.outputs[0], sine.inputs[0])
            soft = nodes.new("ShaderNodeMath"); soft.operation = "POWER"
            links.new(sine.outputs[0], soft.inputs[0]); soft.inputs[1].default_value = 0.65
            profiles.append(soft.outputs[0])
        product = nodes.new("ShaderNodeMath"); product.operation = "MULTIPLY"
        for i, value in enumerate(profiles): links.new(value, product.inputs[i])
        energy = nodes.new("ShaderNodeMath"); energy.operation = "MULTIPLY"
        links.new(product.outputs[0], energy.inputs[0])
        energy.inputs[1].default_value = 2*spec["power"]/(width*height*math.pi)
        emission = nodes.new("ShaderNodeEmission")
        links.new(energy.outputs[0], emission.inputs["Strength"])
        output = nodes.new("ShaderNodeOutputMaterial")
        links.new(emission.outputs[0], output.inputs["Surface"])
        data.materials.append(source)
    world = bpy.data.worlds.new("PE6 | Pure black studio")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0,0,0,1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0
    scene.world = world
    floor = bpy.data.materials.new("PE6 | Matte black photography floor")
    floor.use_nodes = True
    nodes, links = floor.node_tree.nodes, floor.node_tree.links
    nodes.clear()
    diffuse = nodes.new("ShaderNodeBsdfDiffuse")
    diffuse.inputs["Color"].default_value = (*settings["floor_color"],1)
    diffuse.inputs["Roughness"].default_value = 1
    glossy = nodes.new("ShaderNodeBsdfAnisotropic")
    glossy.inputs["Color"].default_value = (0.02,0.02,0.02,1)
    glossy.inputs["Roughness"].default_value = 0.35
    mix = nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = settings["floor_reflection_fraction"]
    links.new(diffuse.outputs[0],mix.inputs[1])
    links.new(glossy.outputs[0],mix.inputs[2])
    output = nodes.new("ShaderNodeOutputMaterial")
    links.new(mix.outputs[0],output.inputs["Surface"])
    bpy.data.objects["Studio | Ground"].data.materials[0] = floor


def refine(settings):
    """Reposition/feather the existing reflection sources, retaining the rig."""
    changes = {}
    for spec in settings["lights"]:
        obj = bpy.data.objects["PE6 | "+spec["name"]]
        if not obj.get("photography_source") or obj.hide_render:
            raise ValueError("Expected active existing photographic source: "+obj.name)
        width = max(v.co.x for v in obj.data.vertices)-min(v.co.x for v in obj.data.vertices)
        height = max(v.co.y for v in obj.data.vertices)-min(v.co.y for v in obj.data.vertices)
        for vertex in obj.data.vertices:
            vertex.co.x *= spec["size"][0]/width
            vertex.co.y *= spec["size"][1]/height
        obj.data.update()
        aim(obj, spec["position"], spec["target"])
        emission = next(n for n in obj.data.materials[0].node_tree.nodes if n.type == "EMISSION")
        energy = emission.inputs["Strength"].links[0].from_node
        if energy.type != "MATH" or energy.operation != "MULTIPLY":
            raise ValueError("Unexpected silk diffuser energy graph")
        energy.inputs[1].default_value = 2*spec["power"]/(spec["size"][0]*spec["size"][1]*math.pi)
        changes[obj.name] = spec
    return changes
