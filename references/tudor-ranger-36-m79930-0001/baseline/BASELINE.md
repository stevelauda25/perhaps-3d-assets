# Baseline: TUDOR Ranger 36 M79930-0001 (saved 2026-11-07, awaiting designer approval)

Front-relief build with the Ranger 39 recipe ([Ranger 39 baseline](../../tudor-ranger-39-m79950-0001/baseline/BASELINE.md)) re-measured on the 36 mm photo; one render pass, no emission change needed. Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/tudor-m79930-0001.glb`, 915,656 bytes, sha256 `142e9f029104ffaddedee4357dfb031bf629f1f6dbd8df5ebbfed1fec25782c4` (GLB 2.0, two embedded JPEG image bufferViews, no external URIs) |
| Comparison render | `baseline_cmp-front_2048.png` (2048 px, white kit, 28.0 px/mm, pivot at the frame centre; same pixel frame as the 2x photo with its pivot (902, 1334) moved to (1024, 1024) i.e. offset (+122, -310)), sha256 `2a838258b6da568ee5e57da59d775e499faf7f98e6f76848ebd96a6aeeecc4e5` |
| Side by side | `baseline_vs_reference.png` (left: 2x reference padded into the 2048 frame, right: render), sha256 `a19c1f617de6ce5eb1f6d89376ead45abc26b07ec6e23dc7722e52b859a015c5` |
| Reference | `../tudor-m79930-0001_900x1200.png` (original), `../tudor-m79930-0001_1800x2400.png` (2x working copy) |
| Job / step / spec | `jobs/tudor-ranger36-m79930-0001.json`, `pipeline/steps/watch_tudor_ranger39.py` (reused unchanged), `baseline_spec.json`, `baseline_job.json` |
| Inputs rebuilt by | `python3 -B -m pipeline.tudor_ranger39_prep m79930-0001` (the prep is registry driven, reused unchanged; measure file `config/watches/tudor-ranger36-m79930-0001-measure.json`) |

Rebuild: `python3 -B -m pipeline.tudor_ranger39_prep m79930-0001 && python3 -B -m pipeline.jobs run jobs/tudor-ranger36-m79930-0001.json --force`

State: same materials as the Ranger 39 baseline (steel parts carry the projected photo, steel emission 0.32; hands emission 0.42; dial photo map emission 0.33, specular 0, crystal alpha 0.02). Own kit preset `config/presets/watch_kit_white_front_tudor_ranger36.json` (28.0 px/mm).

Differs from the Ranger 39: scale 14.0 px/mm (36 mm anchor), pivot row 667 (case higher in the frame, bracelet 427 px above / 453 px below the pivot), narrower bezel (rings 200 / 213 / 215 / 249 px), crown 3.1 mm radius centred on the pivot row (36 flutes), hands re-measured (hour 8.78 mm, minute 13.1 mm, seconds 13.06 mm with a stub tail of 4.24 mm, hub 1.36 mm), lug steps 21.1 / 21.45 mm, bracelet joints measured on this photo (centre column bottom has a fourth, thin end piece), vertical joint lines x 381.3 / 516.0 (top) and 380 / 516 (bottom).

Region mean luminance (sRGB grey), render : photo: dial 1.022, dial outer ring 0.993, bezel 1.023, bracelet top 1.011, bracelet bottom 0.998, case top (lugs) 1.023, case bottom 1.032, crown 0.963, bright dial features 0.996, dark dial 1.048. Joint rows match the photo within 1 to 3 px at 2x.

Known differences: drop shadow and background are not part of the asset; dark dial areas read about 5 percent lighter than the photo while bright features match (one emission value cannot fix both); bezel and case about 2 to 3 percent brighter; crown about 4 percent darker, and its end cap is squarer than the photo's rounded end; numerals, indices and print are a little softer than the photo (2x upscale); the 3D hands add a faint bevel outline; the dial/bezel rings are centred on the pivot while the photo's ring centre is 1.2 px (1x) to the left; heights are estimated (no side view, copied from the Ranger 39). Not verified: designer approval.
