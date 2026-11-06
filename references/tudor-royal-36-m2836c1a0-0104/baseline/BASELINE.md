# Baseline: TUDOR Royal 36 M2836C1A0-0104 (saved 2026-11-07, awaiting designer approval)

Front-relief build made with the -0101/-0103 recipe, compared with the reference photo and tuned over four correction passes. Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/tudor-m2836c1a0-0104.glb`, 1,475,784 bytes, sha256 `6b48a42ecb5840f0dabde48b2fcb32afa1aa0ddba293c224e45a08ccdd921e53` (GLB 2.0, two embedded JPEG image bufferViews, no external URIs) |
| Comparison render | `baseline_cmp-front_1800.png` (1800 px, white kit, same frame as the 2x reference), sha256 `0cf5033a3cdda3094d390435d522c1991e28dac687e343bd00c71e35c5d40c7e` |
| Side by side | `baseline_vs_reference.png` (left: reference 2x crop, right: render) |
| Reference | `../tudor-m2836c1a0-0104_900x1200.png` (original), `../tudor-m2836c1a0-0104_1800x2400.png` (2x working copy) |
| Job / step / spec | `jobs/tudor-royal36-m2836c1a0-0104.json`, shared `pipeline/steps/watch_tudor_royal36_0103.py` (read-only reuse), `baseline_spec.json`, `baseline_job.json` |
| Inputs rebuilt by | `python3 -B -m pipeline.tudor_royal36_prep 0104` (trace, dial map, steel map in `outputs/watches/tudor-royal36-m2836c1a0-0104/`) |

Rebuild: `python3 -B -m pipeline.tudor_royal36_prep 0104 && python3 -B -m pipeline.jobs run jobs/tudor-royal36-m2836c1a0-0104.json --force`

State: steel parts, hands, hub and lume strips carry the reference photo projected from the front (the hands show the photographed gold); bracelet is flat with rows and polished pieces at the template positions (joint gap 0.12 mm); dial is the 2x photo map; steel emission 0.33, dial emission 0.55 (silver dial needs more than -0103's 0.4), dial specular 0.

Differences from the earlier variants: hand half widths are under the photographed ones (no +0.1 mm cover, which left a grey rim on the silver dial), seconds tail (479, 640) and hour tail (483, 686) shortened, hub_r 16 px; everything else is the shared template (alpha silhouette differs from -0101 by at most 58/255).

Region mean luminance, render : photo: dial 0.998, dial outer ring 0.993, bezel 1.011, bracelet top 1.014, bracelet bottom 0.998, case top 1.027.

Known differences: drop shadow and background are not part of the asset; case top reads about 3% brighter; a faint grey sliver remains beside the seconds tail and the hour-hand tail corner at the hub; the dial render looks slightly softer than the photo (2x upscale); gold numerals read about 3% less saturated; heights are estimated (no side view).
