"""Lighting checks on a saved floating-presentation job scene (read-only: never saves a scene).

    python3 -B -m pipeline.rig_check passes JOB_ID [IMAGE]   # low-res isolated light passes + per-face luminance -> outputs/jobs/JOB_ID/diag/
    python3 -B -m pipeline.rig_check verify JOB_ID --against SRC.blend   # reopen saved scene: active lights, camera, product/material fingerprint vs SRC

Host side uses the shared GPU/Blender slots from pipeline.jobs. Blender side runs this same file.
Luminance numbers are display-referred PNG values (0..1, Standard view) averaged over projected face cells: a lighting-structure
measurement (gradient, side/front ratio, underside level, edge peak), not a quality judgement.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BORDER = (0.1667, 0.8333)  # vertical render border used by every float job
BOX = (-0.07, 0.07, -0.07, 0.07, 0.0, 0.14)  # product-frame x0,x1,y0,y1,z0,z1 (pivot z 0.07)
PASSES = {"key": ("01",), "edge_side": ("02", "03"), "bounce": ("04",), "all": ("01", "02", "03", "04")}


def host(args):
    import subprocess
    from contextlib import nullcontext
    from pipeline.cli import detect_blender
    from pipeline.jobs import JOBS, slot
    out = JOBS / args.job
    out.joinpath("diag").mkdir(exist_ok=True)
    task = out / "diag" / (args.mode + ".task.json")
    task.write_text(json.dumps({"mode": args.mode, "scene": str(out / "stage.blend"), "out": str(out / "diag"),
                                "image": args.image or str(out / "preview.png"), "against": args.against}))
    cmd = [detect_blender({}), "--background", "--factory-startup", "--disable-autoexec", "--python-exit-code", "1",
           "--python", str(ROOT / "pipeline/rig_check.py"), "--", str(task)]
    with (slot("gpu", 1, args.job, args.mode) if args.mode == "passes" else nullcontext()), slot("blender", 2, args.job, args.mode):
        log = out / "logs" / ("rig_" + args.mode + ".log")
        with open(log, "w") as f:
            code = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT)
    print(json.dumps({"job": args.job, "mode": args.mode, "exit": code, "result": str(out / "diag" / (args.mode + ".json")), "log": str(log.relative_to(ROOT))}))
    return code


def measure(scene, image_path):
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    img = bpy.data.images.load(str(image_path))
    img.colorspace_settings.name = "Non-Color"  # raw display values
    w, h = img.size
    px = list(img.pixels)
    cam, pose = scene.camera, bpy.data.objects["PRESENT | pose"]
    pivot_z = pose.location.z

    def lum(x, y):
        i = (int(max(0, min(h - 1, y))) * w + int(max(0, min(w - 1, x)))) * 4
        return (px[i] + px[i + 1] + px[i + 2]) / 3

    def project(p):
        v = world_to_camera_view(scene, cam, pose.matrix_world @ (Vector(p) - Vector((0, 0, pivot_z))))
        return v.x * w, (v.y - BORDER[0]) / (BORDER[1] - BORDER[0]) * h

    def grid(c00, c10, c01, c11, n, m):
        rows = []
        for j in range(m):
            row = []
            for i in range(n):
                vals = []
                for a in (0.25, 0.5, 0.75):
                    for b in (0.25, 0.5, 0.75):
                        u, v = 0.08 + (i + a) / n * 0.84, 0.08 + (j + b) / m * 0.84
                        vals.append(lum(*project([(1 - u) * (1 - v) * c00[k] + u * (1 - v) * c10[k] + (1 - u) * v * c01[k] + u * v * c11[k] for k in range(3)])))
                row.append(sum(vals) / len(vals))
            rows.append(row)
        return rows

    def edge(a, b, n=24, inward=(0, -12), absolute=False):
        """highlight excess along an edge: brightest pixel within 3 px of the edge minus the face level 12 px inside it (absolute: no subtraction)."""
        vals = []
        for k in range(n):
            t = 0.06 + 0.88 * k / (n - 1)
            x, y = project([a[i] + (b[i] - a[i]) * t for i in range(3)])
            vals.append(max(0.0, max(lum(x + dx, y + dy) for dx in (-3, 0, 3) for dy in (-3, 0, 3)) - (0 if absolute else lum(x + inward[0], y + inward[1]))))
        return [round(v, 3) for v in vals]

    x0, x1, y0, y1, z0, z1 = BOX
    mean = lambda g: sum(map(sum, g)) / sum(map(len, g))
    lid = grid((x0, y0, .03), (x1, y0, .03), (x0, y0, z1), (x1, y0, z1), 8, 4)
    side = grid((x1, y0, .005), (x1, y1, .005), (x1, y0, z1), (x1, y1, z1), 6, 3)
    under = grid((x0, y0, 0), (x1, y0, 0), (x0, y1, 0), (x1, y1, 0), 6, 4)
    cols = [sum(r[i] for r in lid) / 4 for i in range(8)]
    scols = [sum(r[i] for r in side) / 3 for i in range(6)]  # front edge -> rear
    urows = [sum(r) / 6 for r in under]  # front -> rear
    top_edge = edge((x0, y0, z1), (x1, y0, z1))
    top_abs = edge((x0, y0, z1), (x1, y0, z1), absolute=True)
    res = {"front_lid_mean": mean(lid), "front_cols_left_to_right": cols, "front_left_right_ratio": max(cols[:3]) / max(1e-6, min(cols[5:])),
           "front_rows_top_to_bottom": [sum(r) / 8 for r in reversed(lid)], "wordmark_zone_contrast": max(map(max, lid)) / max(1e-6, min(map(min, lid))),
           "side_mean": mean(side), "side_cols_front_to_rear": scols, "side_over_front": mean(side) / max(1e-6, mean(lid)),
           "underside_mean": mean(under), "underside_rows_front_to_rear": urows, "underside_max_cell": max(map(max, under)),
           "top_front_edge_profile": top_edge, "top_front_edge_abs_profile": top_abs, "top_front_edge_abs_peak": max(top_abs), "top_front_edge_excess_peak": max(top_edge), "top_front_edge_lit_fraction": sum(v > 0.12 for v in top_edge) / len(top_edge),
           "left_vertical_edge_peak": max(edge((x0, y0, .03), (x0, y0, z1), inward=(12, 0))),
           "frame_mean": sum(px[i] + px[i + 1] + px[i + 2] for i in range(0, len(px), 4)) / (3 * w * h)}
    bpy.data.images.remove(img)

    def rnd(o):
        return [rnd(x) for x in o] if isinstance(o, list) else {k: rnd(v) for k, v in o.items()} if isinstance(o, dict) else round(o, 4) if isinstance(o, float) else o
    return rnd(res)


def rig_lights():
    """[(pass id, light object)] for the active lights: PCS* rigs by their number, FLOAT rigs by role (key 01, edge 02, side 03, bounce 04)."""
    import bpy
    roles = (("Key", "01"), ("Edge", "02"), ("Side", "03"), ("Underside", "04"))
    out = []
    for o in bpy.data.objects:
        if o.type != "LIGHT" or o.hide_render:
            continue
        if o.name.startswith("PCS") and o.name[4:7] == " | ":
            out.append((o.name[7:9], o))
        elif o.name.startswith("FLOAT | "):
            out.append(next((i for r, i in roles if r in o.name), "05") and (next((i for r, i in roles if r in o.name), "05"), o))
    return out


def passes(task):
    import bpy
    from pipeline.job_entry import use_metal
    out = Path(task["out"])
    bpy.ops.wm.open_mainfile(filepath=task["scene"], load_ui=False, use_scripts=False)
    scene, lights = bpy.context.scene, rig_lights()
    use_metal()
    scene.cycles.samples, scene.cycles.use_adaptive_sampling, scene.cycles.adaptive_threshold = 48, True, 0.02
    scene.render.resolution_percentage = 40
    scene.render.use_border = scene.render.use_crop_to_border = True
    scene.render.border_min_x, scene.render.border_max_x, scene.render.border_min_y, scene.render.border_max_y = 0, 1, *BORDER
    scene.render.image_settings.file_format, scene.render.image_settings.color_mode, scene.render.image_settings.color_depth = "PNG", "RGB", "8"
    result = {}
    for name, ids in PASSES.items():
        for k, o in lights:
            o.hide_render = k not in ids
        bpy.ops.render.render(write_still=False)
        path = out / ("pass-%s.png" % name)
        bpy.data.images["Render Result"].save_render(str(path), scene=scene)
        result[name] = measure(scene, path)
    if task.get("image") and Path(task["image"]).is_file():  # the rendered frame the designer reviews, measured with the same face grid
        for _, o in lights:
            o.hide_render = False
        result["rendered_image"] = {"file": task["image"], **measure(scene, task["image"])}
    (out / "passes.json").write_text(json.dumps(result, indent=1))


def fingerprint():
    """Hashes of everything that must not change between the source and the saved presentation scene."""
    import hashlib
    import bpy
    from array import array

    def h(*parts):
        return hashlib.sha256(repr(parts).encode()).hexdigest()[:16]

    def val(v):
        return [round(x, 6) for x in v] if hasattr(v, "__len__") and not isinstance(v, str) else round(v, 6) if isinstance(v, float) else v
    objs, mats, imgs = {}, {}, {}
    for o in bpy.data.objects:
        if o.type == "LIGHT":
            continue
        d = {"type": o.type, "parent": o.parent.name if o.parent else None, "basis": [val(r) for r in o.matrix_basis], "hide_render": o.hide_render,
             "mats": [s.material.name if s.material else None for s in o.material_slots]}
        if o.type == "MESH":
            v = array("f", [0.0]) * (len(o.data.vertices) * 3)
            o.data.vertices.foreach_get("co", v)
            d["mesh"] = h(v.tobytes(), len(o.data.polygons), [m.name for m in o.data.materials])
        if o.type == "CAMERA":
            d["lens"], d["shift"] = o.data.lens, [o.data.shift_x, o.data.shift_y]
        objs[o.name] = d
    for m in bpy.data.materials:
        if m.node_tree:
            nodes = [(n.bl_idname, n.name, [(i.name, val(i.default_value)) for i in n.inputs if hasattr(i, "default_value")], n.image.name if getattr(n, "image", None) else None)
                     for n in sorted(m.node_tree.nodes, key=lambda n: n.name)]
            mats[m.name] = h(nodes, sorted((l.from_node.name, l.from_socket.name, l.to_node.name, l.to_socket.name) for l in m.node_tree.links))
    for i in bpy.data.images:
        imgs[i.name] = h(tuple(i.size), i.colorspace_settings.name, len(i.packed_file.data) if i.packed_file else i.filepath)
    s, v, c = bpy.context.scene, bpy.context.scene.view_settings, bpy.context.scene.cycles
    w = s.world.node_tree.nodes["Background"].inputs
    scene = {"engine": s.render.engine, "view": v.view_transform, "look": v.look, "exposure": v.exposure, "gamma": v.gamma, "bounces": c.max_bounces,
             "res": [s.render.resolution_x, s.render.resolution_y], "world": [val(w["Color"].default_value), w["Strength"].default_value], "camera": s.camera.name}
    return {"objects": objs, "materials": mats, "images": imgs, "scene": scene}


def verify(task):
    import math
    import bpy
    bpy.ops.wm.open_mainfile(filepath=task["against"], load_ui=False, use_scripts=False)
    before = fingerprint()
    bpy.ops.wm.open_mainfile(filepath=task["scene"], load_ui=False, use_scripts=False)
    after = fingerprint()
    s = bpy.context.scene
    layer_excluded = {lc.name for lc in bpy.context.view_layer.layer_collection.children if lc.exclude}
    active, off = [], []
    for o in bpy.data.objects:
        if o.type != "LIGHT":
            continue
        d = o.data
        row = {"name": o.name, "collections": [c.name for c in o.users_collection], "hide_render": o.hide_render, "energy_w": round(d.energy, 4),
               "loc_m": [round(x, 4) for x in o.matrix_world.translation], "rot_deg": [round(math.degrees(a), 1) for a in o.matrix_world.to_euler()],
               "shape": d.shape, "size_m": [round(d.size, 4), round(d.size_y, 4)], "spread_deg": round(math.degrees(d.spread), 1), "color": [round(x, 3) for x in d.color],
               "visible_camera": o.visible_camera}
        (active if not o.hide_render and not all(c.name in layer_excluded for c in o.users_collection) else off).append(row)
    diff = {k: sorted(n for n in set(before[k]) | set(after[k]) if before[k].get(n) != after[k].get(n)) for k in ("objects", "materials", "images")}
    diff["scene"] = [k for k in before["scene"] if before["scene"][k] != after["scene"][k]]
    cam = s.camera
    result = {"scene_file": task["scene"], "engine": s.render.engine, "camera": cam.name, "camera_loc_m": [round(x, 4) for x in cam.matrix_world.translation],
              "camera_rot_deg": [round(math.degrees(a), 2) for a in cam.matrix_world.to_euler()], "lens_mm": cam.data.lens,
              "view_transform": s.view_settings.view_transform, "exposure": s.view_settings.exposure,
              "active_lights": active, "disabled_lights": len(off), "disabled_collections_excluded": sorted(layer_excluded),
              "all_disabled_really_off": all(r["hide_render"] for r in off), "unchanged_vs_source": diff, "all_unchanged": not any(diff.values())}
    Path(task["out"], "verify.json").write_text(json.dumps(result, indent=1))


def main():
    try:
        import bpy  # noqa: F401
    except ImportError:
        import argparse
        p = argparse.ArgumentParser()
        p.add_argument("mode", choices=("passes", "verify"))
        p.add_argument("job")
        p.add_argument("image", nargs="?")
        p.add_argument("--against")
        sys.path.insert(0, str(ROOT))
        sys.exit(host(p.parse_args()))
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(ROOT))
    task = json.loads(Path(sys.argv[sys.argv.index("--") + 1]).read_text())
    {"passes": passes, "verify": verify}[task["mode"]](task)


if __name__ == "__main__":
    main()
