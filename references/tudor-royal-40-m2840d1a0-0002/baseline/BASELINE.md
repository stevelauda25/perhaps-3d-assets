# Baseline: TUDOR Royal 40 M2840D1A0-0002 (saved 2026-11-07, awaiting designer approval)

Front-relief build made with the Royal 40 template of -0001 on the -0002 photo (blue dial, Roman numerals, day-date), tuned over three renders (dial emission only). Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/tudor-m2840d1a0-0002.glb`, 1,600,912 bytes, sha256 `8d4b4b8a142960bcf61a2b46d487302f67a6a3a68ccc56b1d3ceade0c0458638` (GLB 2.0, two embedded JPEG image bufferViews, no external URIs) |
| Comparison render | `baseline_cmp-front_2048.png` (2048 px, white kit, 27.8 px/mm, pivot at the frame centre; same pixel frame as the 2x photo with its pivot (900, 1218) moved to (1024, 1024)), sha256 `54fe8c1bf2725572c832dcbbaf743ba17416e602b07889e32111731e338cbbc8` |
| Side by side | `baseline_vs_reference.png` (left: 2x reference padded into the 2048 frame, right: render), sha256 `655b1d9bdb720d96a3655b2da67c8e77febc9ab28961e03b0aa06326dd50ad4d` |
| Reference | `../tudor-m2840d1a0-0002_900x1200.png` (original), `../tudor-m2840d1a0-0002_1800x2400.png` (2x working copy) |
| Job / step / spec | `jobs/tudor-royal40-m2840d1a0-0002.json`, shared `pipeline/steps/watch_tudor_royal40.py` (read-only reuse), `baseline_spec.json`, `baseline_job.json` |
| Inputs rebuilt by | `python3 -B -m pipeline.tudor_royal40_prep m2840d1a0-0002` (trace, dial map, steel map in `outputs/watches/tudor-royal40-m2840d1a0-0002/`) |

Rebuild: `python3 -B -m pipeline.tudor_royal40_prep m2840d1a0-0002 && python3 -B -m pipeline.jobs run jobs/tudor-royal40-m2840d1a0-0002.json --force`

State: all template values of -0001 unchanged (pivot, rings, crown, bracelet joints, hand geometry; verified against this photo: silhouette alpha differs by at most 49/255 in 72 px, steel pixels outside the dial differ by 0.8/255 on average); steel parts, hands, hub and lume carry the reference photo projected from the front (the photographed steel/white lume); dial is the 2x photo map; steel emission 0.33, dial emission 0.33, dial specular 0. Differences from -0001: only the dial map and the dial emission (0.40 -> 0.33).

Dial emission trials (dial mean render : photo): 0.40 -> 1.042, 0.37 -> 1.030, 0.33 -> 1.013.

Region mean luminance (sRGB grey), render : photo: dial 1.013, dial outer ring 1.000, bezel 1.017, bracelet top 1.026, bracelet bottom 1.006, case top 1.030, case bottom 0.968; dial dark half 1.047, dial bright features (numerals, hands) 0.989; dial BGR 1.007 / 1.010 / 1.028 (blue channel about 2% strong).

Known differences: drop shadow and background are not part of the asset; dial dark blue areas read about 5% lighter while numerals/hands read about 1% darker (one emission value cannot fix both); case top about 3% brighter and case bottom about 3% darker (lug slopes); a thin dark joint line and 1 px outline fringe at bracelet row ends and lug edges; the hands' 3D bevels add a faint outline; the render is slightly softer than the photo (2x upscale); heights are estimated (no side view). Not verified: designer approval.
