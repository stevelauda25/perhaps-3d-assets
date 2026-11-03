"""Explicit device selection and reusable preview/final render profiles."""
import bpy

from .geometry.box import set_opened


def configure(config, preset, device, emit):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    selected, devices = "CPU", []
    if device != "cpu":
        try:
            prefs.compute_device_type = "METAL"
            prefs.get_devices()
            devices = [{"name": d.name, "type": d.type} for d in prefs.devices]
            available = [d for d in prefs.devices if d.type == "METAL"]
            for d in prefs.devices:
                d.use = d.type == "METAL"
            if not available:
                raise RuntimeError("No Metal GPU found")
            selected = "GPU"
        except Exception as exc:
            if device == "metal":
                raise RuntimeError("Requested Metal backend unavailable") from exc
            emit("device_fallback", reason=str(exc))
    scene.cycles.device = selected
    profile = config["presets"][preset]
    scene.cycles.samples = profile["samples"]
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.adaptive_threshold = profile["adaptive_threshold"]
    scene.cycles.use_denoising = profile["denoise"]
    scene.cycles.seed = 42
    scene.cycles.max_bounces = 8
    scene.render.resolution_x = scene.render.resolution_y = profile["resolution"]
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = profile["bit_depth"]
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0
    emit("render_configuration", backend="METAL" if selected == "GPU" else "CPU", devices=devices,
         preset=preset, resolution=profile["resolution"], samples=profile["samples"])


def render_views(views, output, emit):
    import time
    scene = bpy.context.scene
    ground = bpy.data.objects["Studio | Ground"]
    for name in views:
        set_opened(name == "opened")
        ground.hide_render = name == "bottom"
        scene.camera = bpy.data.objects["CAM | " + name]
        scene.render.filepath = str(output / (name + ".png"))
        start = time.monotonic()
        bpy.ops.render.render(write_still=True)
        emit("render_complete", view=name, path=scene.render.filepath,
             seconds=round(time.monotonic() - start, 3), device=scene.cycles.device)
    set_opened(False)
    ground.hide_render = False
    scene.camera = bpy.data.objects["CAM | hero"]
