"""Blender-side executor for one job stage. Launched only by pipeline.jobs.

Scene stage: open input → run pipeline.steps.<step>.run(params) → verify geometry lock → save.
Render stage: open scene read-only → apply quality profile → render one view → PNG (+EXR).
Look settings (view transform, exposure, bounces, filter, lights) always come from the
saved scene; a render profile only controls sampling, resolution and output files.
"""
import hashlib
import importlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))


def loaded_code():
    """Hash every project module this process imported, so the host can detect code changes."""
    result = {}
    for module in list(sys.modules.values()):
        path = Path(getattr(module, "__file__", None) or "/").resolve()
        if ROOT / "pipeline" in path.parents and path.suffix == ".py":
            result[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def use_metal():
    import bpy
    prefs = bpy.context.preferences.addons["cycles"].preferences
    prefs.compute_device_type = "METAL"
    prefs.get_devices()
    metal = [d for d in prefs.devices if d.type == "METAL"]
    if not metal:
        raise RuntimeError("Metal GPU unavailable; refusing silent CPU fallback")
    for d in prefs.devices:
        d.use = d.type == "METAL"
    bpy.context.scene.cycles.device = "GPU"
    return [d.name for d in metal]


def render(spec, profile, out_dir):
    import bpy
    from pipeline.studio import aim
    scene, r = bpy.context.scene, spec["render"]
    devices = use_metal()
    camera = bpy.data.objects[r["camera"]]
    if "camera_override" in r:
        # Unsaved copy: approved presets stay untouched even in memory.
        o = r["camera_override"]
        camera = camera.copy(); camera.data = camera.data.copy(); camera.name = "CAM | job override"
        scene.collection.objects.link(camera)
        if "lens_mm" in o:
            camera.data.lens = o["lens_mm"]
        aim(camera, o["position"], o["target"])
    scene.camera = camera
    c = scene.cycles
    c.samples, c.adaptive_threshold = profile["samples"], profile["adaptive_threshold"]
    c.use_adaptive_sampling, c.use_denoising, c.seed = True, profile["denoise"], 42
    scene.render.resolution_x = r["resolution"]
    scene.render.resolution_y = round(r["resolution"] * r.get("aspect_h_over_w", 1))  # e.g. 1.25 = 4:5 portrait
    scene.render.resolution_percentage = round(profile["scale"] * 100)
    border = r.get("border")
    if profile.get("border_required") and not border:
        raise ValueError("Profile requires a render border [xmin,xmax,ymin,ymax]")
    scene.render.use_border = bool(border)
    scene.render.use_crop_to_border = bool(border)
    if border:
        (scene.render.border_min_x, scene.render.border_max_x,
         scene.render.border_min_y, scene.render.border_max_y) = border
    start = time.monotonic()
    bpy.ops.render.render(write_still=False)
    seconds = round(time.monotonic() - start, 3)
    image, settings = bpy.data.images["Render Result"], scene.render.image_settings
    outputs = []
    if profile["exr"]:
        settings.file_format, settings.color_depth, settings.exr_codec = "OPEN_EXR", "16", "ZIP"
        image.save_render(str(out_dir / (spec["name"] + ".exr")), scene=scene)
        outputs.append(spec["name"] + ".exr")
    settings.file_format, settings.color_mode, settings.color_depth = "PNG", "RGB", "16"
    image.save_render(str(out_dir / (spec["name"] + ".png")), scene=scene)
    outputs.append(spec["name"] + ".png")
    v = scene.view_settings
    return {"render_seconds": seconds, "outputs": outputs, "devices": devices,
            "settings": {"camera": camera.name, "resolution": r["resolution"],
                         "percentage": scene.render.resolution_percentage, "border": border,
                         "samples": c.samples, "adaptive_threshold": round(c.adaptive_threshold, 5),
                         "denoise": c.use_denoising, "bounces": c.max_bounces, "light_tree": c.use_light_tree,
                         "filter_width": c.filter_width, "view_transform": v.view_transform,
                         "look": v.look, "exposure": round(v.exposure, 4)}}


def main(task_path):
    import bpy
    task = json.loads(Path(task_path).read_text())
    spec, out_dir = task["stage"], Path(task["out_dir"])
    bpy.ops.wm.open_mainfile(filepath=task["input"], load_ui=False, use_scripts=False)
    result = {}
    lock = json.loads(Path(task["geometry_lock"]).read_text())["protected"] if task.get("geometry_lock") else None
    if lock:
        from pipeline import locked
        result["lock_before"] = locked.verify(lock)
    if "render" in spec:
        result.update(render(spec, task["profile"], out_dir))
    else:
        step = importlib.import_module("pipeline.steps." + spec["step"])
        result["summary"] = step.run(spec.get("params", {}))
        if lock:
            result["lock_after"] = locked.verify(lock)  # raises if canonical data moved
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(out_dir / (spec["name"] + ".blend")), compress=False)
        result["outputs"] = [spec["name"] + ".blend"]
        if isinstance(result["summary"], dict):  # files a step wrote into the job folder (e.g. an exported GLB)
            result["outputs"] += result["summary"].get("outputs", [])
    result["code"] = loaded_code()
    Path(task["result"]).write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1])
