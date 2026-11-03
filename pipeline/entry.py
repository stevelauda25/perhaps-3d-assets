"""Blender entry point; only main() performs scene operations or writes files."""
import json
from pathlib import Path
import sys
from datetime import datetime, timezone

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    import bpy
    from pipeline import materials, studio, rendering
    from pipeline.geometry import box
    from pipeline.validation import validate
    from pipeline.exporting import export_glb

    job = json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text())
    output = Path(job["output"])
    config = json.loads((output / "effective_config.json").read_text())

    def emit(event, **fields):
        record = {"time_utc": datetime.now(timezone.utc).isoformat(), "event": event, **fields}
        with (output / "events.jsonl").open("a") as stream:
            stream.write(json.dumps(record) + "\n")
        print("PIPELINE", json.dumps(record), flush=True)

    try:
        emit("started", command=job["command"])
        if job["command"] == "build":
            bpy.ops.wm.read_factory_settings(use_empty=True)
            scene = bpy.context.scene
            scene.unit_settings.system = "METRIC"
            scene.unit_settings.length_unit = "MILLIMETERS"
            scene.unit_settings.scale_length = 1
            box.build(config, materials.create_materials(config, job["tier"]))
            rendering.configure(config, job["preset"], job["device"], emit)
            studio.create(config)
        else:
            bpy.ops.wm.open_mainfile(filepath=job["input"], load_ui=False, use_scripts=False)
            box.set_opened(False)
            if job["command"] == "render":
                rendering.configure(config, job["preset"], job["device"], emit)
        report = validate(config)
        (output / "validation.json").write_text(json.dumps(report, indent=2) + "\n")
        emit("geometry_validated", mesh_sha256=report["mesh_sha256"], bounds_mm=report["closed_bounds_mm"])
        if job["command"] == "build":
            scene = bpy.context.scene
            scene.render.filepath = str(output / "hero.png")
            bpy.context.preferences.filepaths.save_version = 0
            path = output / "canonical_box.blend"
            bpy.ops.wm.save_as_mainfile(filepath=str(path))
            emit("scene_saved", path=str(path))
        if job["command"] == "render" or (job["command"] == "build" and job["render"]):
            rendering.render_views(job["views"], output, emit)
        if job["command"] == "export":
            export_glb(output / "canonical_box.glb")
            emit("glb_exported", path=str(output / "canonical_box.glb"), materials="placeholder")
        emit("completed")
    except Exception as exc:
        emit("failed", error=str(exc))
        raise


if __name__ == "__main__":
    main()
