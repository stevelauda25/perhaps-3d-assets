"""Lossless storage optimisation of a finished scene into a separate portable copy (never edits the source).

    python3 -B -m pipeline.optimize_scene SRC.blend OUT_DIR [--name private_edition.blend]

Does, in the copy only: delete texture nodes whose outputs have no links (and images they alone used),
write each remaining packed image byte-for-byte to OUT_DIR/textures/ (only if its bytes are not already
there), reference it project-relative (//textures/<file>), drop the packed copy. Pixels, colour spaces and
node links are unchanged. Writes dependencies.json and optimization_data.json (signatures + sizes), then
re-opens the copy in a second Blender process and compares scene signatures with the source.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def signature(removed=()):
    """Digest of everything the optimisation must not change. `removed` node names are skipped."""
    import bpy
    from pipeline.locked import values

    def h(x):
        return hashlib.sha256(json.dumps(x, sort_keys=True, default=str).encode()).hexdigest()

    def rnd(v):
        return [round(x, 7) for x in v] if hasattr(v, "__len__") and not isinstance(v, str) else (round(v, 7) if isinstance(v, float) else v)

    sig = {"objects": {}, "materials": {}, "lights": {}, "cameras": {}, "scene": {}, "images": {}}
    for o in bpy.data.objects:
        rec = {"type": o.type, "parent": o.parent.name if o.parent else None, "data": o.data.name if o.data else None,
               "matrix_basis": [rnd(r) for r in o.matrix_basis], "hide_render": o.hide_render, "hide_viewport": o.hide_viewport,
               "mods": [values(m) for m in o.modifiers], "slots": [s.material.name if s.material else None for s in o.material_slots],
               "collections": sorted(c.name for c in o.users_collection)}
        if o.type == "MESH":
            rec["verts"] = h([rnd(v.co) for v in o.data.vertices]); rec["faces"] = h([(list(p.vertices), p.material_index, p.use_smooth) for p in o.data.polygons])
            rec["uvs"] = sorted(o.data.uv_layers.keys())
        sig["objects"][o.name] = h(rec)
        if o.type == "LIGHT":
            sig["lights"][o.name] = h(values(o.data))
        if o.type == "CAMERA":
            sig["cameras"][o.name] = h(values(o.data))
    for m in bpy.data.materials:
        if not m.node_tree:
            continue
        nodes = {n.name: n for n in m.node_tree.nodes if n.name not in removed}
        rec = {"props": values(m),
               "nodes": {k: [values(n), {i.identifier: rnd(i.default_value) for i in n.inputs if hasattr(i, "default_value") and not i.is_linked},
                             n.image.name if getattr(n, "image", None) else None] for k, n in nodes.items()},
               "links": sorted((l.from_node.name, l.from_socket.identifier, l.to_node.name, l.to_socket.identifier)
                               for l in m.node_tree.links if l.from_node.name in nodes and l.to_node.name in nodes)}
        sig["materials"][m.name] = h(rec)
    s = bpy.context.scene
    for k, block in {"render": s.render, "cycles": s.cycles, "view": s.view_settings, "display": s.display_settings,
                     "image": s.render.image_settings, "unit": s.unit_settings}.items():
        sig["scene"][k] = h(values(block))
    sig["scene"]["camera"] = s.camera.name if s.camera else None
    sig["scene"]["world"] = h([[n.name, values(n)] for n in s.world.node_tree.nodes]) if s.world and s.world.node_tree else None
    for i in bpy.data.images:
        if i.name != "Render Result":
            sig["images"][i.name] = {"size": list(i.size), "colorspace": i.colorspace_settings.name, "alpha_mode": i.alpha_mode,
                                     "channels": i.channels, "filepath": i.filepath, "packed": bool(i.packed_file)}
    return sig


def optimise(src, out_dir, name):
    import bpy
    bpy.ops.wm.open_mainfile(filepath=str(src), load_ui=False, use_scripts=False)
    dead = [(m, n) for m in bpy.data.materials if m.node_tree for n in m.node_tree.nodes
            if n.type == "TEX_IMAGE" and not any(o.links for o in n.outputs)]
    removed = [(m.name, n.name, n.image.name if n.image else None) for m, n in dead]
    pre = signature({n for _, n, _ in removed})  # everything except the dead nodes
    for m, n in dead:
        m.node_tree.nodes.remove(n)
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=False, do_recursive=True)  # images only they used
    tex = out_dir / "textures"
    tex.mkdir(parents=True, exist_ok=True)
    deps = {}
    for i in bpy.data.images:
        if i.name == "Render Result" or not i.packed_file:
            continue
        data = bytes(i.packed_file.data)
        target = tex / i.name
        if not target.exists():
            target.write_bytes(data)
        elif target.read_bytes() != data:
            raise RuntimeError("Refusing to overwrite different %s" % target)
        deps[i.name] = {"path": "textures/" + i.name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                        "size": list(i.size), "colorspace": i.colorspace_settings.name}
        i.unpack(method="REMOVE")
        i.filepath = str(target)  # absolute while resolving; made relative before saving
        i.source = "FILE"
        i.reload()
    for i in bpy.data.images:
        if i.name != "Render Result":
            assert i.size[0] > 0 and not i.packed_file, "texture did not resolve: " + i.name
            assert list(i.size) == deps[i.name]["size"], "size changed: " + i.name
    bpy.ops.file.make_paths_relative()  # relative to the source; save_as remaps to the new location
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(out_dir / name), compress=False, relative_remap=True)
    (out_dir / "dependencies.json").write_text(json.dumps({"scene": name, "textures": deps, "note": "paths relative to the .blend; move the whole folder"}, indent=2) + "\n")
    (out_dir / "optimization_data.json").write_text(json.dumps({"pre": pre, "removed_nodes": removed, "source": str(src.relative_to(ROOT))}, indent=2) + "\n")


def verify(blend, out_dir):
    import bpy
    bpy.ops.wm.open_mainfile(filepath=str(blend), load_ui=False, use_scripts=False)
    data = json.loads((out_dir / "optimization_data.json").read_text())
    removed = {n for _, n, _ in data["removed_nodes"]}
    post, pre = signature(removed), data["pre"]
    diffs = [(sec, k) for sec in ("objects", "materials", "lights", "cameras", "scene") for k in set(pre[sec]) | set(post[sec])
             if pre[sec].get(k) != post[sec].get(k)]
    img_diffs = [(k, pre["images"][k], post["images"].get(k)) for k in pre["images"]
                 if k in post["images"] and {a: b for a, b in pre["images"][k].items() if a not in ("filepath", "packed")} !=
                 {a: b for a, b in post["images"][k].items() if a not in ("filepath", "packed")}]
    deps = json.loads((out_dir / "dependencies.json").read_text())["textures"]
    resolved = {i.name: Path(bpy.path.abspath(i.filepath)).is_file() and i.filepath.startswith("//textures/")
                for i in bpy.data.images if i.name != "Render Result"}
    hashes = {k: hashlib.sha256((out_dir / v["path"]).read_bytes()).hexdigest() == v["sha256"] for k, v in deps.items()}
    result = {"signature_diffs": diffs, "image_setting_diffs": img_diffs, "textures_resolved": resolved,
              "texture_bytes_match_source": hashes, "images_in_copy": sorted(post["images"]),
              "removed_images_absent": sorted({i for _, _, i in data["removed_nodes"] if i} - set(post["images"]))}
    result["ok"] = not diffs and not img_diffs and all(resolved.values()) and all(hashes.values())
    (out_dir / "integrity.json").write_text(json.dumps(result, indent=2) + "\n")
    print("INTEGRITY " + json.dumps({"ok": result["ok"], "diffs": len(diffs), "image_diffs": len(img_diffs)}))


def main(argv):
    sys.path.insert(0, str(ROOT))
    mode = argv[0]
    if mode == "optimise":
        optimise(Path(argv[1]), Path(argv[2]), argv[3])
    else:
        verify(Path(argv[1]), Path(argv[2]))


if __name__ == "__main__":
    if "--" in sys.argv:
        main(sys.argv[sys.argv.index("--") + 1:])
    else:
        from .cli import detect_blender
        args = [a for a in sys.argv[1:] if not a.startswith("--")]
        src, out = (ROOT / args[0]).resolve(), (ROOT / args[1]).resolve()
        name = sys.argv[sys.argv.index("--name") + 1] if "--name" in sys.argv else src.name
        if out in src.parents or out.exists() and any(out.glob("*.blend")):
            sys.exit("Refusing: OUT_DIR must be new and not contain the source")
        for mode, rest in (("optimise", [str(src), str(out), name]), ("verify", [str(out / name), str(out)])):
            subprocess.run([detect_blender({}), "-b", "--factory-startup", "--disable-autoexec", "--python-exit-code", "1",
                            "--python", __file__, "--", mode, *rest], check=True, stdout=subprocess.DEVNULL if mode == "optimise" else None)
