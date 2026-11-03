"""Blender script: flat-white silhouette of the whole watch from the orthographic front camera at the reference scale (23.77 px/mm).

    blender -b --factory-startup --python pipeline/front_silhouette.py -- BUILD.blend OUT.png

Host side (pipeline/front_compare.py: silhouette_report) compares it with the reference alpha: IoU, and where our outline is outside/inside.
"""
import sys

import bpy
from mathutils import Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
build, out = argv[:2]
S, CENTER, SIZE = 23.7709, (999.0, 882.98), 2000
bpy.ops.wm.open_mainfile(filepath=build, load_ui=False, use_scripts=False)
scene = bpy.context.scene
pose = bpy.data.objects["OMG | pose"]
cx_mm, cy_mm = (SIZE / 2 - CENTER[0]) / S, (CENTER[1] - SIZE / 2) / S
cam_data = bpy.data.cameras.new("SIL")
cam_data.type, cam_data.ortho_scale, cam_data.clip_start, cam_data.clip_end = "ORTHO", SIZE / S / 1000.0, 0.001, 5
cam = bpy.data.objects.new("SIL", cam_data)
scene.collection.objects.link(cam)
loc, rot, _ = (pose.matrix_world @ Matrix(((1, 0, 0, cx_mm), (0, 1, 0, cy_mm), (0, 0, 1, 200.0), (0, 0, 0, 1)))).decompose()
cam.location, cam.rotation_mode, cam.rotation_quaternion = loc, "QUATERNION", rot
scene.camera = cam
for o in bpy.data.objects:
    if o.type in ("MESH", "CURVE", "FONT"):
        o.hide_render = not o.name.startswith("OMG | ") or o.name[6:].startswith(("print_", "bezel_numerals", "dial_print", "minute_track", "hand_", "indices", "subdials", "subhub"))
    elif o.type == "LIGHT":
        o.hide_render = True
scene.render.engine = "BLENDER_WORKBENCH"
sh = scene.display.shading
sh.light, sh.color_type, sh.single_color, sh.show_cavity, sh.show_object_outline = "FLAT", "SINGLE", (1, 1, 1), False, False
scene.view_settings.view_transform, scene.view_settings.look = "Standard", "None"
if scene.world:
    scene.world.use_nodes = False
    scene.world.color = (0, 0, 0)
scene.render.film_transparent = False
scene.render.use_compositing = False
scene.render.resolution_x = scene.render.resolution_y = SIZE
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("SIL", out)
