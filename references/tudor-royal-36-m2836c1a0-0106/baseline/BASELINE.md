# Baseline: TUDOR Royal 36 M2836C1A0-0106 (saved 2026-11-07, awaiting designer approval)

Front-relief build made with the -0101 recipe and the -0103/-0104 tuning; compared with the reference photo, no correction pass needed after the first build. Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/tudor-m2836c1a0-0106.glb`, 1,435,768 bytes, sha256 `ea744ada9f3f1e91c2e91c344a9e6b3d66832b4c2c7fd97a04688a053888cc30` (GLB 2.0, two embedded JPEG image bufferViews, no external URIs) |
| Comparison render | `baseline_cmp-front_1800.png` (1800 px, white kit, same frame as the 2x reference), sha256 `fd91fda831d76b435d37489d11796b9e3deebd25b5b6df7ab8768ed5196a598a` |
| Side by side | `baseline_vs_reference.png` (left: reference 2x crop, right: render) |
| Reference | `../tudor-m2836c1a0-0106_900x1200.png` (original), `../tudor-m2836c1a0-0106_1800x2400.png` (2x working copy) |
| Job / step / spec | `jobs/tudor-royal36-m2836c1a0-0106.json`, shared `pipeline/steps/watch_tudor_royal36_0103.py` (read-only reuse), `baseline_spec.json`, `baseline_job.json` |
| Inputs rebuilt by | `python3 -B -m pipeline.tudor_royal36_prep 0106` (trace, dial map, steel map in `outputs/watches/tudor-royal36-m2836c1a0-0106/`) |

Rebuild: `python3 -B -m pipeline.tudor_royal36_prep 0106 && python3 -B -m pipeline.jobs run jobs/tudor-royal36-m2836c1a0-0106.json --force`

State: steel parts, hands, hub and lume strips carry the reference photo projected from the front (the hands show the photographed blue and white lume); bracelet flat with rows and polished pieces at the template positions (joint gap 0.12 mm); dial is the 2x photo map; steel emission 0.33, dial emission 0.55 (as -0104; light dial), dial specular 0.

Differences from the earlier variants: spec and tails follow -0104 (hand half widths under the photographed ones, hour tail (483, 686), seconds tail (479, 640), hub_r 16); baton indices, blue hands; template otherwise shared (alpha silhouette vs -0103 max diff 48/255).

Region mean luminance, render : photo: dial 1.001, dial outer ring 1.002, bezel 1.015, bracelet top 1.018, bracelet bottom 1.006, case top 1.042.

Known differences: drop shadow and background are not part of the asset; case top reads about 4% brighter; a faint grey sliver beside the seconds tail and a grey halo at the top of the hub; hand edges a touch brighter than the photographed blue; dial slightly softer than the photo (2x upscale); heights are estimated (no side view).
