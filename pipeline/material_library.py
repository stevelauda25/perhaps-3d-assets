"""PBR material library: approved/candidate presets in config/material_library/<id>.json (stdlib only).

    python3 -B -m pipeline.material_library list
    python3 -B -m pipeline.material_library verify [ID ...]     # texture checksums vs source manifest
    python3 -B -m pipeline.material_library hash DIR            # sha256/bytes/size of every map in DIR (for source.json)
    python3 -B -m pipeline.material_library sheet JOB_ID        # labelled comparison sheet of a lookdev job's renders

An agent selects a material by ID (job param `material`, or `library` on a tier role); it never rebuilds the shader.
"""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
LIBRARY = ROOT / "config/material_library"


def preset_path(material_id):
    return LIBRARY / (material_id + ".json")


def load(material_id):
    p = preset_path(material_id)
    if not p.is_file():
        raise FileNotFoundError("Unknown material %r; available: %s" % (material_id, ", ".join(ids()) or "none"))
    return json.loads(p.read_text())


def ids():
    return sorted(p.stem for p in LIBRARY.glob("*.json"))


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 23), b""):
            h.update(block)
    return h.hexdigest()


def verify(preset):
    """Raise unless every mapped texture exists and matches its recorded checksum."""
    if not any(preset["maps"].values()):  # parametric preset: nothing to checksum
        return {}
    src = ROOT / preset["source"]["dir"]
    manifest = json.loads((src / "source.json").read_text())["files"]
    for channel, name in preset["maps"].items():
        if name is None:
            continue
        if name not in manifest or sha256(src / name) != manifest[name]["sha256"]:
            raise RuntimeError("%s: texture %s missing or checksum changed" % (preset["id"], name))
    return {c: str(src / n) for c, n in preset["maps"].items() if n}


def hash_dir(d):
    d = Path(d)
    files = [p for p in sorted(d.iterdir()) if p.suffix.lower() in (".png", ".jpg", ".exr", ".tif")]
    return {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in files}


def sheet(job_id):
    from PIL import Image, ImageDraw
    out = ROOT / "outputs/jobs" / job_id
    pngs = sorted(out.glob("*.png"))
    pngs = [p for p in pngs if p.stem != "comparison"]
    tiles = [Image.open(p).convert("RGB") for p in pngs]
    cell = 800
    cols = 4
    rows = -(-len(tiles) // cols)
    canvas = Image.new("RGB", (cols * cell, rows * (cell + 30)), "black")
    for i, (p, t) in enumerate(zip(pngs, tiles)):
        t.thumbnail((cell, cell))
        x, y = (i % cols) * cell, (i // cols) * (cell + 30)
        canvas.paste(t, (x, y + 30))
        ImageDraw.Draw(canvas).text((x + 8, y + 8), p.stem, fill=(255, 255, 255))
    canvas.save(out / "comparison.png")
    return str(out / "comparison.png")


if __name__ == "__main__":
    cmd, args = (sys.argv[1] if len(sys.argv) > 1 else "list"), sys.argv[2:]
    if cmd == "list":
        for i in ids():
            m = load(i)
            print(json.dumps({"id": i, "category": m["category"], "status": m["status"], "approved_version": m.get("approved_version")}))
    elif cmd == "verify":
        for i in args or ids():
            verify(load(i)); print(i, "ok")
    elif cmd == "hash":
        print(json.dumps(hash_dir(args[0]), indent=2))
    elif cmd == "sheet":
        print(sheet(args[0]))
    else:
        sys.exit(__doc__)
