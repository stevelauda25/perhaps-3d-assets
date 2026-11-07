# Baseline: TUDOR Royal 40 M2840D1A0-0004 (saved 2026-11-07, awaiting designer approval)

Front-relief build made with the Royal 40 template of -0001 on the -0004 photo (silver sunburst dial, gold baton indices, day-date), tuned over two renders (dial and steel emission only). Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/tudor-m2840d1a0-0004.glb`, 1,530,664 bytes, sha256 `96e1a9b0566f735d9f7002d1566b9f9e4816091eb84041068e02c3d744ed300e` (GLB 2.0, two embedded JPEG image bufferViews, no external URIs) |
| Comparison render | `baseline_cmp-front_2048.png` (2048 px, white kit, 27.8 px/mm, pivot at the frame centre; same pixel frame as the 2x photo with its pivot (900, 1218) moved to (1024, 1024)), sha256 `15dc5b905458c54e2a4e3e9bc15f449cc62cef6a6e7b20996583d9c0b8ac819c` |
| Side by side | `baseline_vs_reference.png` (left: 2x reference padded into the 2048 frame, right: render), sha256 `dd3d8f3c90954e0b3b446fe7237d0c3e842f98e2d996f0805e71092b131f459e` |
| Reference | `../tudor-m2840d1a0-0004_900x1200.png` (original), `../tudor-m2840d1a0-0004_1800x2400.png` (2x working copy) |
| Job / step / spec | `jobs/tudor-royal40-m2840d1a0-0004.json`, shared `pipeline/steps/watch_tudor_royal40.py` and preset `config/presets/watch_kit_white_front_tudor_royal40.json` (read-only reuse), `baseline_spec.json`, `baseline_job.json` |
| Inputs rebuilt by | `python3 -B -m pipeline.tudor_royal40_prep m2840d1a0-0004` (trace, dial map, steel map in `outputs/watches/tudor-royal40-m2840d1a0-0004/`) |

Rebuild: `python3 -B -m pipeline.tudor_royal40_prep m2840d1a0-0004 && python3 -B -m pipeline.jobs run jobs/tudor-royal40-m2840d1a0-0004.json --force`

State: all template values of -0001 unchanged (pivot, rings, crown, bracelet joints, hand geometry; verified on this photo: silhouette alpha differs by at most 44/255 in 48 px, steel pixels outside the dial differ by 0.6/255 on average, gold hands with white lume at the same place). Steel parts, hands, hub and lume carry the reference photo projected from the front; dial is the 2x photo map; dial specular 0. Differences from -0001: only the dial map, dial emission 0.34 (-0001: 0.40) and steel emission 0.32 (-0001: 0.33).

Emission trials (dial mean render : photo): dial 0.40 / steel 0.33 gave 1.030 (dark half 1.034, bright half 1.026, outer ring 1.016, bracelet top 1.023, bezel 1.017); dial 0.34 / steel 0.32 gave 1.006 (dark 1.009, bright 1.004, outer ring 0.989). Unlike Royal 36 -0104 (silver dial rendered dark at 0.4, needed 0.55) the Royal 40 build is bright at 0.40, so no raise was needed; the response was near-linear here (dark and bright halves moved together).

Region mean luminance (sRGB grey, pixels with photo alpha above 200), render : photo: dial 1.006, dial outer ring 0.989, bezel 1.012, bracelet top 1.019, bracelet bottom 1.005, case top 1.030, case bottom 0.941, case sides 0.992; gold features (indices, hands) 1.020. Dial BGR 1.006 / 1.006 / 1.006. (Case top/bottom use a 200 px wide centre strip beside the bezel; they are not the same regions as the -0001..-0003 notes, the same measure on the -0001 baseline gives 1.035 / 0.946.)

Known differences: drop shadow and background are not part of the asset; case top about 3% brighter and case bottom about 6% darker (lug slopes lit by the shared kit, the same on -0001); bracelet top about 2% brighter; a thin dark joint line and 1 px outline fringe at bracelet row ends and lug edges; the hands' 3D bevels add a faint outline; the render is slightly softer than the photo (2x upscale); heights are estimated (no side view). Not verified: designer approval.
