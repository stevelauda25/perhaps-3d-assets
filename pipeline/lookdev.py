"""CLI for material updates and rendering of an approved, locked canonical scene."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from .grain_compare import grain_multiplier

from .cli import detect_blender
from .config import ROOT, output_directory

VIEWS = ("hero", "front", "left", "opened", "leather_macro", "branding_macro", "corner_macro",
         "reference_hero", "reference_leather_macro", "reference_branding_macro", "reference_corner_macro")


def validate_settings(config):
    grain_multiplier(config["leather"].get("leather_grain_scale_multiplier", 1.0))
    if "surface_refinement" in config["leather"]:
        from .realism import validate_refinement
        validate_refinement(config)
    if not 0 < config["leather"]["source_maps"]["tile_width_mm"] <= 1000:
        raise ValueError("Leather scan tile width must be in (0,1000] mm")
    if not 0 < config["leather"]["grain_height_um"] <= 150:
        raise ValueError("Leather relief must be in (0,150] microns")
    if not 0 < config["branding"]["deboss_depth_mm"] <= 0.2:
        raise ValueError("Finishing skin/deboss depth must be in (0,0.2] mm")
    if not 0 < config["stitching"]["length_mm"] < config["stitching"]["pitch_mm"]:
        raise ValueError("Stitch length must be shorter than its pitch")
    for name in ("preview", "performance", "hero", "macro"):
        profile = config["presets"][name]
        if profile["resolution"] < 16 or profile["samples"] < 1:
            raise ValueError("Invalid render profile " + name)


def main():
    parser = argparse.ArgumentParser(description="Perhaps locked-geometry Private Edition look development")
    parser.add_argument("command", choices=("prepare", "refine", "preview", "performance", "final", "validate", "grain-compare", "surface-refine"))
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--config", type=Path, help="Material settings for prepare; renders use scene snapshots")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--views", nargs="+", choices=VIEWS, help="Default: all six previews; hero + two macros for final")
    parser.add_argument("--device", default="metal", choices=("metal", "cpu", "auto"))
    args = parser.parse_args()
    try:
        source = args.input.resolve()
        if not source.is_file() or source.suffix.lower() != ".blend":
            raise ValueError("--input must be an existing .blend")
        if args.command not in ("prepare", "refine", "surface-refine") and args.config:
            raise ValueError("Render/validation uses saved settings; use prepare/refine for parameter changes")
        if args.command in ("grain-compare", "surface-refine") and args.views:
            raise ValueError(args.command+" uses its fixed benchmark cameras")
        if args.command == "surface-refine" and not args.config:
            raise ValueError("surface-refine requires a versioned --config")
        settings_path = args.config or (ROOT / "config/private_edition_reference.json" if args.command in ("prepare", "refine")
                                       else source.parent / "lookdev_config.json")
        config = json.loads(settings_path.read_text())
        validate_settings(config)
        if args.command == "surface-refine":
            from .realism import validate_refinement
            validate_refinement(config)
        if args.command == "grain-compare" and (config["leather"]["source_maps"]["tile_width_mm"] != 32 or
                config["leather"].get("leather_grain_scale_multiplier", 1.0) != 1.0):
            raise ValueError("grain-compare requires the unscaled v007 32 mm baseline")
        canonical = json.loads((source.parent / "effective_config.json").read_text())
        studio_path = ROOT / config["studio_file"] if args.command in ("prepare", "refine", "surface-refine") else source.parent / "studio_config.json"
        studio = json.loads(studio_path.read_text())
        if args.command in ("prepare", "refine"):
            maps = config["leather"]["source_maps"]
            resources = [ROOT / config["reference"], Path(config["branding"]["font"]), ROOT/maps["height"], ROOT/maps["roughness"]]
            if config.get("reference_reconstruction"):
                resources += [ROOT/maps["color"], ROOT/maps["normal"]]
            for p in resources:
                if not p.is_file():
                    raise FileNotFoundError(str(p))
        if args.command != "prepare" and not (source.parent / "geometry_lock.json").is_file():
            raise ValueError("Input is not a prepared look-development scene")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        output = output_directory(args.output or ROOT / "outputs/packaging" / ("private-"+args.command+"-"+stamp))
        output.mkdir(parents=True, exist_ok=False)
        for name, value in [("lookdev_config.json", config), ("studio_config.json", studio), ("effective_config.json", canonical)]:
            (output/name).write_text(json.dumps(value, indent=2)+"\n")
        blender = detect_blender(canonical)
        job = {"command": args.command, "input": str(source), "output": str(output), "device": args.device,
               "views": args.views or (config.get("benchmark_views") or
                         (list(VIEWS[:6]) if args.command == "preview" else ["hero", "leather_macro", "branding_macro"])),
               "created_utc": stamp}
        job_path = output/"job.json"
        job_path.write_text(json.dumps(job, indent=2)+"\n")
        command = [blender, "--background", "--factory-startup", "--disable-autoexec", "--python-exit-code", "1",
                   "--python", str(ROOT/"pipeline/lookdev_entry.py"), "--", str(job_path)]
        print("Running", args.command, "→", output, flush=True)
        with (output/"blender.log").open("w") as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                    env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        if result.returncode:
            print("\n".join((output/"blender.log").read_text().splitlines()[-18:]), file=sys.stderr)
        elif args.command in ("grain-compare", "surface-refine"):
            try:
                if args.command == "grain-compare":
                    from .grain_compare import finish_comparison
                    finish_comparison(output)
                else:
                    from .realism import finish_realism
                    finish_realism(output)
            except Exception as exc:
                (output/"status.json").write_text(json.dumps({"success": False, "exit_code": 1,
                                                             "stage": "comparison_sheet", "error": str(exc)}, indent=2)+"\n")
                raise
        (output/"status.json").write_text(json.dumps({"success": result.returncode == 0, "exit_code": result.returncode}, indent=2)+"\n")
        print("Completed" if result.returncode == 0 else "Failed", output, flush=True)
        raise SystemExit(result.returncode)
    except (ValueError, KeyError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
