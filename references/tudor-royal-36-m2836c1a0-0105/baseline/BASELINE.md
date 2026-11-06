# Baseline: TUDOR Royal 36 M2836C1A0-0105 (saved 2026-11-07, awaiting designer approval)

Front-relief build made with the -0101 recipe and the -0103 tuning, compared with the reference photo; one correction pass (dial emission). Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/tudor-m2836c1a0-0105.glb`, 1,479,260 bytes, sha256 `76a4d02865b2f2958d3c886d31b68c1747b8bebbe77d945473f83e498e18df92` (GLB 2.0, two embedded JPEG image bufferViews, no external URIs) |
| Comparison render | `baseline_cmp-front_1800.png` (1800 px, white kit, same frame as the 2x reference), sha256 `5297faeb16ea531e919c24652c9383ba66e5b8bb21c5dbd58e89bd2803d4d6c0` |
| Side by side | `baseline_vs_reference.png` (left: reference 2x crop, right: render) |
| Reference | `../tudor-m2836c1a0-0105_900x1200.png` (original), `../tudor-m2836c1a0-0105_1800x2400.png` (2x working copy) |
| Job / step / spec | `jobs/tudor-royal36-m2836c1a0-0105.json`, `pipeline/steps/watch_tudor_royal36_0103.py` (shared with -0103, read-only), `baseline_spec.json`, `baseline_job.json` |
| Inputs rebuilt by | `python3 -B -m pipeline.tudor_royal36_prep 0105` (trace, dial map, steel map in `outputs/watches/tudor-royal36-m2836c1a0-0105/`) |

Rebuild: `python3 -B -m pipeline.tudor_royal36_prep 0105 && python3 -B -m pipeline.jobs run jobs/tudor-royal36-m2836c1a0-0105.json --force`

State: steel parts, hands, hub and lume strips carry the reference photo projected from the front; bracelet is flat with rows and polished pieces at the photo's positions (joint gap 0.12 mm); dial is the 2x photo map; steel emission 0.33, dial emission 0.55 (the -0103 value 0.4 rendered the salmon dial 6% dark: 0.4 gave 0.938, 0.43 gave 0.950, 0.55 gave 0.995), dial specular 0.

Region mean luminance, render : photo: dial 0.995, dial outer ring 1.000, bezel 1.011, bracelet top 1.001, bracelet bottom 0.992, case top 1.038.

Known differences: drop shadow and background are not part of the asset; case top reads about 4% brighter; heights are estimated (no side view); the hands' 3D edge bevels add a faint outline around the photographed hands.
