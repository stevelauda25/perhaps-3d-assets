# Baseline: TUDOR Royal 40 M2840D1A0-0003 (saved 2026-11-07, awaiting designer approval)

Front-relief build made with the Royal 40 template of -0001 on the green Roman-numeral dial photo, tuned over three emission passes. Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/tudor-m2840d1a0-0003.glb`, 1,597,904 bytes, sha256 `a819e6056bdaf41478842670852231d985dc9acd85d7be69e7f8e30535063d7d` (GLB 2.0, two embedded JPEG image bufferViews, no external URIs) |
| Comparison render | `baseline_cmp-front_2048.png` (2048 px, white kit, 27.8 px/mm, pivot at the frame centre; same frame as the 2x photo with its pivot (900, 1218) moved to (1024, 1024)), sha256 `25f3d8db61800065c766f7b340de62dbb6709e24b8cb9dddf57a25b931b34fb6` |
| Side by side | `baseline_vs_reference.png` (left: 2x reference padded into the 2048 frame, right: render) |
| Reference | `../tudor-m2840d1a0-0003_900x1200.png` (original), `../tudor-m2840d1a0-0003_1800x2400.png` (2x working copy) |
| Job / step / spec | `jobs/tudor-royal40-m2840d1a0-0003.json`, shared `pipeline/steps/watch_tudor_royal40.py` (read-only reuse), `baseline_spec.json`, `baseline_job.json` |
| Inputs rebuilt by | `python3 -B -m pipeline.tudor_royal40_prep m2840d1a0-0003` (trace, dial map, steel map in `outputs/watches/tudor-royal40-m2840d1a0-0003/`) |

Rebuild: `python3 -B -m pipeline.tudor_royal40_prep m2840d1a0-0003 && python3 -B -m pipeline.jobs run jobs/tudor-royal40-m2840d1a0-0003.json --force`

State: identical to the -0001 template (case, bezel, crown, bracelet rows and pieces, hands, materials; shared 2048 px kit preset reused read-only) because the photo silhouette is identical to -0001 and the hands sit at the same place. Differences: dial map (green, Roman numerals, silver steel hands), dial emission 0.32 (-0001: 0.40), steel emission 0.315 (-0001: 0.33). Dial emission sweep (dial mean / dial dark half / dial bright half, render : photo): 0.40 gave 1.043 / 1.105 / 1.026; 0.34 gave 1.019 / 1.072 / 1.004; 0.30 gave 1.001 / 1.050 / 0.988 (outer ring 0.983); 0.32 chosen as the compromise.

Region mean luminance (sRGB grey), render : photo: dial 1.010, dial outer ring 0.992, bezel 1.011, bracelet top 1.017, bracelet bottom 1.005, case top 1.028, case bottom 0.965. Dial dark half 1.061, bright half 0.996.

Known differences: drop shadow and background are not part of the asset; dark dial areas read about 6% lighter than the photo while the bright numerals and print match (nonlinear response, no single emission fixes both); case top about 3% brighter and case bottom about 3.5% darker (lighting on the sloped lugs, as in -0001); blue channel of the dial about 3% high; a thin dark joint line and a 1 px fringe at the bracelet row ends and lug edges remain; 3D hands/hub bevels add a faint outline; 2x upscale makes the dial print slightly softer than the photo; heights are estimated (no side view).
