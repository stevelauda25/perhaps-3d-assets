# Baseline: TUDOR Black Bay 58 Burgundy M7939A1A0RU-0001 (saved 2026-11-07, awaiting designer approval)

Front-relief build, FOLLOWER of the Black Bay 58 template ([black M7939A1A0NU-0001](../../tudor-black-bay-58-m7939a1a0nu-0001/baseline/BASELINE.md)): template step, prep and kit preset reused read-only, one render pass (no correction needed). Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/tudor-m7939a1a0ru-0001.glb`, 1,216,044 bytes, sha256 `c2a3eed5f3bf61353e0d903bd8e4ce21bef8c47b42c6cb017bd5290f9d3ca225` (GLB 2.0, two embedded JPEG image bufferViews, no external URIs) |
| Comparison render | `baseline_cmp-front_2048.png` (2048 px, 16-bit PNG, white kit, 27.744 px/mm, pivot at the frame centre; same pixel frame as the 2x photo with its pivot (902, 1226) moved to (1024, 1024), offset (+122, -202)), sha256 `054b2a9f848c99f74e29aa23ddb7615e8664181c0dcab87f3dad9124ae584500` |
| Side by side | `baseline_vs_reference.png` (left: 2x reference padded into the 2048 frame, including drop shadow and corner logo, right: render), sha256 `22c73c4d55c3a65755c8cc7b96ec0164fad797da18274a7378947ad4c4d28361` |
| Reference | `../tudor-m7939a1a0ru-0001_900x1200.png` (original), `../tudor-m7939a1a0ru-0001_1800x2400.png` (2x working copy) |
| Job / step / spec | `jobs/tudor-bb58-m7939a1a0ru-0001.json`, `pipeline/steps/watch_tudor_bb58.py` (template, unchanged), `baseline_spec.json`, `baseline_job.json` |
| Inputs rebuilt by | `python3 -B -m pipeline.tudor_bb58_prep m7939a1a0ru-0001` (template prep, largest alpha component only: the corner TUDOR logo and ticks stay out of the silhouette and steel map) |
| Kit preset | `config/presets/watch_kit_white_front_tudor_bb58.json` (template, unchanged) |

Rebuild: `python3 -B -m pipeline.tudor_bb58_prep m7939a1a0ru-0001 && python3 -B -m pipeline.jobs run jobs/tudor-bb58-m7939a1a0ru-0001.json --force`, then `cp outputs/jobs/tudor-bb58-m7939a1a0ru-0001/tudor-bb58-m7939a1a0ru-0001.glb models/watches/tudor-m7939a1a0ru-0001.glb`.

Registration check against the black photo: watch bbox identical (x 180..754, y 141..1123), silhouette differs by 193 px of 377,000, lug rows 303 / 944 equal, so pivot (451, 613), scale 13.8718 px/mm, rings, crown, bracelet joints and the 10:10:38 hand axes are the template's (hands: 511 render pixels outside and 525 photo pixels uncovered of 26.0k bright hand pixels, about 2 percent). Differences from the black build: spec/measure/job names and notes only; dial and bezel insert burgundy and hands silver-white (all from the photo maps / `hands_photo`), emissions unchanged (dial 0.29, hands 0.355, steel 0.31, specular 0).

Region mean luminance (sRGB grey, 2048 frame, render : photo): dial (no hands) 1.013, dial dark areas (photo < 60) 1.089 (24.4 vs 26.6 grey levels), dial bright features (> 150) 0.963, rehaut ring 0.981, bezel insert 1.027, coin-edge ring 1.017, hands + hub 1.008 (bright hand pixels 0.998), bracelet top 0.999, bracelet bottom 0.990, lug top 1.021, lug bottom 0.990, crown 0.975, whole watch (largest component) 1.006. Mean abs grey difference over the silhouette 5.2 (mostly edge pixels).

Known differences: drop shadow, logo and background are not part of the asset; dark burgundy dial areas read about 2 grey levels lighter than the photo and bright features about 4 percent darker (one emission value cannot fix both; not retuned); bezel insert 2.7 percent and lug tops 2 percent brighter, crown 2.5 percent darker; the render is slightly softer than the photo (2x upscale), hands' 3D bevels add a faint outline, bracelet joint bands and rounded outer link ends differ by 1-2 px as in the black build; bezel numerals, pearl triangle and coin teeth are texture only; heights copied from the Black Bay 54 / 58 builds (no side view). Not verified: designer approval.
