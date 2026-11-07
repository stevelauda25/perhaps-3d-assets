# Baseline: TUDOR Ranger M79950-0008 (saved 2026-11-07, awaiting designer approval)

Front-relief build on the Ranger 39 template of M79950-0001 (same case, bezel, crown, bracelet, camera and pose) with the beige dial photo map. Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/tudor-m79950-0008.glb`, 939,640 bytes, sha256 `dc7ad3232ff2ac2b443fb0c8a85bd4519fa1f487acd03a68eb6f5d80a1e84a98` (GLB 2.0, two embedded JPEG image bufferViews, no external URIs) |
| Comparison render | `baseline_cmp-front_2048.png` (2048 px, white kit, 27.59 px/mm, pivot at the frame centre, same frame as the 2x photo with offset (+122, -206)), sha256 `c272a5f085614d1f65e4fc438caf924b3f97e9841fd3f81eda232814d51600ed` |
| Side by side | `baseline_vs_reference.png` (left: 2x reference padded into the 2048 frame, right: render), sha256 `e101a89bd0ab08a4273d7c51bdc2a5f67e88a28c0325ba3f5c562aad7b092047` |
| Reference | `../tudor-m79950-0008_900x1200.png` (original), `../tudor-m79950-0008_1800x2400.png` (2x working copy) |
| Job / step / spec | `jobs/tudor-ranger39-m79950-0008.json`, `pipeline/steps/watch_tudor_ranger39.py` (shared with -0001, unchanged), `baseline_spec.json`, `baseline_job.json` |
| Inputs rebuilt by | `python3 -B -m pipeline.tudor_ranger39_prep m79950-0008` |

Rebuild: `python3 -B -m pipeline.tudor_ranger39_prep m79950-0008 && python3 -B -m pipeline.jobs run jobs/tudor-ranger39-m79950-0008.json --force`

State: identical to -0001 except model/ids/paths (trace, dial map, steel map) and the measure file's per-photo values: hour tip (346, 543), minute tip (628, 532), seconds tip (308, 750) (end of the red tip; -0001's (295, 755) lies past it), seconds tail (499, 575), hand lume fractions. Hands carry the photo (`hands_photo`, emission 0.42), so the cream lume strips, black outlines, black minute-hand tip and black hub come from the photo. Dial emission 0.33 (same as the black dial, no increase needed: the beige map already carries the brightness), steel emission 0.32, dial specular 0, crystal alpha 0.02. The hand outline profiles in the spec are the -0001 ones (minute 14.07 mm, hour 9.39 mm; the photo's tips are about 0.1 mm longer).

Region mean luminance (sRGB grey), render : photo: dial 0.999, dial outer ring 0.997, bezel 1.022, bracelet top 1.016, bracelet bottom 1.005, case top (lugs) 1.036, case bottom 0.995, crown 0.992, beige dial background 0.995, dark features (numerals, indices, hand outlines; grey < 70 in the photo) 1.293 (29.5 vs 22.8 grey levels).
Dial emission trials (dial mean : photo): 0.33 -> 0.999, 0.29 -> 0.982 (dark features barely move, 1.272), so 0.33 was kept. One correction pass; steel parts left at the template emission.

Known differences: drop shadow and background are not part of the asset; black numerals/indices/outlines read about 7 grey levels lighter than the photo (emission lifts blacks, lowering it darkens the beige more); bezel about 2 percent and lug tops about 3.5 percent brighter (same as -0001); the minute-hand tip may look slightly forked where the 3D hand edge meets the printed index; lug corners and bracelet row ends slightly rounder than the photo; crown end flat-cut instead of rounded; render a little softer than the photo (2x upscale); heights estimated (no side view). Not verified: designer approval.
