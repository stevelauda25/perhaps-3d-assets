"""Standard-library configuration shared by the launcher and Blender."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VIEWS = ("hero", "front", "left", "right", "top", "rear", "bottom", "opened")


def load_config(path=None):
    path = Path(path) if path else ROOT / "config/packaging.json"
    config = json.loads(path.read_text())
    material_path = Path(config["materials_file"])
    if not material_path.is_absolute():
        material_path = ROOT / material_path
    config["materials"] = json.loads(material_path.read_text())
    validate_config(config)
    return config


def validate_config(config):
    g = config["geometry_mm"]
    for key in ("width", "depth", "height", "wall", "base_front", "base_rear", "reveal",
                "bevel", "collar_wall", "collar_clearance", "collar_engagement", "tray_thickness"):
        value = g[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError("geometry_mm.%s must be a finite positive number" % key)
    low, high = sorted((g["base_front"], g["base_rear"]))
    if low <= g["wall"] + g["tray_thickness"]:
        raise ValueError("Base seam must clear the bottom and tray")
    if high + g["reveal"] + g["collar_engagement"] >= g["height"] - g["wall"]:
        raise ValueError("Collar must clear the lid ceiling")
    if 2 * (g["wall"] + g["collar_clearance"] + g["collar_wall"]) >= min(g["width"], g["depth"]):
        raise ValueError("Wall/collar thickness leaves no interior")
    # The tray receives its own smaller bevel in the geometry generator.
    if 2 * g["bevel"] >= min(g["wall"], g["collar_wall"]):
        raise ValueError("Bevel must be smaller than half the shell thickness")
    for preset in config["presets"].values():
        if not isinstance(preset["resolution"], int) or preset["resolution"] < 16:
            raise ValueError("Render resolution must be an integer >= 16")
        if not isinstance(preset["samples"], int) or preset["samples"] < 1:
            raise ValueError("Render samples must be a positive integer")
    for tier in config["materials"].values():
        for slot in ("exterior", "interior", "band", "branding"):
            m = tier[slot]
            if len(m["color"]) != 3 or not all(0 <= v <= 1 for v in m["color"]):
                raise ValueError("Material color must contain three linear RGB values in [0,1]")
            if not 0 <= m["roughness"] <= 1 or not 0 <= m.get("metallic", 0) <= 1:
                raise ValueError("Material roughness/metallic must be in [0,1]")


def check_references(config):
    missing = [p for p in config["references"] if not (ROOT / p).is_file()]
    if missing:
        raise FileNotFoundError("Missing references: " + ", ".join(missing))


def output_directory(path):
    path = Path(path).resolve()
    if (ROOT / "outputs").resolve() not in path.parents:
        raise ValueError("Output must be a new directory beneath workspace outputs/")
    if path.exists():
        raise FileExistsError("Refusing to overwrite existing output: " + str(path))
    return path
