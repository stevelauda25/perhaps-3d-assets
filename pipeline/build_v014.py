"""Private Edition v014: v013 with its three 8192 px maps area-resampled to 2048 px (scene otherwise unchanged).

    python3 -B -m pipeline.build_v014        # maps -> scene -> verify; refuses to overwrite

Resampling is a 4x4 box average in the right space: colour luminance in linear light, roughness as linear data,
normals as vectors (average xyz, renormalise). No sharpening. v013 is only read.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
V13, V14 = ROOT / "outputs/packaging/private-edition-v013", ROOT / "outputs/packaging/private-edition-v014"
MAPS = {"leather_red_02_lum_8k.png": "leather_red_02_lum_2k.png", "leather_red_02_rough_8k.png": "leather_red_02_rough_2k.png",
        "leather_red_02_nor_gl_8k.png": "leather_red_02_nor_gl_2k.png"}


def maps():
    import numpy as np
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    from .lean_leather_maps import to_linear, to_srgb
    (V14 / "textures").mkdir(parents=True)
    report = {}
    for src, dst in MAPS.items():
        a = np.asarray(Image.open(V13 / "textures" / src))
        n = a.shape[0] // 4
        out = np.empty((n, n) + a.shape[2:], np.uint8)
        for y in range(0, n, 128):  # 128 output rows = 512 source rows
            b = a[y * 4:(y + 128) * 4].astype(np.float32) / 255
            if "lum" in src:
                b = to_linear(b)
            if "nor" in src:
                b = b * 2 - 1
            r = b.reshape(b.shape[0] // 4, 4, n, 4, *b.shape[2:]).mean(axis=(1, 3))
            if "lum" in src:
                r = to_srgb(r)
            if "nor" in src:
                r = r / np.maximum(np.sqrt((r ** 2).sum(-1, keepdims=True)), 1e-6) * 0.5 + 0.5
            out[y:y + 128] = np.rint(np.clip(r, 0, 1) * 255).astype(np.uint8)
        Image.fromarray(out).save(V14 / "textures" / dst, optimize=True, compress_level=9)
        report[dst] = {"from": src, "size": [n, n], "bytes": (V14 / "textures" / dst).stat().st_size}
    (V14 / "textures" / "maps.json").write_text(json.dumps(report, indent=2) + "\n")


def build():
    import bpy
    bpy.ops.wm.open_mainfile(filepath=str(V13 / "private_edition.blend"), load_ui=False, use_scripts=False)
    for im in bpy.data.images:
        if im.filepath:
            new = V14 / "textures" / MAPS[Path(bpy.path.abspath(im.filepath)).name]
            im.filepath = str(new)
            im.reload()
            im.name = new.stem
    bpy.ops.file.make_paths_relative()
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(V14 / "private_edition.blend"), compress=False, relative_remap=True)
    deps = {i.name: {"path": "textures/" + Path(i.filepath).name, "size": list(i.size), "colorspace": i.colorspace_settings.name,
                     "sha256": hashlib.sha256((V14 / "textures" / Path(i.filepath).name).read_bytes()).hexdigest()}
            for i in bpy.data.images if i.filepath}
    (V14 / "dependencies.json").write_text(json.dumps({"scene": "private_edition.blend", "textures": deps, "note": "paths relative to the .blend; move the whole folder"}, indent=2) + "\n")


def verify():
    import bpy
    sys.path.insert(0, str(ROOT))
    from pipeline.build_v013 import geometry_digest
    bpy.ops.wm.open_mainfile(filepath=str(V13 / "private_edition.blend"), load_ui=False, use_scripts=False)
    ref, ref_mat = geometry_digest(), {m.name: sorted((n.name, n.type) for n in m.node_tree.nodes) for m in bpy.data.materials if m.node_tree}
    bpy.ops.wm.open_mainfile(filepath=str(V14 / "private_edition.blend"), load_ui=False, use_scripts=False)
    geo = geometry_digest()
    mats = {m.name: sorted((n.name, n.type) for n in m.node_tree.nodes) for m in bpy.data.materials if m.node_tree}
    links = {}
    for m in bpy.data.materials:
        for n in (m.node_tree.nodes if m.node_tree else []):
            if n.type == "TEX_IMAGE":
                links.setdefault(m.name, {})[n.name] = [n.image.name, list(n.image.size), n.image.colorspace_settings.name,
                                                        [l.to_node.name + "." + l.to_socket.name for l in n.outputs[0].links]]
    imgs = [i for i in bpy.data.images if i.name != "Render Result"]
    res = {"geometry_differing_objects": sorted(k for k in set(ref) | set(geo) if ref.get(k) != geo.get(k)), "meshes": len(geo),
           "material_node_sets_equal_v013": ref_mat == mats, "tex_nodes": links,
           "images": {i.name: {"relative": i.filepath.startswith("//textures/"), "resolved": Path(bpy.path.abspath(i.filepath)).is_file(),
                               "packed": bool(i.packed_file), "size": list(i.size)} for i in imgs},
           "fonts": len(bpy.data.fonts), "exposure": bpy.context.scene.view_settings.exposure}
    res["ok"] = (not res["geometry_differing_objects"] and res["material_node_sets_equal_v013"] and not res["fonts"]
                 and all(v["relative"] and v["resolved"] and not v["packed"] and v["size"] == [2048, 2048] for v in res["images"].values()))
    (V14 / "integrity.json").write_text(json.dumps(res, indent=2) + "\n")
    print("INTEGRITY", res["ok"], res["geometry_differing_objects"], res["material_node_sets_equal_v013"])


if __name__ == "__main__":
    if "--" in sys.argv:
        {"build": build, "verify": verify}[sys.argv[-1]]()
    elif V14.exists():
        sys.exit("Refusing: " + str(V14) + " exists")
    else:
        from .cli import detect_blender
        maps()
        for mode in ("build", "verify"):
            subprocess.run([detect_blender({}), "-b", "--factory-startup", "--disable-autoexec", "--python-exit-code", "1",
                            "--python", __file__, "--", mode], check=True)
