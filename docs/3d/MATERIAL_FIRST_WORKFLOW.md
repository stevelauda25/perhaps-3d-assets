# Material-first workflow (all agents)

Do not invent a shader from text. Pick a **library material by ID**, qualify it in the lookdev scene, get it
approved, then reference the ID from a packaging job. Routine job commands: [OPTIMIZED_PRODUCTION_WORKFLOW.md](OPTIMIZED_PRODUCTION_WORKFLOW.md).

## Steps

1. **Reference analysis** – sample the reference sheet colour/relief (`references/packaging/`).
2. **Source real PBR textures** (ambientCG / Poly Haven, CC0) into `textures/sources/<provider>_<asset>_<res>/`;
   write `source.json` (url, license, per-file sha256: `python3 -B -m pipeline.material_library hash <dir>`).
   Inspect the maps (flat normal? roughness range? tileable? aspect?) before choosing; reject by data, not by name.
3. **Preset** `config/material_library/<category>.<provider>-<asset>.json` (fields: id, category, version, status,
   approved_version, source, maps, mapping.tile_width_mm, color, roughness, normal/height, micro, bsdf, measured, limitations).
   `status: candidate` until the designer approves; then set `approved_version`.
4. **Lookdev** – `jobs/material-essential-paper-v001.json` is the template: scene `assets/material-lookdev/material_lookdev_v001.blend`
   (140 mm flat slab + 70 mm block, 0.6 mm x4 bevel, neutral and grazing lights, fixed cameras), step `material_lookdev`
   (`material`, `lighting`), diagnostic renders (~30–125 s each at 1600²). `python3 -B -m pipeline.material_library sheet <job>` → `comparison.png`.
5. **Calibrate** physical scale (`mapping.tile_width_mm`), roughness `source_range → range`, bump `distance_mm`
   (rule used: pick distance so rms height slope ≈ a real normal map's, ~0.08) in the preset, not in scripts.
6. **Apply** – tier preset role `{"library": "<id>", "overrides": {...}}` (see `config/tiers/essential-library-check.json`);
   job stage `packaging_tier` as before. Fingerprints include the tier preset and the library files it names.
7. **Final render** only after the material is approved.

Library commands: `python3 -B -m pipeline.material_library list | verify [ID] | hash DIR | sheet JOB`.
Builder: `pipeline/pbr_material.py` (box or uv mapping, square texels, normal+height chain, optional `micro`).
No commercial software required; a photographed sample can be added as another `textures/sources/` folder
(any image-to-material tool that exports colour/normal/roughness/height) plus a preset.
