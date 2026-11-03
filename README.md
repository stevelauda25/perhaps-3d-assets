# Perhaps 3D production

**Start here: [3D workflow documentation](docs/3d/README.md).** Private Edition
**v010 is the designer-selected best baseline**. The canonical procedure is in
[PRODUCTION_WORKFLOW.md](docs/3d/PRODUCTION_WORKFLOW.md), with exact scene/config
paths, verified settings and recovery instructions in
[BASELINE_V010.md](docs/3d/BASELINE_V010.md).

The existing content below is preserved implementation history. Its earlier
"current" v007/v008/v009 descriptions and commands do not supersede the v010
snapshot or the shared workflow documentation.

The approved Private Edition primary leather grain is **v008 Variant C**:
3.0x physical grain size, a 96 mm texture repeat. **v009** adds secondary surface
detail and restrained studio adjustments for manual review. The approved
canonical master, previous benchmarks and separate Casio workspace are preserved.

## Current files

- `outputs/packaging/private-edition-v009/`: refined editable scene, four actual
  Cycles renders, four-panel historical/reference comparison, exact material and
  studio snapshots, preservation checks and execution logs.
- `outputs/packaging/private-edition-v008/variant-c/`: approved grain-scale base.
- `outputs/packaging/private-edition-v007/private_edition.blend`: editable scene,
  packed PBR maps and font, approved controls, original cameras and reference cameras.
- `outputs/packaging/private-edition-v007-benchmarks/`: four 16-bit renders,
  comparison sheet, exact configuration snapshots and execution logs.
- `outputs/packaging/private-edition-v007-verification/`: reopened geometry and
  camera checks.
- `outputs/packaging/canonical-v001/`: approved geometry source, configuration and
  validation. It is a required foundation, not an obsolete material iteration.
- `references/packaging/`: all six original tier sheets and manifest, unchanged.
- `textures/sources/ambientcg_leather037_2k/`: the four retained PBR source maps
  and their license/download/checksum record.
- `assets/casio-f91w/` and `references/casio-f91w/`: preserved separate watch work.

The benchmark images are `reference_hero.png`, `reference_leather_macro.png`,
`reference_branding_macro.png`, `reference_corner_macro.png` and
`hero_comparison.png`. The comparison retains native 16-bit Blender pixels;
its original-reference crop uses nearest-neighbor enlargement only.

## Commands

Run from `/Users/admin/Documents/perhaps-3d-assets`:

```sh
rtk proxy python3 -B -m pipeline check
rtk proxy python3 -B -m pipeline.lookdev final --input outputs/packaging/private-edition-v007/private_edition.blend --output outputs/packaging/private-new-renders
rtk proxy python3 -B -m pipeline.lookdev preview --input outputs/packaging/private-edition-v007/private_edition.blend --views reference_hero --output outputs/packaging/private-new-preview
rtk proxy python3 -B -m pipeline.lookdev validate --input outputs/packaging/private-edition-v007/private_edition.blend --output outputs/packaging/private-new-validation
rtk proxy python3 -B -m unittest discover -s tests -v
```

To prepare a future material version, load the approved master without rebuilding
its geometry. This also keeps the selected v007 scene untouched:

```sh
rtk proxy python3 -B -m pipeline.lookdev prepare --input outputs/packaging/canonical-v001/canonical_box.blend --config config/private_edition_reference.json --output outputs/packaging/private-next-version
```

Output directories must be new and below `outputs/`. Rendering reads the exact
configuration snapshots beside the input scene and does not recreate materials.
All older-version defaults have been replaced with the retained configuration.
Blender CLI is primary; Blender MCP is optional. No dependencies are installed by
these commands. `BLENDER_BIN` overrides the configured Blender executable.

## Configuration and construction

- `config/private_edition_reference.json`: current scanned leather, graphite
  metal, lining, deboss, stitching, reference camera and render profiles.
- `config/studio_private_reference.json`: fixed silk-diffuser emission sources,
  matte black floor, pure black world and Standard/None color management.
- `config/packaging.json`, `config/materials.json`: canonical dimensions and
  foundational material-slot catalogue for later tiers.
- `pipeline/reference_material.py`, `reference_finish.py`, `reference_studio.py`:
  current appearance workflow. Shared CLI, geometry, lighting, rendering,
  validation and future export utilities remain reusable.

Canonical meshes, topology, bevels, transforms, origins and opening controls are
locked. Removable render wraps are exact copies of the approved evaluated
surfaces; only the wraps receive metric UVs, improved shading normals and the
physical deboss. The canonical lid/base remain in the scene, hidden beneath the
wraps for rendering. Protected-data checks verify their preservation.

Leather uses [ambientCG Leather037](https://ambientcg.com/view?id=Leather037), a
photometric-stereo set under [CC0](https://docs.ambientcg.com/license/). Color,
roughness, OpenGL normal and height maps are retained and packed. The inferred
32 mm tile, restrained normal response, obsidian pigmentation and slight warm
undertone remain configurable. Pigmentation uses scanned luminance, not its brown
hue. The original reference images and all selected render files are unchanged.

The canonical box is 140 mm cubed with 2.5 mm walls, 0.6 mm outer bevels, a
5 mm reveal, and the approved low-front/high-rear diagonal separation. Reference
inter-view inconsistencies and the approved structural silhouette are preserved.
Didot remains provisional because no official wordmark vector was supplied.

Current benchmark: hero 2048 px / 512 samples, three macros 1536 px / 512 samples,
Metal, 16-bit PNG. The retained batch took 421.835 seconds total and approximately
4.4 GB peak reported process resident memory. Technical checks do not establish
an exact visual match; v007 is the selected baseline for future user-directed work.
Other tiers and GLB optimization have not been produced.

## v008 controlled grain-scale comparison

Run the fixed six-preview experiment from the unscaled v007 scene:

```sh
rtk proxy /usr/bin/python3 -B -m pipeline.lookdev grain-compare --input outputs/packaging/private-edition-v007/private_edition.blend --output outputs/packaging/private-edition-v008 --device metal
```

The output directory must not already exist. Each candidate loads v007 afresh;
this command never rebuilds geometry, finishing details, lights or cameras.
Scenes and config snapshots are in `variant-a/`, `variant-b/`, and `variant-c/`.
Each contains `private_edition.blend`, `reference_hero.png` and
`reference_leather_macro.png`. The root contains `grain_comparison.png`, its
pixel-preservation/provenance manifest, validation, execution logs and
`technical_summary.txt`. Open the comparison for manual scale selection.

`leather.leather_grain_scale_multiplier` controls physical size, with default
`1.0`. The material samples all four PBR maps at `existing_uv / multiplier`;
it never scales bump strength or edits mesh UVs. The same coordinate operation
is applied to exterior and pressed leather on every wrapped face.

| Candidate | Multiplier | Effective repeat | Repeats across 140 mm |
| --- | ---: | ---: | ---: |
| v007 baseline | 1.0 | 32 mm | 4.375 |
| A | 1.5 | 48 mm | 2.917 |
| B | 2.25 | 72 mm | 1.944 |
| C | 3.0 | 96 mm | 1.458 |

The scan contains many small grain cells per tile. At the baseline's 4.375
repeats per face, these structures become difficult to resolve in a hero view.
Larger repeats reduce spatial frequency; they retain the same 2K maps, linear
filtering, normal strength and 4-micron height distance. Source texel density
decreases as the physical repeat grows. Scanned pores enlarge with the primary
grain; a separate microdetail layer is deferred until manual grain selection.

All six previews use 1024 px, 128 samples, adaptive threshold 0.01, denoising,
seed 42, Cycles Metal and 16-bit PNG. The saved v007 Standard/None transform,
exposure -0.25, Blackman-Harris pixel filter, materials and studio stay fixed.
The comparison uses native historical v007 pixels and integer nearest-neighbor
enlargement for the smaller previews and original reference crop. Labels identify
v007's historical 2048 px / 512 sample settings. Enlargement adds no detail;
the reference pixel grid is not a physical grain measurement.

Validation checks original source hashes, all object/mesh/UV/curve data, existing
cameras and controls, non-coordinate shader settings, studio lights and color
management. Each new scene is reopened for validation after its two renders.
Only the coordinate node and documented preview-output settings may differ.
Blender omits three unused historical material datablocks when saving; these
zero-user datablocks are excluded from scene-material checks. Original v007
bytes remain unchanged. A technical check recovery reused A's completed images;
the batch produced exactly six previews, without repeating renders. Combined
render time was 70.404 seconds; peak reported process resident memory was 3114 MB.

This experiment does not change Leather037's angular crease morphology or isolate
the contributions of broad reflection sources, filtering and denoising to a flat
hero appearance. If scale alone remains insufficient, those are separate follow-up
questions. No candidate is automatically selected, no independent pore shader is
added, and no high-resolution final render is produced.

## v009 secondary realism refinement

The v009 operation edits the existing Variant C material and reflection sources
in place in a new scene. It never calls the geometry, finishing or camera builders:

```sh
rtk proxy /usr/bin/python3 -B -m pipeline.lookdev surface-refine --input outputs/packaging/private-edition-v008/variant-c/private_edition.blend --config config/private_edition_v009.json --output outputs/packaging/private-edition-v009 --device metal
```

That delivery folder now exists; use a new output path to run the command again.
Material parameters are in `config/private_edition_v009.json`; lighting is in
`config/studio_private_v009.json`. The output also retains both effective snapshots.
The scale contract rejects any primary repeat other than 3.0x / 96 mm.

The existing scanned normal, 4-micron scan bump, dye and primary UV mapping are
unchanged. A second Bump node perturbs the scanned normal with sparse, shallow
follicle-like pits: 0.14 mm spacing, 0.8-micron distance and 0.35 strength. These
are approximate procedural pores, not a new scan or a second leather grain.
They use unscaled metric wrap coordinates, independently of the approved primary
repeat. Pressed lettering receives only 45% of the secondary pore/finish strength.

Scanned roughness changes from `0.4 * scan + 0.28` to
`0.6 * scan + 0.205`, retaining approximately the same median while widening
variation. Layered summit polish (+/-0.012), subtle 1.2 mm finish variation
(+/-0.012), and pore cavity roughness (up to +0.018) are bounded to 0.30-0.60.
Low-amplitude Noise affects roughness only; the scanned leather remains the
primary visible pattern. Coat weight falls from 0.025 to 0.01 and sheen from
0.025 to 0.012. Pigment, IOR, original grain normal strength and exposure stay fixed.

The same five silk-diffuser sources remain. Front/left cards are slightly narrower
with lower energy, the top card moves slightly, camera-fill energy falls from
0.12 to 0.045, and the small band source increases from 0.003 to 0.004. Black world
and floor response are unchanged. No metal shader, wordmark, stitching or camera
changes are made.

One four-view benchmark uses Cycles Metal, 256 samples, adaptive threshold 0.005,
denoising and 16-bit PNG: hero 2048 px; leather, branding/inlay and corner macros
1536 px. Comparison panels retain native pixels or labeled integer enlargement.
Original v007/v008 files, references and source textures are hash-checked;
product meshes, UVs, finishing curves, all cameras and controls are checked before
and after rendering and after reopening the saved scene. Only the two leather
shaders and specified photographic reflection sources are excluded from the
unchanged-scene fingerprint; their grain contract is checked separately.

Limits remain: Leather037 has an angular crease morphology; the added follicles
are an approximation. Approved bevel/corner construction and provisional Didot
typography cannot exactly match the supplied sheet. Lighting and microscopic
dimensions remain calibrated artistic assumptions. Render completion is not
evidence of near 1:1 visual fidelity; v009 awaits manual approval.

The delivered v009 hero has clearer primary grain and reduced broad sheen, but
the macros remain soft and angular relative to the reference; the wordmark is
still very faint. At a 96 mm repeat the 2K scan provides about 46.9 microns per
texel, limiting detail in the 18 mm corner macro. Added shallow pores remain
subtle under these lights and denoising. This is a review benchmark, not an
approved near 1:1 result. The four renders took 201.627 seconds combined.
Reopen verification excluded two unused historical packed red-leather maps that
Blender omitted on saving; all four active Leather037 maps and all original
v007/v008 source files remain unchanged. No renders were repeated.

## v010 reference reconstruction

The bounded production pass is implemented in `pipeline/production.py`, with
parameters in `config/private_edition_production.json`. It loads v009 and preserves
the canonical meshes, controls, product transforms and all existing cameras.
Separate production cameras and nonstructural finishing changes live in v010.

```sh
rtk proxy /usr/bin/python3 -B -m pipeline.production material
rtk proxy /usr/bin/python3 -B -m pipeline.production studio
rtk proxy /usr/bin/python3 -B -m pipeline.production calibrate
rtk proxy /usr/bin/python3 -B -m pipeline.production final
rtk proxy /usr/bin/python3 -B -m pipeline.production verify
```

These stages refuse existing stage logs and outputs. For another production run,
copy the config, change `output` to a fresh version, and pass `--config PATH` to
each command. The shipped config contains the final calibrated values; the v010
`config_material.json` and `config_studio.json` preserve the initial crop settings.
`calibrate` applies the two evidence-driven corrections without rebuilding assets.

The deliverable scene is `private_edition_calibrated.blend`; `private_edition.blend`
and `calibration/material.blend` preserve the earlier diagnostic stages. Four
full-frame PNG/EXR pairs are generated exactly once. The hero uses 2048 pixels,
macros 1536 pixels, 512 samples, adaptive threshold 0.003, Metal and denoising.
Standard/None, exposure -0.25 and a 1px pixel filter are explicit. EXRs retain
scene-linear half-float pixels; PNGs contain the display transform.

Original Poly Haven Leather Red 02 8K maps replace Leather037. Source URLs,
CC0 license, checksums and provider provenance are retained in
`textures/sources/polyhaven_leather_red_02_8k/source.json`. All four original maps
are packed into the editable scene. The source's detailed normal supplies both
rounded grain and smaller pores. Its smoother height map is retained but does
not drive displacement or add a second copy of grain bump. There is no new
procedural pore layer or invented measured height field.

One shared mapping operation applies `32 / 400 = 0.08` to the unchanged metric
wrap UVs. The 400mm repeat is an artistic physical calibration for this different
source, not a change to v008/v009's retained 96mm maps. At 8K this is approximately
48.8 microns per source texel. Fine macro detail remains limited by actual source
information; more output pixels cannot recover missing detail.

The source pigmentation is remapped into obsidian dye while retaining local
variation. Roughness spans 0.32–0.52; the supplied tangent normal uses strength
0.6 outside and 0.35 in pressed lettering. The finishing wrap's deboss floor is
0.20mm deep with a 0.035mm lip; existing stitch centers remain fixed, with 1mm
stitches and a 0.045mm radius. These are documented manufacturing assumptions.
The canonical geometry is untouched. Didot remains provisional branding.

The comparison sheet retains unretouched native 16-bit hero pixels and a labeled
nearest-neighbor reference crop. No automatic visual score is computed. See the
output's `implementation_summary.txt` and `manual_review.json` for limitations
and the designer-review rubric; successful renders do not certify 90–95% fidelity.
