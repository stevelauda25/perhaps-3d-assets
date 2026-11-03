"""Private Edition v013: Essential v002 lean scene + v012 wordmark wrap and leather graphs + lean 8K maps.

    python3 -B -m pipeline.build_v013            # maps, scene, verification (new OUT dir only)

Scene: open the Essential v002 job scene (canonical geometry, cameras, lights, no heavy images), bring in only the
v012 lid wrap (Baskerville deboss) and the four Private Edition material graphs from the v012 reference, point their
image nodes at project-relative lean maps, show the stitching, set the v012 exposure, purge, save.
Verify (second process): images external/relative/resolved/unpacked, no fonts or orphans, and every mesh object's
world matrix + evaluated geometry equals v012's.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/private_edition_v013.json"


def geometry_digest():
    import bpy
    dg, out = bpy.context.evaluated_depsgraph_get(), {}
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        m = o.evaluated_get(dg).to_mesh()
        h = hashlib.sha256()
        for v in m.vertices:
            h.update(("%.7f,%.7f,%.7f;" % tuple(v.co)).encode())
        for p in m.polygons:
            h.update((",".join(map(str, p.vertices)) + ";").encode())
        out[o.name] = {"geom": h.hexdigest(), "matrix_world": [round(x, 7) for r in o.matrix_world for x in r], "hide_render": o.hide_render}
        o.evaluated_get(dg).to_mesh_clear()
    return out


def build(cfg, out):
    import bpy
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / cfg["base"]), load_ui=False, use_scripts=False)
    ref = ROOT / cfg["visual_reference"]
    old = bpy.data.objects[cfg["lid_wrap"]]
    old.name = "OLD lid wrap"
    with bpy.data.libraries.load(str(ref), link=False) as (src, dst):
        dst.objects = [cfg["lid_wrap"]]
        dst.materials = list(cfg["reference_materials"].values())
    wrap = bpy.data.objects[cfg["lid_wrap"]]
    for c in old.users_collection:
        c.objects.link(wrap)
    wrap.parent, wrap.matrix_parent_inverse = old.parent, old.matrix_parent_inverse.copy()
    assert all(abs(a - b) < 1e-9 for ra, rb in zip(wrap.matrix_basis, old.matrix_basis) for a, b in zip(ra, rb)), "wrap placement differs"
    bpy.data.objects.remove(old, do_unlink=True)
    mats = {k: bpy.data.materials[v] for k, v in cfg["reference_materials"].items()}
    for obj in bpy.data.objects:
        for slot in obj.material_slots:
            if slot.material and slot.material.name in mats:
                slot.material = mats[slot.material.name]
    textures = out / "textures"
    for m in {mats["Essential | exterior"], mats["Essential | branding"]}:
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE":
                img = bpy.data.images.load(str(textures / cfg["images"][n.name]), check_existing=True)
                img.colorspace_settings.name = "sRGB" if n.name.endswith("color") else "Non-Color"
                n.image = img
    for name in cfg["show_render"]:
        bpy.data.objects[name].hide_render = False
    for name in cfg["reference_materials"]:  # Essential paperboard materials and their packed images go
        bpy.data.materials.remove(bpy.data.materials[name])
    for f in list(bpy.data.fonts):  # wordmark is baked geometry; the font is dead weight
        bpy.data.fonts.remove(f)
    bpy.data.orphans_purge(do_recursive=True)
    for im in [i for i in bpy.data.images if i.packed_file]:
        raise SystemExit("packed image left: " + im.name)
    bpy.context.scene.view_settings.exposure = cfg["exposure"]
    bpy.data.orphans_purge(do_recursive=True)
    bpy.ops.file.make_paths_relative()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(out / cfg["scene"]), compress=False, relative_remap=True)
    deps = {}
    for i in bpy.data.images:
        if i.filepath:
            f = Path(bpy.path.abspath(i.filepath))
            deps[f.name] = {"path": "textures/" + f.name, "bytes": f.stat().st_size, "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
                            "size": list(i.size), "colorspace": i.colorspace_settings.name}
    (out / "dependencies.json").write_text(json.dumps({"scene": cfg["scene"], "textures": deps, "note": "paths relative to the .blend; move the whole folder"}, indent=2) + "\n")


def verify(cfg, out):
    import bpy
    bpy.ops.wm.open_mainfile(filepath=str(ref := ROOT / cfg["visual_reference"]), load_ui=False, use_scripts=False)
    ref_geo = geometry_digest()
    bpy.ops.wm.open_mainfile(filepath=str(out / cfg["scene"]), load_ui=False, use_scripts=False)
    geo = geometry_digest()
    diffs = sorted(k for k in set(ref_geo) | set(geo) if ref_geo.get(k) != geo.get(k))
    imgs = [i for i in bpy.data.images if i.name != "Render Result"]
    deps = json.loads((out / "dependencies.json").read_text())["textures"]
    res = {"geometry_vs_v012_differing_objects": diffs, "mesh_objects_compared": len(geo),
           "images": {i.name: {"relative": i.filepath.startswith("//textures/"), "resolved": Path(bpy.path.abspath(i.filepath)).is_file(),
                               "packed": bool(i.packed_file), "colorspace": i.colorspace_settings.name} for i in imgs},
           "texture_sha_match": {k: hashlib.sha256((out / v["path"]).read_bytes()).hexdigest() == v["sha256"] for k, v in deps.items()},
           "fonts": [f.name for f in bpy.data.fonts], "materials": sorted(m.name for m in bpy.data.materials),
           "unused_images": [i.name for i in imgs if i.users == 0],
           "exposure": bpy.context.scene.view_settings.exposure, "view_transform": bpy.context.scene.view_settings.view_transform}
    res["ok"] = (not diffs and all(v["relative"] and v["resolved"] and not v["packed"] for v in res["images"].values())
                 and all(res["texture_sha_match"].values()) and not res["fonts"] and not res["unused_images"])
    (out / "integrity.json").write_text(json.dumps(res, indent=2) + "\n")
    print("INTEGRITY " + json.dumps({"ok": res["ok"], "geometry_diffs": diffs}))


def main(argv):
    cfg = json.loads(CONFIG.read_text())
    {"build": build, "verify": verify}[argv[0]](cfg, ROOT / cfg["output"])


if __name__ == "__main__":
    if "--" in sys.argv:
        main(sys.argv[sys.argv.index("--") + 1:])
    else:
        from .cli import detect_blender
        out = ROOT / json.loads(CONFIG.read_text())["output"]
        if (out / "private_edition.blend").exists():
            sys.exit("Refusing: output already exists: " + str(out))
        subprocess.run([sys.executable, "-B", "-m", "pipeline.lean_leather_maps", str(out / "textures")], check=True, cwd=ROOT)
        for mode in ("build", "verify"):
            subprocess.run([detect_blender({}), "-b", "--factory-startup", "--disable-autoexec", "--python-exit-code", "1",
                            "--python", __file__, "--", mode], check=True)
