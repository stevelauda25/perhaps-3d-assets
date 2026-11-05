"""watch_kit: reflection-first studio. Replaces lights with emissive gradient cards + black flags, builds a coloured gradient world
(camera sees a screen-space gradient, reflections see a direction gradient of the same colours), adds cameras and a compositor post chain.

Params: kit_preset (config/presets/watch_kit_*.json), pose (default `OMG | pose`). Needs that pose empty (watch or probe scene); the dial centre is pose @ (0, 0, 8.5) mm.
Why cards and not area lights: steel and glass show what they mirror, so a card with a linear emission ramp becomes the smooth
light-to-dark sweep on curved links/flanks; black flags carve the dark between sweeps. Cards are invisible to the camera and cast no
shadow. Angles: az 0 = dial normal, negative = viewer's left, el up; distance in metres from the dial centre.
"""
import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

from pipeline.studio import aim

ROOT = Path(__file__).resolve().parents[2]


def polar(center, az_deg, el_deg, dist):
    az, el = math.radians(az_deg), math.radians(el_deg)
    return center + Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el))) * dist


def feather_mask(nt, coord, feather):
    """Soft card edges: smooth ramp from each edge of the Generated 0..1 square, multiplied across both axes."""
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Generated"], sep.inputs["Vector"])
    parts = []
    for axis in ("X", "Y"):
        for flip in (False, True):
            r = nt.nodes.new("ShaderNodeMapRange")
            r.clamp, r.interpolation_type = True, "SMOOTHSTEP"
            r.inputs["From Min"].default_value, r.inputs["From Max"].default_value = (1, 1 - feather) if flip else (0, feather)
            r.inputs["To Min"].default_value, r.inputs["To Max"].default_value = 0, 1
            nt.links.new(sep.outputs[axis], r.inputs["Value"])
            parts.append(r.outputs["Result"])
    acc = parts[0]
    for q in parts[1:]:
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        nt.links.new(acc, mul.inputs[0])
        nt.links.new(q, mul.inputs[1])
        acc = mul.outputs["Value"]
    return acc


def emission_material(name, tint, strength=None, axis="y", feather=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em, out = nt.nodes.new("ShaderNodeEmission"), nt.nodes.new("ShaderNodeOutputMaterial")
    em.inputs["Color"].default_value = (*tint, 1)
    if strength is None:  # black flag: absorbs, emits nothing
        em.inputs["Strength"].default_value = 0.0
    else:
        coord, sep, rng = nt.nodes.new("ShaderNodeTexCoord"), nt.nodes.new("ShaderNodeSeparateXYZ"), nt.nodes.new("ShaderNodeMapRange")
        rng.inputs["To Min"].default_value, rng.inputs["To Max"].default_value = strength
        nt.links.new(coord.outputs["Generated"], sep.inputs["Vector"])
        nt.links.new(sep.outputs["Y" if axis == "y" else "X"], rng.inputs["Value"])
        if feather:
            mul = nt.nodes.new("ShaderNodeMath")
            mul.operation = "MULTIPLY"
            nt.links.new(rng.outputs["Result"], mul.inputs[0])
            nt.links.new(feather_mask(nt, coord, feather), mul.inputs[1])
            nt.links.new(mul.outputs["Value"], em.inputs["Strength"])
        else:
            nt.links.new(rng.outputs["Result"], em.inputs["Strength"])
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m


def plane(name, w, h, mat):
    me = bpy.data.meshes.new(name)
    me.from_pydata([(-w / 2, -h / 2, 0), (w / 2, -h / 2, 0), (w / 2, h / 2, 0), (-w / 2, h / 2, 0)], [], [(0, 3, 2, 1)])  # normal -Z: faces the dial after aim()
    me.update()
    me.materials.append(mat)
    return bpy.data.objects.new(name, me)


def set_input(node, name, value):
    try:
        node.inputs[name].default_value = value
    except (KeyError, TypeError, AttributeError):
        pass  # optional socket not present for this glare type / Blender build


def post_chain(scene, post):
    g = bpy.data.node_groups.new("WATCH_KIT | post", "CompositorNodeTree")
    scene.compositing_node_group = g
    g.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    n, link = g.nodes, g.links
    last = n.new("CompositorNodeRLayers").outputs["Image"]

    def chain(node, out="Image"):
        nonlocal last
        link.new(last, node.inputs["Image"])
        last = node.outputs[out]

    if post.get("glow"):
        gl = n.new("CompositorNodeGlare")
        gl.inputs["Type"].default_value = "Fog Glow"
        for k, v in (("Threshold", post["glow"]["threshold"]), ("Strength", post["glow"]["strength"]), ("Smoothness", post["glow"].get("smoothness", 0.5))):
            set_input(gl, k, v)
        chain(gl)
    if post.get("streaks"):
        st = n.new("CompositorNodeGlare")
        st.inputs["Type"].default_value = "Streaks"
        for k, v in (("Threshold", post["streaks"]["threshold"]), ("Strength", post["streaks"]["strength"])):
            set_input(st, k, v)
        chain(st)
    if post.get("grade"):
        cb = n.new("CompositorNodeColorBalance")
        for k, v in post["grade"].items():
            set_input(cb, k, v)
        chain(cb)
    if post.get("vignette"):
        v = post["vignette"]
        mask = n.new("CompositorNodeEllipseMask")
        set_input(mask, "Size", tuple(v["size"]))
        set_input(mask, "Position", (0.5, 0.5))
        blur = n.new("CompositorNodeBlur")
        set_input(blur, "Size", (v.get("soften", 120), v.get("soften", 120)))
        link.new(mask.outputs["Mask"], blur.inputs["Image"])
        ramp = n.new("ShaderNodeMix")
        ramp.data_type = "RGBA"
        ramp.inputs["A"].default_value = (1 - v["amount"],) * 3 + (1,)
        ramp.inputs["B"].default_value = (1, 1, 1, 1)
        link.new(blur.outputs["Image"], ramp.inputs["Factor"])
        mul = n.new("ShaderNodeMix")
        mul.data_type, mul.blend_type = "RGBA", "MULTIPLY"
        mul.inputs["Factor"].default_value = 1.0
        link.new(last, mul.inputs["A"])
        link.new(ramp.outputs["Result"], mul.inputs["B"])
        last = mul.outputs["Result"]
    out = n.new("NodeGroupOutput")
    link.new(last, out.inputs["Image"])
    scene.render.use_compositing = True


def run(params):
    cfg = json.loads((ROOT / params["kit_preset"]).read_text())
    scene, pose = bpy.context.scene, bpy.data.objects[params.get("pose", "OMG | pose")]
    center = pose.matrix_world @ Vector((0, 0, 8.5))
    old = bpy.data.collections.new("WATCH_KIT | previous lights (excluded)")
    scene.collection.children.link(old)
    for o in list(bpy.data.objects):
        if o.type == "LIGHT":
            for c in list(o.users_collection):
                c.objects.unlink(o)
            old.objects.link(o)
    bpy.context.view_layer.layer_collection.children[old.name].exclude = True
    for name in ("Studio | feathered diffusion reflection",) + (("Studio | reflective black ground",) if cfg.get("ground") is False else ()):
        if bpy.data.objects.get(name):
            bpy.data.objects[name].hide_render = True
    rig = bpy.data.collections.new("WATCH_KIT | " + cfg["name"])
    scene.collection.children.link(rig)

    # world: camera sees a screen gradient, reflections see a direction gradient of the same palette
    w = cfg["world"]
    world = bpy.data.worlds.new("WATCH_KIT | gradient world")
    world.use_nodes = True
    nt = world.node_tree
    nt.nodes.clear()
    coord = nt.nodes.new("ShaderNodeTexCoord")
    win_y, dir_z = nt.nodes.new("ShaderNodeSeparateXYZ"), nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(coord.outputs["Window"], win_y.inputs["Vector"])
    nt.links.new(coord.outputs["Generated"], dir_z.inputs["Vector"])
    gamma = nt.nodes.new("ShaderNodeMath")
    gamma.operation = "POWER"
    gamma.inputs[1].default_value = w.get("gamma", 1.0)
    nt.links.new(win_y.outputs["Y"], gamma.inputs[0])
    cam_col = nt.nodes.new("ShaderNodeMix")
    cam_col.data_type = "RGBA"
    cam_col.inputs["A"].default_value, cam_col.inputs["B"].default_value = (*w["bottom"], 1), (*w["top"], 1)
    nt.links.new(gamma.outputs["Value"], cam_col.inputs["Factor"])
    zmap = nt.nodes.new("ShaderNodeMapRange")
    zmap.inputs["From Min"].default_value, zmap.inputs["From Max"].default_value = -1, 1
    nt.links.new(dir_z.outputs["Z"], zmap.inputs["Value"])
    env_col = nt.nodes.new("ShaderNodeMix")
    env_col.data_type = "RGBA"
    env_col.inputs["A"].default_value, env_col.inputs["B"].default_value = (*w["env_bottom"], 1), (*w["env_top"], 1)
    nt.links.new(zmap.outputs["Result"], env_col.inputs["Factor"])
    bg_cam, bg_env = nt.nodes.new("ShaderNodeBackground"), nt.nodes.new("ShaderNodeBackground")
    bg_env.inputs["Strength"].default_value = w.get("env_strength", 1.0)
    nt.links.new(cam_col.outputs["Result"], bg_cam.inputs["Color"])
    nt.links.new(env_col.outputs["Result"], bg_env.inputs["Color"])
    ray, mix, out = nt.nodes.new("ShaderNodeLightPath"), nt.nodes.new("ShaderNodeMixShader"), nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(ray.outputs["Is Camera Ray"], mix.inputs["Fac"])
    nt.links.new(bg_env.outputs["Background"], mix.inputs[1])
    nt.links.new(bg_cam.outputs["Background"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    scene.world = world

    # cards (emissive gradients) and flags (black absorbers)
    def place(spec, strength=None):
        mat = emission_material("WATCH_KIT | " + spec["name"], spec.get("tint", (1, 1, 1)), strength, spec.get("axis", "y"), spec.get("feather", cfg.get("feather", 0.0)))
        o = plane("WATCH_KIT | " + spec["name"], spec["size"][0], spec["size"][1], mat)
        rig.objects.link(o)
        aim(o, polar(center, spec["az_deg"], spec["el_deg"], spec["distance_m"]), center)
        if spec.get("roll_deg"):
            o.rotation_euler.rotate_axis("Z", math.radians(spec["roll_deg"]))
        o.visible_camera = o.visible_shadow = False  # seen only in reflections / as light
        return o
    for spec in cfg["cards"]:
        place(spec, tuple(spec["strength"]))
    for spec in cfg.get("flags", []):
        place(spec, None)

    # cameras
    def registered(name, c):
        """Camera that reproduces a photo's pose (pipeline/ref_register.py JSON): sensor 36 mm, focal from the fit, no depth of field."""
        spec = json.loads((ROOT / c["registered"]).read_text())
        rv = Vector(spec["rvec"])
        angle = rv.length
        R = Matrix.Rotation(angle, 3, rv.normalized()) if angle > 1e-12 else Matrix.Identity(3)
        t = Vector(spec["tvec"])
        C = -(R.transposed() @ t)
        right, down, fwd = R.transposed().col[0], R.transposed().col[1], R.transposed().col[2]
        m = Matrix(((right[0], -down[0], -fwd[0], C[0]), (right[1], -down[1], -fwd[1], C[1]), (right[2], -down[2], -fwd[2], C[2]), (0, 0, 0, 1)))
        loc, rot, _ = (pose.matrix_world @ m).decompose()
        data = bpy.data.cameras.new("CAM | " + name)
        data.sensor_fit, data.sensor_width, data.lens = "HORIZONTAL", 36.0, spec["focal_px"] * 36.0 / spec["size"][0]
        data.clip_start, data.clip_end = 0.005, 5
        o = bpy.data.objects.new(data.name, data)
        rig.objects.link(o)
        o.location, o.rotation_mode, o.rotation_quaternion = loc, "QUATERNION", rot

    def ortho(name, c):
        """Straight-on orthographic camera that reproduces a front reference image: given px/mm, the dial centre's pixel and the image size."""
        o_ = c["ortho"]
        data = bpy.data.cameras.new("CAM | " + name)
        data.type, data.ortho_scale = "ORTHO", o_["size"] / o_["scale_px_per_mm"] / 1000.0  # scene units are metres
        data.clip_start, data.clip_end = 0.001, 5
        cx_mm, cy_mm = (o_["size"] / 2 - o_["center_px"][0]) / o_["scale_px_per_mm"], (o_["center_px"][1] - o_["size"] / 2) / o_["scale_px_per_mm"]
        loc, rot, _ = (pose.matrix_world @ Matrix(((1, 0, 0, cx_mm), (0, 1, 0, cy_mm), (0, 0, 1, 200.0), (0, 0, 0, 1)))).decompose()
        ob = bpy.data.objects.new(data.name, data)
        rig.objects.link(ob)
        ob.location, ob.rotation_mode, ob.rotation_quaternion = loc, "QUATERNION", rot

    for name, c in cfg["cameras"].items():
        if "ortho" in c:
            ortho(name, c)
            continue
        if "registered" in c:
            registered(name, c)
            continue
        data = bpy.data.cameras.new("CAM | " + name)
        data.lens, data.clip_start, data.clip_end = c["lens_mm"], 0.005, 5
        o = bpy.data.objects.new(data.name, data)
        rig.objects.link(o)
        target = pose.matrix_world @ Vector(c["target_local_mm"]) if "target_local_mm" in c else center
        aim(o, polar(target, c["azimuth_deg"], c["elevation_deg"], c["distance_m"]), target)
        if c.get("roll_deg"):
            o.rotation_euler.rotate_axis("Z", math.radians(c["roll_deg"]))
        data.dof.use_dof, data.dof.focus_distance, data.dof.aperture_fstop = True, c["distance_m"], c["fstop"]
    scene.render.engine = "CYCLES"  # empty input scenes default to EEVEE, which cannot mirror emissive cards
    scene.cycles.max_bounces, scene.cycles.filter_width, scene.cycles.use_light_tree = 12, 1.5, True
    cm, v = cfg["color_management"], scene.view_settings
    v.view_transform, v.exposure = cm["view_transform"], cm["exposure"]
    post_chain(scene, cfg.get("post", {}))
    bpy.ops.file.make_paths_relative()
    bpy.context.view_layer.update()
    return {"cards": len(cfg["cards"]), "flags": len(cfg.get("flags", [])), "cameras": sorted(cfg["cameras"]), "post": sorted(cfg.get("post", {}))}
