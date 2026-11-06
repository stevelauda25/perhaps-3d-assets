# Baseline: TUDOR Royal 36 M2836C1A0-0103 (saved 2026-11-07, awaiting designer approval)

Front-relief build made with the -0101 recipe, compared with the reference photo and tuned over four correction passes. Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/tudor-m2836c1a0-0103.glb`, 1,438,284 bytes, sha256 `be036b2c60136b9b7b48e7d56609e16479ba18cfea736333fe233c1e03864a24` (GLB 2.0, two embedded JPEG image bufferViews, no external URIs) |
| Comparison render | `baseline_cmp-front_1800.png` (1800 px, white kit, same frame as the 2x reference), sha256 `587a849e9f3f885d40b9c0f98af3bc55532714ff2a928c212c0e14d2066be2f9` |
| Side by side | `baseline_vs_reference.png` (left: reference 2x crop, right: render) |
| Reference | `../tudor-m2836c1a0-0103_900x1200.png` (original), `../tudor-m2836c1a0-0103_1800x2400.png` (2x working copy) |
| Job / step / spec | `jobs/tudor-royal36-m2836c1a0-0103.json`, `pipeline/steps/watch_tudor_royal36_0103.py` (copy of the shared step plus `hands.lume_material`), `baseline_spec.json`, `baseline_job.json` |
| Inputs rebuilt by | `python3 -B -m pipeline.tudor_royal36_prep 0103` (trace, dial map, steel map in `outputs/watches/tudor-royal36-m2836c1a0-0103/`) |

Rebuild: `python3 -B -m pipeline.tudor_royal36_prep 0103 && python3 -B -m pipeline.jobs run jobs/tudor-royal36-m2836c1a0-0103.json --force`

State: steel parts, hands, hub and lume strips carry the reference photo projected from the front; bracelet is flat with rows and polished pieces at the photo's positions (joint gap 0.12 mm); dial is the 2x photo map; steel emission 0.33, dial emission 0.4, dial specular 0.

Region mean luminance, render : photo: dial 0.996, dial outer ring 0.987, bezel 1.016, bracelet top 1.019, bracelet bottom 1.005, case top 1.042.

Known differences: drop shadow and background are not part of the asset; case top reads about 4% brighter; bracelet row ends show a thin dark backing line the photo does not have; heights are estimated (no side view); the hands' 3D edge bevels add a faint outline around the photographed hands.
