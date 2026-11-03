# Perhaps 3D production workflow

This is the canonical operating procedure. Use the [entry point](README.md),
[exact v010 snapshot](BASELINE_V010.md), [design contract](REFERENCE_AND_ASSET_SPECS.md)
and [debug guide](TROUBLESHOOTING.md) for supporting details. Numerical baseline
settings belong in the snapshot and actual configs, not in agent-specific copies.

## 1. Environment and execution boundary

Verified on 2026-10-29 in the standalone `perhaps-3d-assets` root:

| Item | Verified state |
| --- | --- |
| OS / architecture | macOS 26.6.2, arm64 |
| Hardware | Apple M4; Metal device reports 10 GPU cores; 16 GiB unified memory |
| Blender | 5.2.3 LTS; `/Applications/Blender.app/Contents/MacOS/Blender` |
| Blender Python | 3.13.13; `bpy` available inside Blender |
| Host Python used for audit | `/usr/bin/python3`, 3.9.6; standalone `bpy` absent |
| Renderer | Cycles; Apple Metal GPU available; CPU also enumerated |
| Host libraries | Pillow, OpenCV (`cv2`) and NumPy importable |
| GLB support | Blender's `EXPORT_SCENE_OT_gltf` operator available |
| Version control | No Git repository configured at this root or its parents |

Host CLI/config orchestration uses Python's standard library. Image comparison
sheets additionally use Pillow, OpenCV and NumPy. Blender supplies `bpy`,
`bmesh`, `mathutils`, rendering and EXR output. No standalone `bpy` package is
needed. Legacy typography reconstruction uses macOS Didot; comparison labels use
macOS Arial. Inspect those paths before attempting source reconstruction elsewhere.
The saved v010 wordmark is already geometry; reproducing v010 from its v009 input
does not recreate text from a system font.

`pipeline.cli.detect_blender` tries `BLENDER_BIN`, the packaging config's Blender
path, executable lookup on PATH, then the macOS application path. Set
`BLENDER_BIN` to the actual executable on a new machine. This overrides detection
without changing the approved configs. Non-macOS operation is **unverified**:
v010's production renderer explicitly requests Metal and offers no CPU flag.

The general CLI and legacy look-development CLI accept `--device cpu`, `metal`
or `auto`. `auto` can fall back to CPU; explicit `metal` fails if unavailable.
The v010 CLI does not expose this selection and fails rather than silently
rendering on CPU. Existing Metal timings are measurements, not a claim that GPU
will always be faster. No new CPU/GPU render comparison was run in this audit.

Use Blender CLI / Python as the production interface. Blender MCP is optional.
The preserved [Master Prompt V2](../../standards/MASTER_PROMPT_V2.md) is a legacy
MCP-first template; its mandatory MCP and iteration instructions are superseded
for this packaging workflow by the current user instructions and this SOP.

## 2. Project map and ownership

| Location | Responsibility |
| --- | --- |
| [pipeline/cli.py](../../pipeline/cli.py), [entry.py](../../pipeline/entry.py), [config.py](../../pipeline/config.py) | Foundational check/build/render/validate/export launcher and geometry config |
| [pipeline/geometry/box.py](../../pipeline/geometry/box.py) | Canonical geometry generator; preserve for provenance, do not rerun for routine look development |
| [pipeline/locked.py](../../pipeline/locked.py), [validation.py](../../pipeline/validation.py) | Protected product/camera fingerprint and construction validation |
| [pipeline/production.py](../../pipeline/production.py) | v010-specific material, studio, calibration, render and verification stages |
| [pipeline/reference_finish.py](../../pipeline/reference_finish.py) | Existing evaluated appearance wraps, metric UVs, deboss and stitching construction |
| [pipeline/reference_studio.py](../../pipeline/reference_studio.py), [studio.py](../../pipeline/studio.py) | Reflection cards, reference cameras and shared aim utility |
| [pipeline/rendering.py](../../pipeline/rendering.py) | Device selection and generic render profiles; v010 restores its own color/bounce settings after calling it |
| [pipeline/lookdev.py](../../pipeline/lookdev.py), [lookdev_entry.py](../../pipeline/lookdev_entry.py) | Earlier Private Edition schema/commands; not the v010 renderer |
| [pipeline/grain_compare.py](../../pipeline/grain_compare.py), [realism.py](../../pipeline/realism.py) | Preserved v008 comparison and v009 refinement logic |
| [pipeline/contact_sheet.py](../../pipeline/contact_sheet.py) | Unretouched reference/actual-render comparison sheet |
| [pipeline/exporting.py](../../pipeline/exporting.py) | Foundational product GLB selection/export; no v010 baking pipeline |
| [config/](../../config) | Parameters; `materials.json` contains foundational tier placeholders, not completed five-tier PBR assets |
| [references/packaging/](../../references/packaging) | Immutable original design sheets and manifest |
| [textures/sources/](../../textures/sources) | Original PBR maps, provider metadata, licenses and qualification evidence |
| [outputs/packaging/](../../outputs/packaging) | Versioned editable scenes, effective configs, renders, validation and logs |
| [assets/casio-f91w/](../../assets/casio-f91w), [references/casio-f91w/](../../references/casio-f91w) | Separate preserved watch history; not a packaging scratch directory |
| [tests/](../../tests), [standards/](../../standards) | Existing technical checks and historical standards |

There is no established v010 export-delivery directory or browser viewer to reuse.
Do not imply one exists. Do not modify the separate Perhaps application repository.

## 3. Starting a task safely

1. Confirm the project root and read this SOP plus the baseline snapshot. Read the
   user's requested scope before running a build or render command.
2. Inspect the relevant original sheets, actual config and final scene. Filenames
   alone are insufficient evidence for materials or construction.
3. Identify whether the task concerns geometry, appearance, rendering or delivery.
   Use the appropriate CLI/schema below. Never import old watch scripts to inspect
   them: some historical scripts perform operations at module scope.
4. Establish file hashes and a protected geometry/camera snapshot before authorized
   production changes. Write only to a new version; preserve v010 as the baseline.
5. Record physical assumptions, sources, intended changes and the bounded output
   set. For documentation-only work, inspect without saving or rendering.

## 4. Canonical construction and geometry lock

The approved [canonical master](../../outputs/packaging/canonical-v001/canonical_box.blend)
contains separate base, removable lid, fitted collar/reveal and tray floor. The
front and rear seams are horizontal at their respective heights; mirrored side
views show one continuous sloped separation. The base is wedge-shaped toward the
rear. Exact dimensions, origins and reference inconsistencies are recorded in the
[baseline](BASELINE_V010.md) and [design contract](REFERENCE_AND_ASSET_SPECS.md).

Do not alter canonical vertices, topology, bevels, dimensions, transforms, origins,
component names, parenting, diagonal seam, controls or opening construction. Keep
existing camera presets. A new task may add separately named cameras and isolated
finishing only within its authorized scope. Materials, roughness, texture mapping
parameters, lighting and output settings can change in a new version when requested.
Do not treat that permission as approval to rebuild structural geometry.

v010 keeps canonical lid/base shells hidden for rendering beneath removable
appearance wraps. **Do not unhide or delete them to fix appearance.** The wraps
contain the deboss and evaluated edge surfaces. They are not alternate canonical
meshes. Preserve both the canonical source and the approved finishing baseline.

`locked.snapshot()` captures the canonical product collection plus existing cameras;
`locked.verify(expected)` compares transforms, modifiers, mesh vertices/faces and
camera settings. It intentionally excludes material values and does not cover every
finishing mesh. v010 separately compares product/finishing transforms, UV hashes,
map alignment and prior file hashes. These checks are complementary; none is a
visual acceptance score or a complete universal scene lock.

Opening is a free lift-off motion, not a hinge. `set_opened()` changes control poses
in memory and may initialize `home_location`; do not call it during a strictly
read-only audit. Approved controls must not be reset or "cleaned up" casually.

## 5. Material sourcing and reconstruction

Qualify actual original maps before rendering a material. Compare grain morphology
at native resolution: rounded raised leather, angular creases, cloth weave and suede
fibers are different structures. Scaling a cracked pattern cannot create rounded
grain. Reject unsuitable sources before adding shader complexity.

Retain provider URL, author, license, original filenames, checksums, channel meaning,
resolution and any published physical size. Source references are not PBR maps.
Do not infer measured normal or height data from a photograph and call it a scan.
Document unavailable capture information as **Unverified**. Preserve original maps;
do not upscale or compress them to claim recovered detail.

Use sRGB for photographic base color and Non-Color for roughness, normal and height.
Verify the normal convention, tangent UV name, scale and handedness. Keep all channels
on a shared coordinate transform. Check object scales and metric UV density across
front, side, top and transitions. Do not hardcode a different scale per face.

For v010, [production.materials](../../pipeline/production.py) replaces only the two
existing leather node trees, retaining their material bindings. Original 8K color,
roughness, OpenGL normal and height maps share one mapping operation. Supplied
normal detail provides primary rounded grain and smaller pores. The source height
is retained and packed but unconnected; it does not add duplicate valley bump or
structural displacement. No additional procedural pore layer is used.

The photographic color becomes restrained obsidian pigment variation. Roughness is
calibrated independently; pressed lettering uses the same aligned texture with
separate normal, roughness and pigmentation response. See [exact values](BASELINE_V010.md).
These are appearance calibrations, not measured BRDF or microscopic depth data.

## 6. Studio, composition and render fidelity

Use the saved studio as a foundation. v010's active softboxes are **emissive mesh
cards**, not five `LIGHT` objects. `reference_studio.refine()` changes their size,
position, aim and emission factor in place. Each card has a fixed soft UV falloff
and is invisible to camera rays while contributing illumination and reflections.
The config's `power` is converted by the implementation; do not label it directly
as Blender area-light watts or replace cards with area lights as a neutral change.

Match source placement, softness and grazing reflection behavior before increasing
overall brightness. Preserve black pigmentation, pure black world, restrained floor,
readable metal and subtle deboss. Exact final card and camera values are in the
[baseline](BASELINE_V010.md). Additional `production_*` cameras preserve older presets.

The production render helper calls the generic renderer, then restores v010's
Standard/None transform, exposure, light tree, bounce depth and filter settings.
Using generic `pipeline render` would apply its own profiles and cameras instead.
Save both display-transformed review PNGs and scene-linear EXRs. No sharpening,
warping, artificial glow or AI-generated replacement renders belong in a benchmark.

## 7. Efficient bounded development

For future authorized appearance work:

1. Qualify a small shortlist of actual maps and their license/provenance.
2. Check coordinates, morphology, roughness and normal connections under controlled
   light before changing the full studio.
3. Render small borders at final frame pixel density using full source fidelity.
4. Make a targeted correction based on those diagnostics. Keep changes attributable.
5. Produce one bounded full-frame set, then stop for designer review.

v010 recorded four cropped diagnostics and four final views. The diagnostic stages
are explicit stages, not a general interactive crop CLI. Reuse existing geometry,
packed textures and saved scenes. Reduce unnecessary computation, not texture,
geometry or final image quality. Do not regenerate unchanged assets.

## 8. CLI selection and command status

Commands below are real repository entry points. All output examples must be unused
paths beneath `outputs/`. Commands that create files are for **future authorized
production work**; none was executed during this documentation task.

| Interface | Actual behavior / validation status |
| --- | --- |
| `python3 -B -m pipeline check` | Executed in this audit: Blender/Python, Metal/CPU discovery and glTF operator; no render or output directory |
| `python3 -B -m pipeline.production --help` | Executed in this audit; accepts stages and `--config` only |
| `python3 -B -m pipeline.production material/studio/calibrate/final/verify` | All five historical v010 statuses report exit 0; reproduction procedure below is source-confirmed but not rerun in this audit |
| `python3 -B -m pipeline build/render/validate/export` | Foundational interface exists; its canonical validation artifact survives; build/render/export were not rerun here |
| `python3 -B -m pipeline.lookdev ...` | Legacy schema and `reference_*` camera workflow; not drop-in compatible with v010 |

General foundation examples, **source-confirmed syntax; not executed in this audit**:

```sh
rtk proxy python3 -B -m pipeline build --tier technical --device metal --output outputs/packaging/foundation-example-new
rtk proxy python3 -B -m pipeline render --input outputs/packaging/canonical-v001/canonical_box.blend --views hero front --preset preview --device metal --output outputs/packaging/canonical-preview-example-new
rtk proxy python3 -B -m pipeline export --input outputs/packaging/canonical-v001/canonical_box.blend --output outputs/packaging/canonical-export-example-new
```

`build` constructs a fresh canonical scene; it is not routine material development
and must never replace the approved master. The general render/export/validate
commands require `effective_config.json` beside the input and reject `--config`.
They operate on foundational product objects and placeholder material delivery.
v010 has a different config layout; these are **not v010 render/export commands**.
The export utility selects `export_product` objects and controls, not a qualified
v010 appearance-wrap delivery set. No v010 GLB equivalence is established.

The v010 CLI has no `--input`, `--output`, `--device` or `--views` flags. Its full
JSON config supplies input, output and final scene name. Do not pass the split
`material_config.json` or `studio_config.json` directly as a full stage config.
Follow [recovery and reproduction](BASELINE_V010.md#recovery-and-reproduction).

## 9. Versioning, preservation and manual QA

Never overwrite canonical scenes, original references, texture sources or previous
benchmarks. Use a new output version and retain its effective configs, source hashes,
logs, scene and images. Stage commands guard existing logs/scenes, but are not
transactional: failed stages can leave partial outputs. Do not delete logs or
override guards to force a rerun; inspect and use a new attempt directory.

`production verify` is **not read-only**: it writes logs and validation JSON and
refuses an existing stage log. For preservation audits, inspect existing evidence
or run a custom non-saving Blender process with `--disable-autoexec` and
`open_mainfile(..., load_ui=False, use_scripts=False)`. Do not invoke stage runners
against the immutable baseline to "check" it.

There is currently no Git repository. The existing `.gitignore` excludes outputs,
large binaries and generated history; initializing Git later would not back up
Blender masters or renders. Preserve baseline directories and source maps through
an explicitly managed backup/archive. This task created an integrity record, not
an off-machine backup. Never initialize, commit or push without authorization.

The designer owns visual approval. Compare unretouched actual renders against the
original reference at comparable framing. No automated browser QA, similarity
scoring, screenshot loops or autonomous visual polish loops. Technical success
does not establish photorealism or 90–95% similarity. Use the [acceptance contract](REFERENCE_AND_ASSET_SPECS.md)
and record concrete remaining differences.

## 10. New tiers and future watch assets

For Essential, Signature, Select or Reserve, start from the same approved canonical
geometry and relevant original sheets. Define a separate material/finish preset,
source manifest and new versioned scene. Preserve dimensions, seam and controls;
only approved appearance differences vary. The foundational slot catalogue is a
starting schema, not completed PBR production. v010's stage runner is specialized
to existing Private Edition material/object names and v009 input; changing only a
tier label does not implement another tier. A future adapter must be explicit,
isolated and authorized.

For watches, reuse configuration, Blender detection, logging, studio, rendering and
validation techniques, but use watch-specific geometry, references and controls.
Keep historical Casio files intact. Review scripts as text before extracting logic;
never import historical modules that could render/save at module scope.

GLB preparation is a separate future phase: duplicate delivery data, bake supported
base-color/roughness/normal channels, decide which appearance geometry to deliver,
preserve PBR provenance and validate in the target renderer. Cycles node mixes,
coordinate math, lighting cards and displacement behavior do not transfer as an
equivalent glTF studio. A React Three Fiber project/QA workflow is outside this root.

## 11. Clay-like result decision tree

Before any rerender, inspect the actual saved scene and final config:

1. **Wrong shapes in the grain?** Inspect native source normal/color maps and the
   source manifest. Fix source qualification before UV scale or bump strength.
2. **Right shapes, wrong physical size?** Inspect metric UV density and the single
   shared mapping factor. Do not inherit another source's repeat blindly.
3. **Right size, exaggerated relief?** Check normal convention/strength, duplicated
   height bump and tangent UVs; do not globally amplify detail.
4. **Flat or plastic under light?** Check roughness remapping, pigment, IOR and coat
   against the saved v010 shader. Keep pigmentation dark.
5. **Material works in a crop but hero is flat?** Inspect reflection-card placement,
   angular response, framing, filter and denoising separately. Do not make all
   faces uniformly bright to expose texture.
6. **Only corners or branding fail?** Inspect isolated wraps, smoothing and provisional
   typography; document structural limitations rather than changing locked geometry.

Use the [troubleshooting table](TROUBLESHOOTING.md) for the corresponding safe action.
