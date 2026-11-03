"""Launch isolated Blender processes without touching historical asset folders."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from .config import ROOT, VIEWS, check_references, load_config, output_directory, validate_config


def detect_blender(config):
    candidates = [os.environ.get("BLENDER_BIN"), config.get("blender"), shutil.which("blender"),
                  "/Applications/Blender.app/Contents/MacOS/Blender"]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return str(Path(candidate).resolve())
    raise FileNotFoundError("Blender not found; set BLENDER_BIN or config.blender")


def main():
    parser = argparse.ArgumentParser(description="Perhaps Blender CLI production pipeline")
    parser.add_argument("command", choices=("check", "build", "render", "validate", "export"))
    parser.add_argument("--config", type=Path)
    parser.add_argument("--input", type=Path, help="Saved canonical .blend for render/validate/export")
    parser.add_argument("--output", type=Path, help="New directory underneath outputs/")
    parser.add_argument("--tier", default="technical")
    parser.add_argument("--preset", default="preview", choices=("preview", "final"))
    parser.add_argument("--device", default="auto", choices=("auto", "metal", "cpu"))
    parser.add_argument("--views", nargs="+", default=["all"], choices=("all",) + VIEWS)
    parser.add_argument("--render", action="store_true", help="Also render after build")
    args = parser.parse_args()
    try:
        if args.command in ("render", "validate", "export"):
            if not args.input or not args.input.is_file() or args.input.suffix.lower() != ".blend":
                raise ValueError("--input must name an existing canonical .blend")
            args.input = args.input.resolve()
            snapshot = args.input.parent / "effective_config.json"
            if args.config or not snapshot.is_file():
                raise ValueError("Use the effective_config.json beside the input .blend; --config is build/check only")
            config = json.loads(snapshot.read_text())
            validate_config(config)
            args.tier = config["selected_tier"]
        else:
            config = load_config(args.config)
        if args.tier not in config["materials"]:
            raise ValueError("Unknown tier: " + args.tier)
        check_references(config)
        blender = detect_blender(config)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        if args.command == "check":
            expression = (
                "import bpy,sys,json; "
                "p=bpy.context.preferences.addons['cycles'].preferences; "
                "p.compute_device_type='METAL'; p.get_devices(); "
                "print('PIPELINE_CHECK',json.dumps({'blender':bpy.app.version_string,"
                "'python':sys.version,'devices':[(d.name,d.type) for d in p.devices],"
                "'gltf_operator':bpy.ops.export_scene.gltf.get_rna_type().identifier}))"
            )
            result = subprocess.run([blender, "--background", "--factory-startup", "--disable-autoexec",
                                     "--python-exit-code", "1", "--python-expr", expression], env=env)
            raise SystemExit(result.returncode)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        output = output_directory(args.output or ROOT / "outputs/packaging" / (args.command + "-" + stamp))
        output.mkdir(parents=True, exist_ok=False)
        config["selected_tier"] = args.tier
        (output / "effective_config.json").write_text(json.dumps(config, indent=2) + "\n")
        job = {"command": args.command, "input": str(args.input) if args.input else None,
               "output": str(output), "tier": args.tier, "preset": args.preset,
               "device": args.device, "views": list(VIEWS) if "all" in args.views else args.views,
               "render": args.render, "created_utc": stamp, "blender": blender}
        job_path = output / "job.json"
        job_path.write_text(json.dumps(job, indent=2) + "\n")
        command = [blender, "--background", "--factory-startup", "--disable-autoexec",
                   "--python-exit-code", "1", "--python", str(ROOT / "pipeline/entry.py"), "--", str(job_path)]
        print("Running", args.command, "→", output, flush=True)
        with (output / "blender.log").open("w") as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, env=env)
        status = {"exit_code": result.returncode, "success": result.returncode == 0}
        (output / "status.json").write_text(json.dumps(status, indent=2) + "\n")
        if result.returncode:
            print("Blender failed; log:", output / "blender.log", file=sys.stderr)
            print("\n".join((output / "blender.log").read_text().splitlines()[-18:]), file=sys.stderr)
        else:
            print("Completed:", output, flush=True)
        raise SystemExit(result.returncode)
    except (OSError, ValueError, KeyError) as exc:
        parser.error(str(exc))
