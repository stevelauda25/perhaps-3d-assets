# Baseline: TUDOR Royal 36 M2836C1A0-0101 (saved 2026-11-07, designer: "perfect")

Designer-accepted front-relief build, kept to compare later changes against the reference photo. Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/tudor-m2836c1a0-0101.glb`, 1,484,268 bytes, sha256 `55e01631312661757225f26eef27b4762fa91a288b90355ca40c81eec279729b` |
| Comparison render | `baseline_cmp-front_1800.png` (1800 px, white kit, same frame as the 2x reference), sha256 `c6040fc0921be7fad9718bf25b31d2371eeda18b8b035d9292ec7e11e0eb2ae6` |
| Side by side | `baseline_vs_reference.png` (left: reference 2x crop, right: render) |
| Reference | `../tudor-m2836c1a0-0101_900x1200.png` (original), `../tudor-m2836c1a0-0101_1800x2400.png` (2x working copy) |
| Job / step / spec | `jobs/tudor-royal36-m2836c1a0-0101.json`, `pipeline/steps/watch_tudor_royal36.py`, `baseline_spec.json` (copy of the spec at this state) |
| Inputs rebuilt by | `python3 -B -m pipeline.tudor_royal36_prep` (trace, dial map, steel map in `outputs/watches/tudor-royal36-m2836c1a0-0101/`) |

Rebuild: `python3 -B -m pipeline.tudor_royal36_prep && python3 -B -m pipeline.jobs run jobs/tudor-royal36-m2836c1a0-0101.json --force`

State: steel parts carry the reference photo projected from the front; bracelet is flat with rows and polished pieces at the photo's measured positions; dial is the 2x photo map with 3D gold hands over it; steel emission 0.4, dial emission 0.45. Known differences: drop shadow and background are not part of the asset; dial reads about 17% brighter than the photo; heights are estimated.
