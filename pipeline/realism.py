"""Bounded secondary-detail refinement of the approved Variant C scene."""
import hashlib
import json
import math
from pathlib import Path
import time

from .config import ROOT
from .grain_compare import MATERIALS, scene_snapshot, scale_report, assert_unchanged, write_json

VIEWS = ("reference_hero", "reference_leather_macro", "reference_branding_macro", "reference_corner_macro")


def validate_refinement(config):
    p = config["leather"]
    if p.get("leather_grain_scale_multiplier") != 3.0 or p["source_maps"]["tile_width_mm"] != 32:
        raise ValueError("Surface refinement requires approved 3.0x / 96 mm Variant C grain")
    limits = {"pore_spacing_mm": (0.04,0.5), "pore_depth_um": (0,3), "pore_strength": (0,1),
              "pressed_micro_factor": (0,1), "roughness_variation": (0,0.05),
              "finish_spacing_mm": (0.2,5), "summit_polish": (0,0.05), "pore_roughness": (0,0.05)}
    for key, (low, high) in limits.items():
        value = p["surface_refinement"][key]
        if isinstance(value, bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not low < value <= high:
            raise ValueError("Invalid secondary surface parameter: "+key)


def source_manifest():
    folders = ["outputs/packaging/private-edition-v007", "outputs/packaging/private-edition-v007-benchmarks",
               "outputs/packaging/private-edition-v008", "outputs/packaging/canonical-v001",
               "references/packaging", "textures/sources/ambientcg_leather037_2k"]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in folders for p in sorted((ROOT/folder).rglob("*")) if p.is_file()}


def protected_snapshot(studio):
    import bpy
    record = scene_snapshot(raw=True)
    permitted_materials = set(MATERIALS)
    for spec in studio["lights"]:
        obj = bpy.data.objects["PE6 | "+spec["name"]]
        record["objects"].pop(obj.name)
        record["meshes"].pop(obj.data.name)
        permitted_materials.update(m.name for m in obj.data.materials)
    for name in permitted_materials:
        record["materials"].pop(name)
    # Historical packed maps can survive one save after their unused material
    # is dropped. Compare scene-used images; original .blend bytes stay locked.
    record["images"] = {name:data for name,data in record["images"].items()
                        if bpy.data.images[name].users or bpy.data.images[name].use_fake_user}
    return {key: hashlib.sha256(json.dumps(value, sort_keys=True,
            default=lambda item: item.name_full if isinstance(item,bpy.types.ID) else list(item)).encode()).hexdigest()
            for key,value in record.items()}


def primary_contract():
    import bpy
    result = scale_report(3.0)
    for name in MATERIALS:
        nodes = bpy.data.materials[name].node_tree.nodes
        result[name]["primary_normal_strength"] = nodes["OpenGL tangent normal"].inputs["Strength"].default_value
        bump = nodes["Restrained scan height microdepth"]
        result[name]["primary_bump"] = {k:bump.inputs[k].default_value for k in ("Strength","Distance")}
        result[name]["base_dye"] = list(nodes["Obsidian dye with espresso undertone"].inputs[1].default_value)
    return result


def verify_secondary(config):
    import bpy
    detail = config["leather"]["surface_refinement"]
    for name in MATERIALS:
        nodes = bpy.data.materials[name].node_tree.nodes
        pore = nodes["PE9 | Pores perturb the scanned leather normal"]
        assert pore.inputs["Normal"].links[0].from_node.name == "Restrained scan height microdepth"
        assert math.isclose(pore.inputs["Distance"].default_value,detail["pore_depth_um"]*1e-6,rel_tol=1e-6)
        assert nodes["Principled BSDF"].inputs["Normal"].links[0].from_node == pore
        assert nodes["Principled BSDF"].inputs["Coat Normal"].links[0].from_node == pore
        assert nodes["PE9 | Metric pore coordinates"].inputs[0].links[0].from_node.uv_map == "PE metric wrap"
        assert math.isclose(nodes["PE9 | Metric pore coordinates"].inputs["Scale"].default_value,0.032,rel_tol=1e-6)
        for node in nodes:
            if node.type == "OUTPUT_MATERIAL":
                assert not node.inputs["Displacement"].is_linked


def run_blender(job):
    import bpy
    import resource
    import sys
    from . import locked, rendering, reference_material, reference_studio

    source, output = Path(job["input"]), Path(job["output"])
    config = json.loads((output/"lookdev_config.json").read_text())
    studio = json.loads((output/"studio_config.json").read_text())
    lock = json.loads((source.parent/"geometry_lock.json").read_text())
    validate_refinement(config)
    originals = source_manifest()
    write_json(output/"source_manifest.json",originals)

    def emit(event, **fields):
        with (output/"events.jsonl").open("a") as stream:
            stream.write(json.dumps({"event":event,**fields})+"\n")
        print("REALISM",event,json.dumps(fields),flush=True)

    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    locked.verify(lock["protected"])
    before = protected_snapshot(studio)
    grain = primary_contract()
    reference_material.refine_surface(config)
    reference_studio.refine(studio)
    if primary_contract() != grain:
        raise RuntimeError("Approved primary grain/normal response/dye changed")
    verify_secondary(config)
    assert_unchanged(before,protected_snapshot(studio))
    write_json(output/"geometry_lock.json",lock)
    scene = bpy.context.scene
    view = (scene.view_settings.view_transform,scene.view_settings.look,scene.view_settings.exposure)
    bounces = scene.cycles.max_bounces

    def configure(preset):
        rendering.configure(config,preset,job["device"],emit)
        scene.view_settings.view_transform,scene.view_settings.look,scene.view_settings.exposure = view
        scene.cycles.max_bounces = bounces
        scene.cycles.use_animated_seed = False

    configure("hero")
    scene.camera = bpy.data.objects["CAM | reference_hero"]
    scene.render.filepath = str(output/"reference_hero.png")
    assert_unchanged(before,protected_snapshot(studio))
    bpy.context.preferences.filepaths.save_version = 0
    scene_path = output/"private_edition.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(scene_path))
    elapsed = {}
    for name in VIEWS:
        configure("hero" if name == "reference_hero" else "macro")
        scene.camera = bpy.data.objects["CAM | "+name]
        scene.render.filepath = str(output/(name+".png"))
        start = time.monotonic()
        bpy.ops.render.render(write_still=True)
        elapsed[name] = round(time.monotonic()-start,3)
        emit("render_complete",view=name,seconds=elapsed[name],path=scene.render.filepath)
    assert_unchanged(before,protected_snapshot(studio))
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    verify_saved(job,round(peak/(1024*1024) if sys.platform=="darwin" else peak/1024,2))
    emit("completed",renders=4,seconds=round(sum(elapsed.values()),3),sources_unchanged=True)


def verify_saved(job, peak_mb=None):
    """Read-only verification also permits recovery without repeating renders."""
    import bpy
    from . import locked
    source,output = Path(job["input"]),Path(job["output"])
    config = json.loads((output/"lookdev_config.json").read_text())
    studio = json.loads((output/"studio_config.json").read_text())
    lock = json.loads((source.parent/"geometry_lock.json").read_text())
    originals = json.loads((output/"source_manifest.json").read_text())
    if source_manifest() != originals:
        raise RuntimeError("Original source files changed")
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    before,grain = protected_snapshot(studio),primary_contract()
    bpy.ops.wm.open_mainfile(filepath=str(output/"private_edition.blend"),load_ui=False,use_scripts=False)
    assert_unchanged(before,protected_snapshot(studio))
    verify_secondary(config)
    if primary_contract() != grain:
        raise RuntimeError("Approved primary grain/normal response/dye changed")
    events = [json.loads(line) for line in (output/"events.jsonl").read_text().splitlines()]
    rendered = [e for e in events if e["event"] == "render_complete"]
    if len(rendered) != 4 or {e["view"] for e in rendered} != set(VIEWS):
        raise RuntimeError("Expected exactly the four benchmark renders")
    elapsed = {e["view"]:e["seconds"] for e in rendered}
    report = {"approved_variant":"C", "grain_multiplier":3.0,"effective_tile_mm":96,
              "primary_contract":grain,"primary_normal_strength_and_dye_unchanged":True,
              "protected_scene_categories":before,"geometry_finishing_cameras_preserved":True,
              "protected_fingerprint":locked.verify(lock["protected"]),"scene_reopened":True,
              "sources_unchanged":True,"lighting":studio["lights"],"secondary_detail":config["leather"]["surface_refinement"],
              "render_seconds":elapsed,"render_count":4,
              "peak_process_resident_mb":peak_mb}
    write_json(output/"validation.json",report)
    return report


def finish_realism(output):
    from .contact_sheet import create_history
    create_history(ROOT/"references/packaging/06_private_edition.png", [
        (ROOT/"outputs/packaging/private-edition-v007-benchmarks/reference_hero.png","v007 | 32 mm repeat"),
        (ROOT/"outputs/packaging/private-edition-v008/variant-c/reference_hero.png","v008 C | approved 96 mm repeat"),
        (output/"reference_hero.png","v009 | secondary surface refinement")], output/"hero_comparison.png")
    (output/"technical_summary.txt").write_text(
        "v009: Variant C primary grain remains 3.0x, 96 mm repeat, all PBR channels aligned.\n"
        "Existing scan normal strength, primary height bump, dye, geometry, UVs, wordmark, stitches and all camera data unchanged.\n"
        "Secondary pores: irregular 2D follicle pits at 0.14 mm spacing, 0.8 um height distance, strength 0.35; pressed leather at 45% strength.\n"
        "The pore Bump node receives the scanned normal stack; no color mixing of normals and no structural displacement.\n"
        "Source roughness gain/offset: 0.4/0.28 -> 0.6/0.205, retaining an approximately 0.434 median before layering.\n"
        "Added height-aligned summit polish +/-0.012, 1.2 mm finish variation +/-0.012, pore roughness up to +0.018; range clamped 0.30-0.60.\n"
        "Coat weight 0.025 -> 0.01; sheen 0.025 -> 0.012. Pigment and exposure unchanged.\n"
        "Existing softboxes only: narrower front/left cards with lower energy; repositioned top card; camera fill reduced 0.12 -> 0.045; band source 0.003 -> 0.004.\n"
        "Black world and restrained floor response unchanged. No new rig, camera, metal shader or finishing geometry.\n"
        "One four-view Cycles Metal benchmark: hero 2048 px, macros 1536 px, 256 samples, threshold 0.005, denoising, 16-bit PNG.\n"
        "Limits: Leather037 still has an angular crease morphology; synthetic follicle pits approximate rather than measure real leather pores.\n"
        "Approved corners/bevels and provisional Didot differ from reference construction/branding. Material and lighting remain artist-calibrated assumptions.\n"
        "Visual fidelity requires manual review; successful execution does not imply near 1:1 matching.\n")
