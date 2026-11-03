"""Explicit Blender material-development entry; no geometry construction calls."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    job = json.loads(Path(sys.argv[sys.argv.index("--")+1]).read_text())
    if job["command"] == "grain-compare":
        from pipeline.grain_compare import run_blender
        return run_blender(job)
    if job["command"] == "surface-refine":
        from pipeline.realism import run_blender
        return run_blender(job)
    import bpy
    from pipeline import leather, finishing, lookdev_studio, locked, rendering
    from pipeline.geometry.box import set_opened
    from pipeline.validation import validate

    output, source = Path(job["output"]), Path(job["input"])
    config = json.loads((output/"lookdev_config.json").read_text())
    studio = json.loads((output/"studio_config.json").read_text())
    canonical = json.loads((output/"effective_config.json").read_text())

    def emit(event, **fields):
        record = {"time_utc": datetime.now(timezone.utc).isoformat(), "event": event, **fields}
        with (output/"events.jsonl").open("a") as stream:
            stream.write(json.dumps(record)+"\n")
        print("LOOKDEV", json.dumps(record), flush=True)

    def profile(name, device):
        rendering.configure({"presets": {name: config["presets"][name]}}, name, device, emit)
        bpy.context.scene.view_settings.exposure = studio["exposure"]
        bpy.context.scene.view_settings.view_transform = studio.get("view_transform", "AgX")
        bpy.context.scene.cycles.max_bounces = 12
        bpy.context.scene.cycles.use_light_tree = True
        bpy.context.scene.render.use_file_extension = True

    def render(name, path, preset, device):
        set_opened(name == "opened")
        profile(preset, device)
        scene = bpy.context.scene
        scene.camera = bpy.data.objects["CAM | "+name]
        scene.render.filepath = str(path)
        start = time.monotonic()
        bpy.ops.render.render(write_still=True)
        elapsed = round(time.monotonic()-start, 3)
        emit("render_complete", view=name, preset=preset, device=device, seconds=elapsed, path=str(path))
        set_opened(False)
        return elapsed

    try:
        emit("started", command=job["command"], source=str(source))
        source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
        bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
        if job["command"] in ("prepare", "refine"):
            if job["command"] == "refine":
                lock = json.loads((source.parent/"geometry_lock.json").read_text())
                locked.verify(lock["protected"])
                expected = dict(lock["protected"])
                extra = [o.name for o in bpy.data.objects if o.type == "CAMERA" and o.name not in expected]
                expected.update(locked.snapshot(extra))
                lock["protected"] = expected
                lock["refinement_input"] = str(source)
                lock["refinement_input_sha256"] = source_hash
                for obj in list(bpy.data.objects):
                    if obj.get("finishing_only"):
                        bpy.data.objects.remove(obj, do_unlink=True)
            else:
                expected = locked.snapshot()
                lock = {"source": str(source), "source_sha256": source_hash,
                        "protected": expected, "fingerprint": locked.digest(expected)}
            lock["fingerprint"] = locked.digest(expected)
            (output/"geometry_lock.json").write_text(json.dumps(lock, indent=2)+"\n")
            if config.get("reference_reconstruction"):
                from pipeline import reference_material, reference_finish, reference_studio
                mats = reference_material.apply(config)
                details = reference_finish.build(config, canonical, mats)
                reference_studio.cameras(config)
                reference_studio.apply(studio["neutral"])
                render("reference_leather_macro", output/"material_neutral.png", "material_preview", job["device"])
                reference_studio.apply(studio)
            else:
                mats = leather.apply(config)
                details = finishing.build(config, canonical, mats)
                lookdev_studio.apply(config, studio)
            profile("preview", job["device"])
            bpy.context.scene.camera = bpy.data.objects["CAM | reference_hero" if config.get("reference_reconstruction") else "CAM | hero"]
            emit("finishing_created", **details)
        else:
            lock = json.loads((source.parent/"geometry_lock.json").read_text())
            expected = lock["protected"]
            (output/"geometry_lock.json").write_text(json.dumps(lock, indent=2)+"\n")
        protected_hash = locked.verify(expected)
        report = validate(canonical)
        report["approved_geometry_and_original_cameras_unchanged"] = True
        report["protected_fingerprint"] = protected_hash
        report["approved_master_sha256"] = lock["source_sha256"]
        report["packed_images"] = {image.name: bool(image.packed_file) for image in bpy.data.images if image.source == "FILE"}
        report["packed_fonts"] = {font.name: bool(font.packed_file) for font in bpy.data.fonts if font.filepath != "<builtin>"}
        report["finishing_objects"] = [obj.name for obj in bpy.data.objects if obj.get("finishing_only")]
        for material in bpy.data.materials:
            if material.use_nodes:
                for node in material.node_tree.nodes:
                    if node.type == "OUTPUT_MATERIAL" and node.inputs["Displacement"].is_linked:
                        raise RuntimeError("Structural displacement is forbidden on this locked asset")
        (output/"validation.json").write_text(json.dumps(report, indent=2)+"\n")
        if job["command"] in ("prepare", "refine"):
            bpy.context.preferences.filepaths.save_version = 0
            bpy.context.scene.render.filepath = str(output/"hero.png")
            bpy.ops.wm.save_as_mainfile(filepath=str(output/"private_edition.blend"))
            emit("scene_saved", path=str(output/"private_edition.blend"))
        elif job["command"] == "performance":
            results = {}
            for device in ("cpu", "metal"):
                results[device] = render("hero", output/("hero_"+device+".png"), "performance", device)
            results["note"] = "One 384px/16-sample render per device; cold setup/compilation included, not a final-resolution speed prediction"
            (output/"performance.json").write_text(json.dumps(results, indent=2)+"\n")
        elif job["command"] in ("preview", "final"):
            for name in job["views"]:
                preset = "preview" if job["command"] == "preview" else ("hero" if name not in config["macros"] else "macro")
                render(name, output/(name+".png"), preset, job["device"])
        locked.verify(expected)
        if hashlib.sha256(source.read_bytes()).hexdigest() != source_hash:
            raise RuntimeError("Input scene changed on disk")
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        emit("completed", protected_fingerprint=protected_hash,
             peak_process_resident_mb=round(peak/(1024*1024) if sys.platform == "darwin" else peak/1024, 2))
    except Exception as exc:
        emit("failed", error=str(exc))
        raise


if __name__ == "__main__":
    main()
