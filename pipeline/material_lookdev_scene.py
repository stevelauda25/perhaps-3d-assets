"""Builds assets/material-lookdev/material_lookdev_v001.blend (run: python3 -B -m pipeline.material_lookdev_scene).

Metric scene, same colour management / Cycles settings as the packaging scenes (Standard sRGB, 12 bounces).
Samples: a 140 mm flat slab (one box face) and a 70 mm block, both with the production 0.6 mm x4 edge bevel.
Two light sets (neutral softbox, grazing strip) toggled by the `material_lookdev` step; fixed cameras.
"""
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets/material-lookdev/material_lookdev_v001.blend"


def build():
    import bpy
    from mathutils import Vector
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine, s.unit_settings.system = "CYCLES", "METRIC"
    s.view_settings.view_transform, s.view_settings.look, s.view_settings.exposure = "Standard", "None", 0.0
    c = s.cycles
    c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.filter_width = 12, 4, 4, 1.0
    c.use_light_tree, c.sample_clamp_indirect, c.caustics_reflective = True, 10.0, True
    w = bpy.data.worlds.new("Lookdev | Dim neutral"); w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.18, 0.18, 0.18, 1)
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.03
    s.world = w

    def block(name, size, loc):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        o = bpy.context.object; o.name = name; o.scale = size; bpy.ops.object.transform_apply(scale=True)
        b = o.modifiers.new("Manufactured edge radius", "BEVEL"); b.width, b.segments, b.limit_method = 0.0006, 4, "ANGLE"
        o.modifiers.new("Weighted surface normals", "WEIGHTED_NORMAL")
        o.data.materials.append(bpy.data.materials.new(name + " | placeholder"))
        bpy.ops.object.shade_smooth()
        return o
    block("SAMPLE | Flat 140 mm slab", (0.14, 0.14, 0.004), (-0.09, 0, -0.002))
    block("SAMPLE | Bevel block 70 mm", (0.07, 0.07, 0.07), (0.07, 0, 0.035))
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, -0.004))
    g = bpy.context.object; g.name = "Lookdev | Neutral grey ground"
    gm = bpy.data.materials.new("Lookdev | Ground 18% grey"); gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.18, 0.18, 0.18, 1)
    gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    g.data.materials.append(gm)

    def aim(o, target):
        o.rotation_euler = (Vector(target) - o.location).to_track_quat("-Z", "Y").to_euler()

    def light(name, loc, target, size, power):
        d = bpy.data.lights.new(name, "AREA"); d.shape = "RECTANGLE"; d.size, d.size_y, d.energy = *size, power
        o = bpy.data.objects.new(name, d); bpy.context.scene.collection.objects.link(o); o.location = loc; aim(o, target)
    light("LIGHT neutral | Softbox", (-0.25, -0.35, 0.5), (-0.02, 0, 0), (0.6, 0.6), 4.0)
    light("LIGHT neutral | Soft fill", (0.4, -0.3, 0.25), (-0.02, 0, 0), (0.5, 0.5), 0.4)
    light("LIGHT grazing | Low strip", (-0.5, -0.02, 0.04), (-0.02, 0, 0), (0.7, 0.06), 12)

    def camera(name, loc, target, lens):
        d = bpy.data.cameras.new(name); d.lens, d.sensor_width, d.clip_start = lens, 36, 0.01
        o = bpy.data.objects.new(name, d); s.collection.objects.link(o); o.location = loc; aim(o, target)
    camera("CAM | overview", (-0.028, -0.33, 0.28), (-0.028, 0, 0.02), 40)
    camera("CAM | macro_flat", (-0.09, -0.16, 0.12), (-0.09, 0, 0), 100)
    s.camera = bpy.data.objects["CAM | overview"]
    s.render.resolution_x = s.render.resolution_y = 1600
    OUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT), compress=False)


if __name__ == "__main__":
    if "--" in sys.argv:
        build()
    else:
        from .cli import detect_blender
        subprocess.run([detect_blender({}), "-b", "--factory-startup", "--python", __file__, "--", "build"], check=True)
