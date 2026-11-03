"""Simple Principled placeholders; no tier-dependent geometry or final textures."""
import bpy


def material(name, params):
    result = bpy.data.materials.new(name)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*params["color"], 1)
    shader.inputs["Roughness"].default_value = params["roughness"]
    shader.inputs["Metallic"].default_value = params.get("metallic", 0)
    result.diffuse_color = (*params["color"], 1)
    return result


def create_materials(config, tier):
    recipe = config["materials"][tier]
    return {slot: material("Perhaps | " + slot, recipe[slot])
            for slot in ("exterior", "interior", "band", "branding")}
