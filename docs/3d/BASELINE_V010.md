> **Historical.** The v010 outputs referenced below were removed in the workspace cleanup ([WORKSPACE_CLEANUP.md](WORKSPACE_CLEANUP.md)). Its canonical geometry survives as `assets/canonical/box_base.blend` + `geometry_lock.json`.

# Private Edition v010 baseline

**Status: designer-selected best baseline**, as stated in the current preservation
request. It remains a reference for reproduction and future work, not a certified
pixel-perfect match or 90–95% visual approval. Historical `manual_review.json` and
validation records still say approval pending; they are preserved as execution-time
evidence rather than rewritten to change history.

Audit date: **2026-10-29, Asia/Jakarta**. The root was confirmed as
`/Users/admin/Documents/perhaps-3d-assets`. See the [SOP](PRODUCTION_WORKFLOW.md) for
workflow policy and [design contract](REFERENCE_AND_ASSET_SPECS.md) for tier intent.

## Authoritative artifacts

All paths here are relative to the project root. The v010 output root is
`outputs/packaging/private-edition-v010/`.

| Role | Actual artifact |
| --- | --- |
| Final editable scene | [private_edition_calibrated.blend](../../outputs/packaging/private-edition-v010/private_edition_calibrated.blend), 342,809,381 bytes |
| Earlier studio scene, not final | [private_edition.blend](../../outputs/packaging/private-edition-v010/private_edition.blend) |
| Earlier neutral material scene | [calibration/material.blend](../../outputs/packaging/private-edition-v010/calibration/material.blend) |
| Approved geometry source | [canonical-v001/canonical_box.blend](../../outputs/packaging/canonical-v001/canonical_box.blend) |
| Production reconstruction input | [v009/private_edition.blend](../../outputs/packaging/private-edition-v009/private_edition.blend) |
| Working full config | [config/private_edition_production.json](../../config/private_edition_production.json) |
| Frozen final-stage full config | [config_final.json](../../outputs/packaging/private-edition-v010/config_final.json) |
| Split material / lighting snapshots | [material_config.json](../../outputs/packaging/private-edition-v010/material_config.json), [studio_config.json](../../outputs/packaging/private-edition-v010/studio_config.json); these are not complete CLI configs |
| Source / qualification record | [source_manifest.json](../../outputs/packaging/private-edition-v010/source_manifest.json), [qualification/source_selection.json](../../outputs/packaging/private-edition-v010/qualification/source_selection.json) |
| Production source / frozen copy | [pipeline/production.py](../../pipeline/production.py), [production_script_snapshot.py](../../outputs/packaging/private-edition-v010/production_script_snapshot.py); SHA-256 values match at audit |
| Original design | [06_private_edition.png](../../references/packaging/06_private_edition.png) |
| Review comparison and provenance | [hero_comparison.png](../../outputs/packaging/private-edition-v010/hero_comparison.png), [hero_comparison.json](../../outputs/packaging/private-edition-v010/hero_comparison.json) |
| Technical summary | [implementation_summary.txt](../../outputs/packaging/private-edition-v010/implementation_summary.txt) |
| Preservation evidence | [geometry_lock.json](../../outputs/packaging/private-edition-v010/geometry_lock.json), [uv_validation.json](../../outputs/packaging/private-edition-v010/uv_validation.json), [validation.json](../../outputs/packaging/private-edition-v010/validation.json), [history_sha256.json](../../outputs/packaging/private-edition-v010/history_sha256.json) |
| Render evidence | [events.jsonl](../../outputs/packaging/private-edition-v010/events.jsonl), [artifact_validation.json](../../outputs/packaging/private-edition-v010/artifact_validation.json) and stage logs/status files listed in the manifest below |

The saved final scene was opened in a fresh Blender CLI process during this audit.
No render, save, control posing or material reconstruction was called. Its shader
connections, packed map sizes/color spaces, cameras, reflection-card geometry,
world and render settings were inspected directly. `locked.verify()` returned
`81e2f2c9459e4e40f7cbb431792d920feba8ff9ef582b3449cdb69ef064ebf00`, matching the
historical v010 validation fingerprint. This is a protected-data digest, not a file
checksum or visual score.

## Canonical geometry and finishing

Scene units are meters with metric display. Front is −Y, rear +Y, left −X and Z up.
Approved dimensions come from [packaging.json](../../config/packaging.json) and the
[canonical validation](../../outputs/packaging/canonical-v001/validation.json):
140 × 140 × 140mm, 2.5mm shell wall, base seam 22mm at front / 105mm at rear,
5mm reveal, 2mm collar wall, 0.5mm collar clearance, 10mm engagement, 1.2mm tray.
These are documented design assumptions, not manufacturer measurements.

| Protected object | Parent / closed world origin (meters) | Verified edge modifier |
| --- | --- | --- |
| `CTRL \| Base` | No parent; `(0,0,0)` | Empty control |
| `CTRL \| Lid lift-off` | No parent; `(0,0,0.13875)` | Empty control; free lift-off |
| `Box \| Base shell` | Base control; `(0,0,0)` | 0.6mm bevel, 4 segments; weighted normals |
| `Box \| Lid shell` | Lid control; `(0,0,0.13875)` | 0.6mm bevel, 4 segments; weighted normals |
| `Box \| Interior collar and reveal` | Base control; `(0,0,0)` | 0.5mm bevel, 4 segments; weighted normals |
| `Box \| Interior tray floor` | Base control; `(0,0,0)` | 0.3mm bevel, 4 segments; weighted normals |

The four structural mesh objects have local location/rotation zero and unit scale.
Keep their local origins, parent relationships and inverse matrices. The canonical
raw mesh digest recorded in validation is
`5f760839d0032b920add29dff6a9c441bc0da403c0fadc36090f418efafc6825`.
The branding guide is retained at front/lower-lid placement. No structural geometry
was rebuilt for v010.

The canonical base/lid shells are hidden for rendering. Visible nonstructural meshes
are `PE6 | Continuous base leather wrap` and `PE6 | Continuous lid leather wrap`.
Their local transforms remain identity and their parents remain the original
controls. `PE6 | Inset leather stitching` is a separate curve parented to the lid.
Do not delete the hidden originals or casually regenerate the appearance wraps.

v010's allowed finishing changes were confined to these appearance treatments:
existing letter floors moved from approximately 0.09mm to 0.20mm recess depth;
weighted die-lip bevel became 0.035mm / 4 segments; stitch length became 1mm with
0.045mm radius while retaining original centers/path and approximately 1.4mm pitch.
The reference-style lowercase Didot reconstruction keeps its placement and outline.
It remains provisional; no approved Perhaps vector was identified in the available
project records. Do not call this an official wordmark.

## Actual leather source and shader

Selected provider asset: **Poly Haven Leather Red 02**, Rob Tuytel, with CC0-1.0
license and source links recorded in the local manifest:
[material source](https://polyhaven.com/a/leather_red_02),
[license](https://polyhaven.com/license). URLs/license metadata were verified from
the preserved source record; no new download or online license audit occurred here.
Capture technique and absolute relief depth are **Unverified**.

Original maps live under
`textures/sources/polyhaven_leather_red_02_8k/`. All are 8192 × 8192 and packed in
the final scene; the shader uses Linear interpolation and Repeat extension.

| File suffix after `leather_red_02_` | Color space | Actual shader role |
| --- | --- | --- |
| `coll1_8k.png` | sRGB | Photographic color → luminance → bounded local pigment variation → obsidian dye |
| `rough_8k.png` | Non-Color | Source roughness remapped with clamped SMOOTHERSTEP |
| `nor_gl_8k.png` | Non-Color | Supplied OpenGL tangent normal, UV `PE metric wrap`, into BSDF Normal and Coat Normal |
| `disp_8k.png` | Non-Color | Packed, shares coordinates, **unconnected**; no height/bump/displacement contribution |

Both `PE6 | Scanned obsidian leather` and `PE6 | Pressed leather` use
`Original metric wrap UV` → `Physical source repeat` (Vector Math SCALE) → all four
image vectors. The preserved UV density is 32mm per UV unit. The factor is
`32 / 400 = 0.08`, giving a **400mm physical repeat** uniformly on the wraps.
The old 3× / 96mm Leather037 repeat is not the v010 scale.

The provider's published width is 600mm; 400mm is an artistic calibration for this
source's grain morphology on a 140mm box. It is not a new measured source size.
At this repeat the original 8K image provides approximately 48.8µm per texel.
Historical UV verification sampled 27 lid / 20 base planar edges, reporting
31.99998–32.00001mm per UV unit with matching pre/post UV hashes and unit object
scales. Shared scaling preserves map alignment and density; it does not guarantee
every manufactured wrap seam is visually invisible.

| Parameter | Exterior | Pressed lettering |
| --- | --- | --- |
| Linear dye basis | `(0.0048, 0.0043, 0.0040)` | Same basis × 0.65 |
| Photographic luminance input / pigment factors | `[0.010, 0.093]` → `[0.55, 1.35]` | Same |
| Roughness source range | `[0.365, 0.624]` | Same |
| Roughness output range | `[0.32, 0.52]` | `[0.265, 0.465]` (−0.055 offset) |
| Supplied normal strength | 0.6 | 0.35 |
| IOR / Specular IOR Level | 1.46 / 0.5 | Same |
| Coat weight / roughness | 0.02 / 0.35 | Same |
| Sheen / diffuse roughness | 0 / 0.1 | Same |

Primary rounded grain and smaller pores both come from the supplied normal map.
There is no new procedural secondary pore layer, duplicate height bump, structural
displacement or manufactured "measured" PBR data. The source height is smoother
and dominated by broad valleys; stacking it was deliberately avoided.

The collar's retained `PE | Dark graphite brushed inlay.001` material is metallic
1.0, linear color `(0.13,0.125,0.12)`, controlled roughness 0.32–0.42 and anisotropy
0.65. Existing directional machining/tangent and fine bump logic is inherited;
v010 changes its response parameters, not the approved reveal geometry.

## Final studio and cameras

The baseline inherits its black world, ground and earlier material bindings from
the v009 scene. v010 has its own final material and light parameters; it does not
inherit Leather037 or the old light powers as its final configuration.

The five active `PE6 | ...` photography sources are emissive mesh cards with
camera visibility disabled. `reference_studio.refine()` converts each config
power to the energy multiplier `2 * power / (width * height * pi)` beneath a fixed
silk UV falloff. Position, aim target and dimensions are meters; power is the
implementation's input, not a direct Blender area-light wattage.

| Card name after `PE6 \|` | Position | Target | Size | Power |
| --- | --- | --- | --- | --- |
| Front silk reflection | `(0.28,-0.30,0.20)` | `(0,-0.06,0.08)` | `0.22 × 0.65` | 0.85 |
| Left silk reflection | `(-0.30,0.22,0.20)` | `(-0.06,0,0.085)` | `0.20 × 0.55` | 0.60 |
| Top reflection card | `(0.38,0.28,0.25)` | `(0,0,0.14)` | `0.22 × 0.25` | 0.04 |
| Quiet camera fill | `(-0.45,-0.40,0.30)` | `(0,0,0.075)` | `0.30 × 0.35` | 0.025 |
| Low inlay reflection | `(0.06,-0.11,0.010)` | `(0,-0.067,0.025)` | `0.12 × 0.025` | 0.009 |

World Background is `(0,0,0,1)`, strength 0. The ground is inherited rather than
rebuilt by production stages; historical studio configuration records a very dark
floor with restrained reflection. The exact active floor node values were not
re-inspected in this audit and are **Unverified here**; recover the saved scene
rather than substituting the generic packaging floor preset.

The scene contains 19 cameras: 15 preserved presets and 4 added production cameras.
All four new cameras have depth of field disabled. `studio.aim()` derives rotation
from position and target rather than hand-entered Euler values.

| Camera | Type / framing | Position, meters |
| --- | --- | --- |
| `CAM \| production_hero` | Perspective, 200mm lens; target `(0,0,0.075)`, elevation about 12° | `(-1.05,-0.80,0.355)` |
| `CAM \| production_leather_macro` | Orthographic 50mm field | `(-0.15,-0.23,0.15)` |
| `CAM \| production_branding_macro` | Orthographic 96mm field | `(-0.12,-0.33,0.12)` |
| `CAM \| production_corner_macro` | Orthographic 50mm field | `(-0.15,-0.18,0.18)` |

Macro orientations are copied from their `reference_*` cameras in the v009 input;
their exact saved rotations remain in the Blender scene. The original 150mm
`reference_hero` and all technical cameras remain available.

## Rendering and historical execution

The final scene directly confirms Cycles, GPU, 2048² at 100%, 512 samples, adaptive
threshold 0.003, denoising, seed 42, 1px filter, 12 bounces, Standard / None,
exposure −0.25, gamma 1, PNG 16-bit and `CAM | production_hero`, with render borders
disabled. `production.render()` selects Metal explicitly and enables the light
tree. Current discovery enumerated Apple M4 CPU and Apple M4 10-core Metal GPU.

| Actual outputs under v010 | Resolution / format |
| --- | --- |
| [hero.png](../../outputs/packaging/private-edition-v010/hero.png), [hero.exr](../../outputs/packaging/private-edition-v010/hero.exr) | 2048²; 16-bit RGB PNG / half-float scene-linear EXR, ZIP |
| [leather_macro.png](../../outputs/packaging/private-edition-v010/leather_macro.png), [leather_macro.exr](../../outputs/packaging/private-edition-v010/leather_macro.exr) | 1536²; same formats |
| [branding_macro.png](../../outputs/packaging/private-edition-v010/branding_macro.png), [branding_macro.exr](../../outputs/packaging/private-edition-v010/branding_macro.exr) | 1536²; same formats |
| [corner_macro.png](../../outputs/packaging/private-edition-v010/corner_macro.png), [corner_macro.exr](../../outputs/packaging/private-edition-v010/corner_macro.exr) | 1536²; same formats |

All final views use 512 samples / threshold 0.003 / denoising. Four diagnostic
borders used the corresponding final frame pixel density at 256 samples.
Historical events record 48.722 seconds of crops and 381.705 seconds for the four
final renders (hero 100.201s, leather 85.110s, branding 101.629s, corner 94.765s).
These are one-run timings on this machine, not a speed guarantee or CPU comparison.

All five stage status JSONs report success/exit 0. `artifact_validation.json`
records 15 tests passed, four crops, four final views, expected image headers and
reopen/preservation checks. This audit used existing logs and opened the final
scene; it did not rerun those tests or any production/render stage.

The comparison is 4300 × 2300. Its provenance records original reference crop
`[30,102,550,550]`, nearest-neighbor 4× enlargement, native 2048² 16-bit hero pixels,
no color change, warping, retouching or automatic scoring. The full original sheet
is separately preserved. The screenshot pixel grid is not a material measurement.

### Stage configs are not interchangeable

`config_material.json` and `config_studio.json` record the initial normal strength
1.0 and top-card power 0.09. After cropped diagnostics, `config_calibrate.json`,
`config_final.json` and `config_verify.json` record 0.6 and 0.04 and specify
`final_scene: private_edition_calibrated.blend`.

The current working config contains the final calibrated values. Starting all
stages with it can reproduce the intended final settings, but not the original
diagnostic history. Use the archived per-stage configs below for the closest
available procedural replay. The saved scene is the most direct baseline recovery.

## Decisions worth preserving

| Evidence / iteration | Decision for future agents |
| --- | --- |
| v007: Leather037, 32mm repeat | Angular crease morphology and grain that disappeared at hero scale |
| v008: A/B/C controlled scale comparison | Designer selected C: 3× / 96mm for **that source**; changing frequency did not change morphology |
| v009: extra procedural microdetail and roughness layering | Retained source still looked angular/soft; additional shader complexity did not resolve source mismatch |
| v010 qualification | Original Red 02 maps selected over Leather White's finer/flatter response; Leather037 rejected for angular network; unavailable Leather038 was not map-qualified |
| v010 reconstruction | Use original 8K source normal for rounded grain plus pores; avoid duplicate smooth height bump; calibrate physical repeat for this source |
| v010 bounded correction | Reduce normal from 1.0 to 0.6 and top-card power from 0.09 to 0.04; do not run another broad full-frame iteration loop |

Qualification evidence is retained in
[textures/sources/private-edition-qualification/](../../textures/sources/private-edition-qualification)
and the v010 selection record. Source suitability precedes scaling, noise or samples.

## Recovery and reproduction

### Recover the preferred baseline

Restore/copy the project with the canonical master, final v010 directory, referenced
PBR source directory, v009 input and pipeline/config files. Preserve filenames and
relative layout; use the integrity table below before changing anything. The final
scene has all four original 8K maps packed, so external absolute image paths from
the old workstation need not resolve merely to open the master. External originals
are still needed to rebuild the material stage, which verifies their SHA-256 values.

Set `BLENDER_BIN` to a compatible Blender executable if detection differs, and run
the non-rendering `pipeline check` described in the [entry point](README.md). Metal
production is verified on this Mac only. A non-Metal port requires an explicitly
authorized implementation change; there is no production `--device cpu` option.

The comparison utility hardcodes macOS Arial. Rebuilding provisional text through
legacy finishing code uses macOS Didot. Those portability limits do not prevent
inspection of the final packed/baked scene. Do not install fonts or dependencies
without a task-specific reason.

### Procedural replay into a new directory

**For a future authorized reproduction, not for a documentation audit.** The command
interfaces and historical stage success are confirmed; this parameterized replay
was not executed here. Pixel-identical output across drivers/Blender versions is
unverified even with the same seed.

From the copied project root, create per-stage full configs with a new output.
The example below fails if its output already exists and changes no original config:

```sh
rtk proxy python3 -B - <<'PY'
import json
from pathlib import Path

root = Path.cwd()
baseline = root / "outputs/packaging/private-edition-v010"
output = root / "outputs/packaging/private-edition-v010-reproduction"
output.mkdir(parents=True, exist_ok=False)
for stage in ("material", "studio", "calibrate", "final", "verify"):
    config = json.loads((baseline / f"config_{stage}.json").read_text())
    config["input"] = "outputs/packaging/private-edition-v009/private_edition.blend"
    config["output"] = str(output.relative_to(root))
    config["final_scene"] = "private_edition_calibrated.blend"
    (output / f"reproduce_{stage}.json").write_text(json.dumps(config, indent=2) + "\n")
PY
rtk proxy python3 -B -m pipeline.production material --config outputs/packaging/private-edition-v010-reproduction/reproduce_material.json
rtk proxy python3 -B -m pipeline.production studio --config outputs/packaging/private-edition-v010-reproduction/reproduce_studio.json
rtk proxy python3 -B -m pipeline.production calibrate --config outputs/packaging/private-edition-v010-reproduction/reproduce_calibrate.json
rtk proxy python3 -B -m pipeline.production final --config outputs/packaging/private-edition-v010-reproduction/reproduce_final.json
rtk proxy python3 -B -m pipeline.production verify --config outputs/packaging/private-edition-v010-reproduction/reproduce_verify.json
rtk proxy python3 -B -m pipeline.contact_sheet --reference references/packaging/06_private_edition.png --hero outputs/packaging/private-edition-v010-reproduction/hero.png --output outputs/packaging/private-edition-v010-reproduction/hero_comparison.png
```

The stages respectively: load v009 and rebuild the two leather shaders/add cameras
plus two crops; refine isolated finishing/studio and save an intermediate plus two
crops; apply the bounded correction and save the final scene; render four PNG/EXR
pairs; reopen/validate and write reports. The comparison command is a separate host
image operation, not a Blender render or automatic scoring step.

Do not change the replay input to v010 and run all stages as a generic updater:
camera names can collide and finishing operations assume the earlier construction.
For a future extension, load the **final v010 scene** into a new version and make
only the explicitly authorized scoped changes through a suitable adapter. The
existing production runner is specialized reconstruction code, not a universal
idempotent material-update CLI.

Current `history()` checks canonical/v007/v008/v009 and references, **not v010**.
Future work must independently hash/preserve v010; reusing this helper alone does
not protect the now-selected baseline. Stage runners also write report files and
are not strictly read-only inspection tools.

## Limitations and unverified items

- Exact leather identity, measured relief/BRDF, manufacturer dimensions, lighting
  power and camera data are not supplied by the concept sheets. Current values are
  disclosed artistic/physical assumptions.
- The replacement grain is more rounded and visible, but retains elongated crease
  channels. Macro detail remains source-limited; output resolution cannot recover
  absent source information. Texture continuity at every corner is not certified.
- Provisional thin Didot lettering/deboss is less substantial than the reference.
  Availability of an approved official vector remains **Requires manual review**.
- Corner transitions remain sharper than the reference's turned leather edges.
  Canonical bevel/silhouette changes are forbidden; detailed bottom folds are absent.
- The top/side reflection distribution remains more even than the reference and
  the side reveal darker. v010 is the preferred comparison baseline, not a claim
  those differences have been solved.
- Final designer approval of all visual criteria, pixel-identical replay, non-Metal
  rendering, v010 GLB baking and React Three Fiber parity are **Unverified / pending**.
- The final scene was freshly inspected here; historical v007/v008/v009 scenes were
  located/hashed and their configs/logs reviewed, not each reopened and rerendered.
- Source URLs/license metadata are preserved locally; this audit did not download
  textures or independently establish the provider's capture technique.
- No Git repository or remote backup was established. File hashes detect changes;
  they do not provide file recovery by themselves.

## Integrity manifest

The following SHA-256 values and exact byte counts were read from disk during this
documentation task. Paths are project-relative. `S` means editable source/config or
reference; `G` generated output; `G/E` generated editable scene. Preserve all listed
files, including intermediate scenes. This table is a file record, not a visual score.

| Relative path | Role | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| `outputs/packaging/canonical-v001/canonical_box.blend` | G/E | 100,669 | `02dc34aac9e43fec4bdd2b9375c8ed73b0d04f60445a10805cb8864b0699172e` |
| `outputs/packaging/canonical-v001/effective_config.json` | G | 7,323 | `389443343a728b0a818ca46c4a2dba6a36b1fa9d6a81a1262b1e4a7af4d9c53f` |
| `outputs/packaging/canonical-v001/validation.json` | G | 2,370 | `9a1340933b8fddcd351145bbbdb48961418d4a9f75f420d419ee7895087aeb8c` |
| `outputs/packaging/private-edition-v007/private_edition.blend` | G/E | 45,908,783 | `d4b42073f648c681a58f3e6600410eaebcaf4ee46ff986d5b6ae289f7773b42c` |
| `outputs/packaging/private-edition-v008/variant-c/private_edition.blend` | G/E | 45,902,145 | `20cedf9d48e63d221e8b83289585d05d914b94fbf198530c535deaaf989cc64f` |
| `outputs/packaging/private-edition-v009/private_edition.blend` | G/E | 35,261,047 | `08c9f6265088e34b1633d807fbf57874d65add535b86a1c57ee5fd9e74fdfd5d` |
| `outputs/packaging/private-edition-v010/artifact_validation.json` | G | 1,926 | `a8240ede48b00af6715fb79528b3462d3abb9cb02a8748f6dc25081fc3e43080` |
| `outputs/packaging/private-edition-v010/branding_macro.exr` | G | 8,558,413 | `ccd8532c50a49f468f2ce4a7a4d3fbfc99b0f018259b7b1a09d65c86b8d59b6a` |
| `outputs/packaging/private-edition-v010/branding_macro.png` | G | 10,955,940 | `2f0cbf01618d1dcf35876f26a4dadd5a6b429e33db851d82973dfee5af6b4622` |
| `outputs/packaging/private-edition-v010/calibrate.log` | G | 274 | `b7a169246a152836a8cce5f9cdaeb043f1236c54589ab0c1bf7fa37bbf469fda` |
| `outputs/packaging/private-edition-v010/calibration/material.blend` | G/E | 342,809,205 | `2868b60bacf247f3f4e74299ed73a7df73cb9faf73c770a4a03a4e153656d089` |
| `outputs/packaging/private-edition-v010/calibration/material_front.png` | G | 1,326,109 | `0d4090208f82906923de326d198aa8a57f5dff0659e2232185f56135753f113b` |
| `outputs/packaging/private-edition-v010/calibration/material_macro.png` | G | 1,161,789 | `f44827f999943138f629d85b959a01e0d21f4dbad245def335ee7683393af0bb` |
| `outputs/packaging/private-edition-v010/calibration/studio_branding.png` | G | 2,849,170 | `cd25f4a13f9fe59c5cc3810697461daa943870129ee9eb521d8cbeb4168de460` |
| `outputs/packaging/private-edition-v010/calibration/studio_edge.png` | G | 949,720 | `5e49ce6353cb06798ac000c4aac147df75ced277ab2fb90c60c82d8ed5675227` |
| `outputs/packaging/private-edition-v010/config_calibrate.json` | G | 4,309 | `9c55b0a0261e90e0136b1d3e55faddffe50671a29694baadcaa641b82c2f2a44` |
| `outputs/packaging/private-edition-v010/config_final.json` | G | 4,309 | `9c55b0a0261e90e0136b1d3e55faddffe50671a29694baadcaa641b82c2f2a44` |
| `outputs/packaging/private-edition-v010/config_material.json` | G | 4,256 | `fb4da7aaa428aa1766cc6e59863cd7bee5a1c8d67f3da72a1e8ca399ecc1d8b8` |
| `outputs/packaging/private-edition-v010/config_studio.json` | G | 4,256 | `fb4da7aaa428aa1766cc6e59863cd7bee5a1c8d67f3da72a1e8ca399ecc1d8b8` |
| `outputs/packaging/private-edition-v010/config_verify.json` | G | 4,309 | `9c55b0a0261e90e0136b1d3e55faddffe50671a29694baadcaa641b82c2f2a44` |
| `outputs/packaging/private-edition-v010/corner_macro.exr` | G | 8,490,448 | `5c118d77b2aabed16b6a4119769c540d1bc80e81151379d391c06844049b5617` |
| `outputs/packaging/private-edition-v010/corner_macro.png` | G | 10,804,090 | `db051507d812e823a43688b593bda2061d777b8729cc9128cf4ac09a71d28179` |
| `outputs/packaging/private-edition-v010/events.jsonl` | G | 2,065 | `52d54eaf46513f9289219503c7c056150a1f88cdfe4dd43a10644c2049d31235` |
| `outputs/packaging/private-edition-v010/final.log` | G | 1,242 | `6a8b6d873d4fdd0196cdf32a30b124a1f57780fd1e2943c6726b37b8c06db4f1` |
| `outputs/packaging/private-edition-v010/finishing.json` | G | 152 | `5c450a3737d8e7149d6f43963116311e0573b60e059b1bf974475e939040fd03` |
| `outputs/packaging/private-edition-v010/geometry_lock.json` | G | 83,936 | `813502347360285f24bf524370ec0a85d2c2f8e6d1ff008dd1c106a53feea466` |
| `outputs/packaging/private-edition-v010/hero.exr` | G | 11,007,158 | `7d542b38eab0af8de2b43f1df581368b264e2a8a134d637f74e83a5011e64dad` |
| `outputs/packaging/private-edition-v010/hero.png` | G | 12,198,499 | `5ad1ca3f9891a62d4c0f282836d2f193e12ceeedc92ae73c8ddae6573df73513` |
| `outputs/packaging/private-edition-v010/hero_comparison.json` | G | 714 | `a1e0370860bb8150ca47761c37697621c9b691e791d206b2e272d48f4e1e4352` |
| `outputs/packaging/private-edition-v010/hero_comparison.png` | G | 13,000,486 | `e7a079a12caa1db3795e88fb5d7b21c22b8128c0da6e8767c68a1cef13bbcb2f` |
| `outputs/packaging/private-edition-v010/history_sha256.json` | G | 12,311 | `c8d23774924ea82fc90e3946ce2ae2e872f57b8a68aefa5ffdd57a5ff59b0575` |
| `outputs/packaging/private-edition-v010/implementation_summary.txt` | G | 5,351 | `6e5e456059709af81ae6b6e7e7e9f9ec421d0f33a5f4e990e202bbf794874bea` |
| `outputs/packaging/private-edition-v010/leather_macro.exr` | G | 8,413,066 | `2d43bf381a6a014bb640630c0160ff9f44aff5913611d93c07ca08b5219f6916` |
| `outputs/packaging/private-edition-v010/leather_macro.png` | G | 10,841,380 | `8a4b308024f2892ddb37e9b0fe05b6add685e85e1deb23a2b6b5441e907eab5f` |
| `outputs/packaging/private-edition-v010/manual_review.json` | G | 329 | `eccc7601d629ede607327e09db7becb7fbddea7fbc30c551d0665daa9da4aa8d` |
| `outputs/packaging/private-edition-v010/material.log` | G | 1,048 | `7282ef6cb657f779e669cf3ba328856e1a811b5ed21543d308f2f747393b2c47` |
| `outputs/packaging/private-edition-v010/material_config.json` | G | 993 | `0b8a6e8907fa8325fc58f2c30137c133dcbe7492935eb1f7ecefd8cb23feb980` |
| `outputs/packaging/private-edition-v010/private_edition.blend` | G/E | 342,809,381 | `906f2dac4dbc0c7ac2265d003feee689993de510ca18ae82d808cf5ec835ea3f` |
| `outputs/packaging/private-edition-v010/private_edition_calibrated.blend` | G/E | 342,809,381 | `a663d9b19126608299d72da494df3635e52d505fd9b7f3a83206a08ffaa56f98` |
| `outputs/packaging/private-edition-v010/production_script_snapshot.py` | G | 19,530 | `8c2e9d6be249fcd290003f505c06d4fb3677fc314c02233917afc83cb17f07fa` |
| `outputs/packaging/private-edition-v010/qualification/source_selection.json` | G | 1,001 | `81b71e62e20ca2e521a35d0d13a5325d84fddc1c63931e9d00f8ffc3118d6c48` |
| `outputs/packaging/private-edition-v010/source_manifest.json` | G | 2,030 | `c910661c843c9a0a61e39a0873878572cfc10f903a1b4796f451cced12348d19` |
| `outputs/packaging/private-edition-v010/status_calibrate.json` | G | 40 | `a159d0ba99a3c5d18a08bf721eefb726d0739b7f0b3e23a86b525376dd94181e` |
| `outputs/packaging/private-edition-v010/status_final.json` | G | 40 | `a159d0ba99a3c5d18a08bf721eefb726d0739b7f0b3e23a86b525376dd94181e` |
| `outputs/packaging/private-edition-v010/status_material.json` | G | 40 | `a159d0ba99a3c5d18a08bf721eefb726d0739b7f0b3e23a86b525376dd94181e` |
| `outputs/packaging/private-edition-v010/status_studio.json` | G | 40 | `a159d0ba99a3c5d18a08bf721eefb726d0739b7f0b3e23a86b525376dd94181e` |
| `outputs/packaging/private-edition-v010/status_verify.json` | G | 40 | `a159d0ba99a3c5d18a08bf721eefb726d0739b7f0b3e23a86b525376dd94181e` |
| `outputs/packaging/private-edition-v010/studio.log` | G | 831 | `16d61eec0a977def325d21677c18b482189a2935a6fb14ac7dd7d552eaccdb96` |
| `outputs/packaging/private-edition-v010/studio_config.json` | G | 1,834 | `3bc810a22c1a89c93db04d480ed509f7c3cd149fc2dc98cbb7e25770f942821f` |
| `outputs/packaging/private-edition-v010/uv_validation.json` | G | 1,417 | `50fe260215b10dda5d638cdc7df7f0e0bf5be01016c651dc3c4ad36ffbc30c6d` |
| `outputs/packaging/private-edition-v010/validation.json` | G | 426 | `56c3532d10b9e10e1967c8168b2c263d0b4c30169ecbba3243201939618f4682` |
| `outputs/packaging/private-edition-v010/verify.log` | G | 381 | `9a2afbae45125bbfaca21efe8023ac8b7b21f3de4e52a05e41c32b59325a43b8` |
| `config/packaging.json` | S | 2,807 | `6d088e30cdf3643c721f5ad363737ab73e58bdd64abf680868e0d926671ef613` |
| `config/materials.json` | S | 2,167 | `06ba60979444a93541241abed2505e80032d30a889f16ec1903e684c919f651f` |
| `config/private_edition_production.json` | S | 2,845 | `0889ba92d343d1c6e03ec26de5998d738f14bbdef65532bf08322891acfd87fd` |
| `config/studio_private_reference.json` | S | 1,215 | `b3315dfbb26666ce93b1e079e63f8c97ccd4896192fb7d375f21015669acf9cc` |
| `pipeline/production.py` | S | 19,530 | `8c2e9d6be249fcd290003f505c06d4fb3677fc314c02233917afc83cb17f07fa` |
| `pipeline/cli.py` | S | 5,215 | `d444d15d9ae2af0fc4e699c425feceeb529f1518c367b8718ff73558abacee0a` |
| `pipeline/config.py` | S | 3,162 | `7da679fa8efcfb3d4ed5f87348d2448703cd4e5f06a8201a2f2de3b814b7090c` |
| `pipeline/entry.py` | S | 2,836 | `86e918c5e7d876a7d0479521806b3d230c293bd4b4e02a02a5b591178cf2cf62` |
| `pipeline/geometry/box.py` | S | 6,266 | `11f48530da0775d32e2f6fd88a2ec963c4e28a40d24f588d3d5069db220515dc` |
| `pipeline/locked.py` | S | 1,950 | `b443a6dbc0d63bbfa22dbd7484f8b2bd062fb32a62553669f88488f3dee0bf2c` |
| `pipeline/rendering.py` | S | 2,696 | `567c2988de6cc6f6bf42b65c75ada3acf3c13a076c4fb54d5207e5fea9301c46` |
| `pipeline/reference_finish.py` | S | 7,725 | `4cca1022668878658416e66f15684899df14513bbb28adb1a66f3ca3bf2e2c78` |
| `pipeline/reference_studio.py` | S | 6,016 | `58577a5e7baf1d3079d97418edcda475cc8ce6e8e5ac696aff983f9d2918019e` |
| `pipeline/exporting.py` | S | 566 | `7a27951edf0d9978c4eeaed4cd3cb73bfa7a58b06d1d8ad2b5022085665e1b6e` |
| `pipeline/contact_sheet.py` | S | 6,049 | `8ee1e2a35caea3f26c561862819a9ac8207794fcb9e4794752489addd444919b` |
| `references/packaging/01_essential.png` | S | 2,599,933 | `511db7a7c5758a7d259563cc79ba9e0a4315d1c0066816c736de96c0097839ac` |
| `references/packaging/02_signature.png` | S | 2,433,682 | `3814b0a3746a22095806e170b6a454f41f547efae0a7bece5e924a21faa24928` |
| `references/packaging/03_select_primary.png` | S | 2,732,425 | `8f31370b837698c15a98da4ec00d4e213cb22d64a023f26e9ad06b4cea23b122` |
| `references/packaging/04_select_secondary.png` | S | 2,714,306 | `aa5dd0cf85cf44e2e164129eb873aa5f6cb054697c899003bd99aeab8517e14b` |
| `references/packaging/05_reserve.png` | S | 2,561,802 | `817c352c5157be892a498302269074dc77b949537983be199b291a335d7963b4` |
| `references/packaging/06_private_edition.png` | S | 2,628,215 | `6d4ade8fbefa13eddc27cf87a494f24879a21177ae26eaede47124bf0365f5cd` |
| `references/packaging/manifest.json` | S | 2,810 | `d1b819938fd89ce8535c639a61f405d5cab1ee22e6ace1969e85a70fd3c0bbdc` |
| `textures/sources/polyhaven_leather_red_02_8k/leather_red_02_coll1_8k.png` | S | 108,818,342 | `59333325f3320b54716d8690029648a9a82a3c64e3b109f897b79dfe0c31434d` |
| `textures/sources/polyhaven_leather_red_02_8k/leather_red_02_disp_8k.png` | S | 106,828,104 | `169536bb813e09230d70a3a742825ba1104f914c88ade995f6a88be1d143f82d` |
| `textures/sources/polyhaven_leather_red_02_8k/leather_red_02_nor_gl_8k.png` | S | 86,788,036 | `87d6fb5e49c77f275a5a4b8b2c00edf3e8482f46773f2a1e2dcf0f38ab57866f` |
| `textures/sources/polyhaven_leather_red_02_8k/leather_red_02_rough_8k.png` | S | 36,699,594 | `9697a2d3c20752abce556bbc8a0b5b82d1ebe71b8c5988249a38db81bb86f518` |
| `textures/sources/polyhaven_leather_red_02_8k/source.json` | S | 2,030 | `c910661c843c9a0a61e39a0873878572cfc10f903a1b4796f451cced12348d19` |

Manifest scope: 79 important baseline files. A broader before/after audit also
hashed 207 existing production, packaging-history, reference and texture files
(2,116,215,174 bytes), excluding watch history, caches and Finder metadata.
No production stage was executed during this documentation audit.


## Documentation audit result

All 207 protected production/reference/source files retained identical bytes and
SHA-256 values after this documentation task. Finder .DS_Store metadata is excluded
from production integrity checks; two such OS metadata records changed during the
audit. No scene, map, config, Python implementation, historical render or camera/
geometry source file changed, and no production artifact was added.

The documentation adds the five files in this directory and the three root agent
entry points; only a pointer/status notice was inserted into the existing root
README. No Git repository was initialized. Local Markdown targets and anchors were
checked, and the reproduction helper was parsed without execution. The environment
check succeeded without rendering. The saved final scene was inspected without saving.
