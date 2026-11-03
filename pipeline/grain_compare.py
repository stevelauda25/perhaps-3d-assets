"""One controlled material-coordinate comparison; no geometry or studio rebuilding."""
import copy
import hashlib
import json
import math
from pathlib import Path
import time

from .config import ROOT

SCALE_NODE = "Leather grain physical size multiplier"
CANDIDATES = (("a", 1.5), ("b", 2.25), ("c", 3.0))
PREVIEW = {"resolution": 1024, "samples": 128, "adaptive_threshold": 0.01,
           "denoise": True, "bit_depth": "16"}
MATERIALS = ("PE6 | Scanned obsidian leather", "PE6 | Pressed leather")
VIEWS = ("reference_hero", "reference_leather_macro")


def grain_multiplier(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError("leather_grain_scale_multiplier must be a finite positive number")
    if not math.isfinite(1.0/value) or not 1.17549435e-38 <= 1.0/value <= 3.4e38:
        raise ValueError("Leather grain coordinate factor exceeds Blender float precision")
    return float(value)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2)+"\n")


def file_manifest(source):
    paths = [source.parent, source.parent.with_name(source.parent.name+"-benchmarks"),
             ROOT/"outputs/packaging/canonical-v001", ROOT/"references/packaging",
             ROOT/"textures/sources/ambientcg_leather037_2k"]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in paths for p in sorted(folder.rglob("*")) if p.is_file()}


def scene_snapshot(raw=False):
    """Fingerprint scene data, normalizing only the explicitly allowed changes."""
    import bpy
    from .locked import values, snapshot

    def props(block, exclude=()):
        result = {k: v for k, v in values(block).items() if k not in exclude}
        for prop in block.bl_rna.properties:
            if prop.type == "POINTER" and prop.identifier not in {"rna_type", "id_data", *exclude}:
                target = getattr(block, prop.identifier)
                if isinstance(target, bpy.types.ID):
                    result[prop.identifier] = target.name_full
        return result

    def custom(block):
        return {k: repr(block[k]) for k in block.keys()
                if k not in {"leather_grain_scale_multiplier", "effective_tile_width_mm"}}

    def nodes(tree):
        if tree is None:
            return None
        data = {}
        for node in tree.nodes:
            if node.name == SCALE_NODE:
                continue
            sockets = []
            for direction in (node.inputs, node.outputs):
                sockets.append([(s.identifier, list(s.default_value) if hasattr(s.default_value, "__len__")
                                 and not isinstance(s.default_value, str) else s.default_value)
                                for s in direction if hasattr(s, "default_value")])
            data[node.name] = {"properties": props(node), "sockets": sockets}
        links = []
        for link in tree.links:
            if link.to_node.name == SCALE_NODE:
                continue
            start = link.from_socket
            if link.from_node.name == SCALE_NODE:
                start = link.from_node.inputs[0].links[0].from_socket
            links.append((start.node.name, start.identifier, link.to_node.name, link.to_socket.identifier))
        return {"nodes": data, "links": sorted(links)}

    objects = snapshot([o.name for o in bpy.data.objects])
    for obj in bpy.data.objects:
        objects[obj.name].update(properties=props(obj), custom=custom(obj), hidden=obj.hide_get(),
                                 constraints=[props(c) for c in obj.constraints])
    meshes = {}
    for mesh in bpy.data.meshes:
        attrs = {a.name: [props(v) for v in a.data] for a in mesh.attributes}
        meshes[mesh.name] = {"properties": props(mesh), "attributes": attrs,
                             "uvs": {uv.name: [list(d.uv) for d in uv.data] for uv in mesh.uv_layers},
                             "edges": [list(e.vertices) for e in mesh.edges],
                             "materials": [m.name if m else None for m in mesh.materials]}
    curves = {c.name: {"properties": props(c), "materials": [m.name for m in c.materials],
                       "splines": [{"properties": props(s), "points": [props(p) for p in s.points],
                                    "bezier_points": [props(p) for p in s.bezier_points]} for s in c.splines]}
              for c in bpy.data.curves}
    # Blender does not serialize zero-user historical materials. They do not
    # belong to the active scene; source .blend bytes remain separately locked.
    materials = {m.name: {"properties": props(m), "custom": custom(m), "nodes": nodes(m.node_tree)}
                 for m in bpy.data.materials if m.users or m.use_fake_user}
    scene = bpy.context.scene
    record = {"objects": objects, "meshes": meshes, "curves": curves, "materials": materials,
              "lights": {l.name: {"properties": props(l), "nodes": nodes(l.node_tree)} for l in bpy.data.lights},
              "worlds": {w.name: {"properties": props(w), "nodes": nodes(w.node_tree)} for w in bpy.data.worlds},
              "images": {i.name: {"size": list(i.size), "colorspace": i.colorspace_settings.name,
                                    "packed_sha256": hashlib.sha256(i.packed_file.data).hexdigest() if i.packed_file else None}
                         for i in bpy.data.images if i.source == "FILE"},
              "collections": {c.name: sorted(o.name for o in c.objects) for c in bpy.data.collections},
              "view": props(scene.view_settings), "display": props(scene.display_settings),
              "world": scene.world.name, "compositor": nodes(scene.compositing_node_group),
              "node_groups": {g.name: nodes(g) for g in bpy.data.node_groups},
              "render": props(scene.render, {"resolution_x", "resolution_y", "resolution_percentage", "filepath"}),
              "image_settings": props(scene.render.image_settings, {"file_format", "color_mode", "color_depth"}),
              "cycles": props(scene.cycles, {"device", "samples", "use_adaptive_sampling", "adaptive_threshold",
                                             "use_denoising", "seed", "use_animated_seed"})}
    if raw:
        return record
    return {k: hashlib.sha256(json.dumps(v, sort_keys=True,
            default=lambda item: item.name_full if isinstance(item, bpy.types.ID) else list(item)).encode()).hexdigest()
            for k, v in record.items()}


def assert_unchanged(before, after):
    changed = [key for key in before if before[key] != after.get(key)]
    if changed:
        raise RuntimeError("Unexpected scene changes: "+", ".join(changed))


def scale_report(multiplier):
    import bpy
    reports = {}
    for name in MATERIALS:
        mat = bpy.data.materials[name]
        node = mat.node_tree.nodes[SCALE_NODE]
        actual = node.inputs["Scale"].default_value
        assert math.isclose(actual, 1.0/multiplier, rel_tol=1e-7)
        assert node.operation == "SCALE" and node.inputs[0].links[0].from_node.uv_map == "PE metric wrap"
        channels = {}
        for key in ("color", "roughness", "normal", "height"):
            texture = mat.node_tree.nodes["Photometric scan | "+key]
            assert len(texture.inputs["Vector"].links) == 1
            assert texture.inputs["Vector"].links[0].from_node == node
            assert texture.image.colorspace_settings.name == ("sRGB" if key == "color" else "Non-Color")
            channels[key] = {"image": texture.image.name, "coordinate_node": node.name,
                             "interpolation": texture.interpolation, "colorspace": texture.image.colorspace_settings.name}
        reports[name] = {"coordinate_factor": actual, "effective_tile_width_mm": mat["effective_tile_width_mm"],
                         "channels": channels}
    return reports


def run_blender(job):
    import bpy
    import resource
    import sys
    from . import locked, rendering
    from .reference_material import set_grain_scale

    output, source = Path(job["output"]), Path(job["input"])
    config = json.loads((output/"lookdev_config.json").read_text())
    canonical = json.loads((output/"effective_config.json").read_text())
    studio = json.loads((output/"studio_config.json").read_text())
    lock = json.loads((source.parent/"geometry_lock.json").read_text())
    manifest = file_manifest(source)
    manifest_path = output/"source_manifest.json"
    if manifest_path.exists():
        if json.loads(manifest_path.read_text()) != manifest:
            raise RuntimeError("Source files changed since this comparison started")
    else:
        write_json(manifest_path, manifest)
    # Technical failure recovery reuses completed images, never an expensive
    # render loop. The public CLI still refuses existing output directories.
    prior = [json.loads(line) for line in (output/"events.jsonl").read_text().splitlines()] if (output/"events.jsonl").exists() else []
    completed = {(v["variant"], v["view"]): v for v in prior if v["event"] == "render_complete"}
    results = []

    def emit(event, **fields):
        with (output/"events.jsonl").open("a") as stream:
            stream.write(json.dumps({"event": event, **fields})+"\n")
        print("GRAIN", event, json.dumps(fields), flush=True)

    baseline = None
    for label, multiplier in CANDIDATES:
        folder = output/("variant-"+label)
        folder.mkdir(exist_ok=True)
        bpy.ops.wm.open_mainfile(filepath=str(source), load_ui=False, use_scripts=False)
        locked.verify(lock["protected"])
        before = scene_snapshot()
        if baseline is None:
            baseline = before
        assert_unchanged(baseline, before)
        for name in MATERIALS:
            if bpy.data.materials[name]["tile_width_mm"] != 32:
                raise ValueError("Scene is not the expected 32 mm v007 leather baseline")
            set_grain_scale(bpy.data.materials[name], multiplier)
        channels = scale_report(multiplier)
        assert_unchanged(before, scene_snapshot())
        candidate = copy.deepcopy(config)
        candidate["leather"]["leather_grain_scale_multiplier"] = multiplier
        candidate["presets"]["preview"] = dict(PREVIEW)
        candidate["benchmark_views"] = list(VIEWS)
        for filename, data in (("lookdev_config.json", candidate), ("studio_config.json", studio),
                               ("effective_config.json", canonical), ("geometry_lock.json", lock)):
            path = folder/filename
            if path.exists():
                if json.loads(path.read_text()) != data:
                    raise RuntimeError("Existing candidate settings differ: "+str(path))
            else:
                write_json(path, data)
        scene = bpy.context.scene
        # configure() also sets look/exposure and bounces; restore these to the
        # saved baseline so this experiment changes only scale and preview settings.
        view = (scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure)
        bounces = scene.cycles.max_bounces
        rendering.configure({"presets": {"preview": PREVIEW}}, "preview", job["device"], emit)
        scene.view_settings.view_transform, scene.view_settings.look, scene.view_settings.exposure = view
        scene.cycles.max_bounces = bounces
        scene.cycles.use_animated_seed = False
        scene.camera = bpy.data.objects["CAM | reference_hero"]
        scene.render.filepath = str(folder/"reference_hero.png")
        bpy.context.preferences.filepaths.save_version = 0
        assert_unchanged(before, scene_snapshot())
        scene_path = folder/"private_edition.blend"
        if not scene_path.exists():
            bpy.ops.wm.save_as_mainfile(filepath=str(scene_path))
        times = {}
        for name in VIEWS:
            scene.camera = bpy.data.objects["CAM | "+name]
            scene.render.filepath = str(folder/(name+".png"))
            if Path(scene.render.filepath).exists():
                previous = completed.get((label, name))
                if previous is None or previous["multiplier"] != multiplier:
                    raise RuntimeError("Refusing to overwrite unverified render: "+scene.render.filepath)
                times[name] = previous["seconds"]
                emit("render_reused", variant=label, view=name)
                continue
            started = time.monotonic()
            bpy.ops.render.render(write_still=True)
            times[name] = round(time.monotonic()-started, 3)
            emit("render_complete", variant=label, multiplier=multiplier, view=name, seconds=times[name])
        assert_unchanged(before, scene_snapshot())
        locked.verify(lock["protected"])
        bpy.ops.wm.open_mainfile(filepath=str(scene_path), load_ui=False, use_scripts=False)
        assert_unchanged(before, scene_snapshot())
        scale_report(multiplier)
        locked.verify(lock["protected"])
        validation = {"variant": label, "multiplier": multiplier, "base_tile_mm": 32,
                      "effective_tile_mm": 32*multiplier, "scene_reopened": True,
                      "preserved_scene_categories": before, "only_coordinate_and_preview_changes": True,
                      "protected_fingerprint": locked.verify(lock["protected"]), "channels": channels,
                      "render_seconds": times}
        write_json(folder/"validation.json", validation)
        results.append(validation)
    if file_manifest(source) != manifest:
        raise RuntimeError("Original source files changed on disk")
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    write_json(output/"validation.json", {"sources_unchanged": True, "candidates": results,
               "render_count": 6, "peak_process_resident_mb": round(peak/(1024*1024) if sys.platform == "darwin" else peak/1024, 2)})
    emit("completed", variants=3, renders=6, sources_unchanged=True)


def finish_comparison(output):
    """Paste unchanged render pixels, enlarging preview panels by integer factors."""
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont

    config = json.loads((output/"lookdev_config.json").read_text())
    job = json.loads((output/"job.json").read_text())
    source = Path(job["input"])
    reference = ROOT/config["reference"]
    historical = source.parent.with_name(source.parent.name+"-benchmarks")/"reference_hero.png"
    sheet = output/"grain_comparison.png"
    if sheet.exists():
        raise FileExistsError("Refusing to overwrite comparison sheet")
    original = cv2.imread(str(reference), cv2.IMREAD_COLOR)
    if original is None:
        raise ValueError("Reference image missing or unreadable")
    crop = original[102:550, 30:550]
    enlarged = np.repeat(np.repeat(crop, 4, axis=0), 4, axis=1).astype(np.uint16)*257
    panel, gap, margin, header = 2080, 30, 30, 190
    canvas = np.zeros((2300, margin*2+panel*5+gap*4, 3), dtype=np.uint16)
    canvas[header+144:header+144+enlarged.shape[0], margin:margin+enlarged.shape[1]] = enlarged
    labels = [("Original Perhaps reference", "Unretouched crop; nearest-neighbor 4x; not a grain ruler")]
    inputs = [(historical, "v007 | 1.0x | 32 mm tile", "Historical 2048px / 512 samples; native pixels", 1)]
    for label, multiplier in CANDIDATES:
        inputs.append((output/("variant-"+label)/"reference_hero.png",
                       "Variant "+label.upper()+" | "+str(multiplier)+"x | "+str(int(32*multiplier))+" mm tile",
                       "1024px / 128 samples; nearest-neighbor 2x", 2))
    record = {"reference": str(reference), "reference_crop_xyxy": [30,102,550,550],
              "reference_scale": 4, "reference_sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
              "interpolation": "nearest-neighbor only", "retouching": False, "similarity_scoring": False,
              "renders": []}
    for index, (path, title, subtitle, factor) in enumerate(inputs, start=1):
        actual = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        size = 2048//factor
        if actual is None or actual.shape != (size,size,3) or actual.dtype != np.uint16:
            raise ValueError("Expected 16-bit RGB render: "+str(path))
        if index > 1:
            macro = cv2.imread(str(path.with_name("reference_leather_macro.png")), cv2.IMREAD_UNCHANGED)
            if macro is None or macro.shape != (1024,1024,3) or macro.dtype != np.uint16:
                raise ValueError("Invalid macro render")
        image = np.repeat(np.repeat(actual, factor, axis=0), factor, axis=1)
        x, y = margin+index*(panel+gap)+16, header+16
        canvas[y:y+2048,x:x+2048] = image
        labels.append((title, subtitle))
        record["renders"].append({"path":str(path), "sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                                  "factor":factor, "pixel_origin_xy":[x,y], "source_pixels_preserved": True})
    heading = Image.new("RGB", (canvas.shape[1], header), "black")
    draw = ImageDraw.Draw(heading)
    font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
    font, small = ImageFont.truetype(font_path, 45), ImageFont.truetype(font_path, 26)
    for index, (title, subtitle) in enumerate(labels):
        x = margin+index*(panel+gap)
        draw.text((x,35), title, font=font, fill=(230,230,230))
        draw.text((x,110), subtitle, font=small, fill=(170,170,170))
    canvas[:header] = np.asarray(heading)[:,:,::-1].astype(np.uint16)*257
    assert cv2.imwrite(str(sheet), canvas, [cv2.IMWRITE_PNG_COMPRESSION, 6])
    check = cv2.imread(str(sheet), cv2.IMREAD_UNCHANGED)
    for entry in record["renders"]:
        actual = cv2.imread(entry["path"], cv2.IMREAD_UNCHANGED)
        x,y = entry["pixel_origin_xy"]
        assert np.array_equal(check[y:y+2048:entry["factor"],x:x+2048:entry["factor"]], actual)
    assert np.array_equal(check[header+144:header+144+enlarged.shape[0],margin:margin+enlarged.shape[1]], enlarged)
    record["dimensions"] = [canvas.shape[1], canvas.shape[0]]
    write_json(output/"grain_comparison.json", record)
    validation = json.loads((output/"validation.json").read_text())
    seconds = sum(sum(v["render_seconds"].values()) for v in validation["candidates"])
    (output/"technical_summary.txt").write_text(
        "v008 controlled grain-scale comparison; no candidate selected.\n"
        "v007 repeats a 32 mm scan tile 4.375 times across a 140 mm planar face.\n"
        "A: 1.5x / 48 mm / 2.917 repeats. B: 2.25x / 72 mm / 1.944 repeats. C: 3x / 96 mm / 1.458 repeats.\n"
        "One UV coordinate division scales all four maps together on exterior and pressed leather. Mesh UVs unchanged.\n"
        "Normal intensity, 4-micron bump distance, roughness, dye, lights, camera data, stitching and geometry unchanged.\n"
        "No independent pore layer added; existing scanned fine detail retained. Increasing grain size also enlarges scanned pores.\n"
        "Morphology remains Leather037's angular crease network; scale alone cannot reproduce a different rounded grain shape.\n"
        "Broad v007 reflection sources, Linear image filtering, Blackman-Harris pixel filtering and denoising remain fixed;\n"
        "they may still suppress hero-scale contrast. This batch does not isolate their individual contributions.\n"
        "Integer preview enlargement preserves pixels but adds no detail; historical v007 uses different render settings.\n"
        "Didot remains provisional; no 1:1 visual-fidelity claim. No final renders or automatic winner selection.\n"
        +"Six render seconds total: "+str(round(seconds,3))+". Sources and scene preservation verified.\n")
    print("Comparison ready:", sheet)
