"""Blender script: render the model's case silhouette from a registered photo's camera (pipeline/ref_register.py output).

    blender -b --factory-startup --python pipeline/ref_overlay.py -- BUILD.blend POSE.json OUT_MASK.png [--parts case,lug,guard,bezel,crystal,crown,pusher]

Workbench flat white on black at the photo's resolution; the host side overlays the outline on the photo. Measurement aid, not a render.
"""
import json
import sys

import bpy
from mathutils import Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
build, pose_json, out = argv[:3]
parts = argv[argv.index("--parts") + 1].split(",") if "--parts" in argv else ["case", "lug", "crown_guard", "bezel", "crystal", "crown", "pusher", "medallion"]
spec = json.load(open(pose_json))
bpy.ops.wm.open_mainfile(filepath=build, load_ui=False, use_scripts=False)
scene = bpy.context.scene
pose = bpy.data.objects["OMG | pose"]
import numpy as np
rv = np.array(spec["rvec"]); tv = np.array(spec["tvec"])
angle = float(np.linalg.norm(rv))
R = np.array(Matrix.Rotation(angle, 3, Vector(rv / angle))) if angle > 1e-12 else np.eye(3)  # Rodrigues (no OpenCV in Blender)
C = -R.T @ tv                                   # camera centre in model space (mm)
right, down, fwd = R.T[:, 0], R.T[:, 1], R.T[:, 2]
m = Matrix(((right[0], -down[0], -fwd[0], C[0]), (right[1], -down[1], -fwd[1], C[1]), (right[2], -down[2], -fwd[2], C[2]), (0, 0, 0, 1)))
loc, rot, _ = (pose.matrix_world @ m).decompose()
cam_data = bpy.data.cameras.new("REG")
cam_data.sensor_fit, cam_data.sensor_width = "HORIZONTAL", 36.0
cam_data.lens = spec["focal_px"] * 36.0 / spec["size"][0]
cam_data.clip_start, cam_data.clip_end = 0.01, 5
cam = bpy.data.objects.new("REG", cam_data)
scene.collection.objects.link(cam)
cam.location, cam.rotation_mode, cam.rotation_quaternion = loc, "QUATERNION", rot
scene.camera = cam
for o in bpy.data.objects:
    if o.type in ("MESH", "CURVE", "FONT"):
        keep = o.name.startswith("OMG | ") and any(o.name[6:].startswith(p) for p in parts)
        o.hide_render = not keep
    elif o.type == "LIGHT":
        o.hide_render = True
scene.render.engine = "BLENDER_WORKBENCH"
sh = scene.display.shading
sh.light, sh.color_type, sh.single_color, sh.show_cavity, sh.show_object_outline = "FLAT", "SINGLE", (1, 1, 1), False, False
scene.view_settings.view_transform = "Standard"
scene.view_settings.look = "None"
scene.render.film_transparent = False
if scene.world:
    scene.world.use_nodes = False
    scene.world.color = (0, 0, 0)
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = spec["size"][0], spec["size"][1], 100
scene.render.use_compositing = False
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("OVERLAY", out, round(cam_data.lens, 1))
