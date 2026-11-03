"""Portable copy of a scene whose textures are external: copies each image next to it under textures/, relative paths.

    python3 -B -m pipeline.package_scene SRC.blend OUT_DIR [--name private_edition.blend]
Packed images are left packed (none expected). Writes dependencies.json. OUT_DIR must be new.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def package(src, out, name):
    import bpy
    bpy.ops.wm.open_mainfile(filepath=src, load_ui=False, use_scripts=False)
    (Path(out) / "textures").mkdir(parents=True)
    deps = {}
    for im in bpy.data.images:
        if im.filepath and not im.packed_file:
            f = Path(bpy.path.abspath(im.filepath))
            dst = Path(out) / "textures" / f.name
            shutil.copy2(f, dst)
            im.filepath = str(dst)
            deps[f.name] = {"path": "textures/" + f.name, "bytes": dst.stat().st_size, "sha256": hashlib.sha256(dst.read_bytes()).hexdigest(),
                            "size": list(im.size), "colorspace": im.colorspace_settings.name}
    bpy.ops.file.make_paths_relative()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(Path(out) / name), compress=True, relative_remap=True)
    (Path(out) / "dependencies.json").write_text(json.dumps({"scene": name, "textures": deps, "note": "paths relative to the .blend; move the whole folder"}, indent=2) + "\n")


if __name__ == "__main__":
    if "--" in sys.argv:
        a = sys.argv[sys.argv.index("--") + 1:]
        package(a[0], a[1], a[2])
    else:
        from .cli import detect_blender
        args = [a for a in sys.argv[1:] if not a.startswith("--")]
        src, out = (ROOT / args[0]).resolve(), (ROOT / args[1]).resolve()
        if out.exists():
            sys.exit("Refusing: OUT_DIR exists")
        name = sys.argv[sys.argv.index("--name") + 1] if "--name" in sys.argv else src.name
        subprocess.run([detect_blender({}), "-b", "--factory-startup", "--disable-autoexec", "--python-exit-code", "1", "--python", __file__, "--", str(src), str(out), name], check=True, stdout=subprocess.DEVNULL)
