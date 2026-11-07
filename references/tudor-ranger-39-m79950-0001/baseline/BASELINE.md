# Baseline: TUDOR Ranger M79950-0001 (saved 2026-11-07, awaiting designer approval)

Front-relief build with the Royal recipe on the 39 mm Ranger photo, new model-specific step, tuned over four render passes. This build also sets the **Ranger 39 template** (beige M79950-0008). Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/tudor-m79950-0001.glb`, 979,680 bytes, sha256 `84f4e0fb9eda47e373bf6da8b4e93aeb2ded389703e49834f283e7112ce4858d` (GLB 2.0, two embedded JPEG image bufferViews, no external URIs) |
| Comparison render | `baseline_cmp-front_2048.png` (2048 px, white kit, 27.59 px/mm, pivot at the frame centre; same pixel frame as the 2x photo with its pivot (902, 1230) moved to (1024, 1024) i.e. offset (+122, -206)), sha256 `4d7b6d6ddf0a373b33ebca234a6991e476fb0738642a64cd79fa35f87bcc35c4`. 2048 so the whole watch fits (bracelet 505 px below the pivot at 1x) |
| Side by side | `baseline_vs_reference.png` (left: 2x reference padded into the 2048 frame, right: render), sha256 `823e68e6c1404b7fe56287b7e65e27b2ab9aa7a30cc07280470ffbacc958059a` |
| Reference | `../tudor-m79950-0001_900x1200.png` (original), `../tudor-m79950-0001_1800x2400.png` (2x working copy) |
| Job / step / spec | `jobs/tudor-ranger39-m79950-0001.json`, `pipeline/steps/watch_tudor_ranger39.py`, `baseline_spec.json`, `baseline_job.json` |
| Inputs rebuilt by | `python3 -B -m pipeline.tudor_ranger39_prep m79950-0001` (trace, dial map, steel map in `outputs/watches/tudor-ranger39-m79950-0001/`); prep is a variant copy of `pipeline/tudor_prep.py` (crown rows follow an off-pivot crown box, no date window needed) |

Rebuild: `python3 -B -m pipeline.tudor_ranger39_prep m79950-0001 && python3 -B -m pipeline.jobs run jobs/tudor-ranger39-m79950-0001.json --force`

State: steel parts (case, bezel, crown, bracelet) carry the reference photo projected from the front; hands/hub/lume use it through `hands_photo` (emission 0.42); dial is the 2x photo map (numerals, indices, print, hands stay in it); case and bracelet outlines follow the photo's alpha silhouette; steel emission 0.32, dial emission 0.33, dial specular 0, crystal alpha 0.02. Ranger-specific: smooth bezel (one lathe ring with polished chamfer, rounded outer edge), fluted crown (28 teeth, chamfered base, narrow neck, off the pivot row by 0.65 mm), hands from measured outline profiles (spear hour hand, sword minute hand, needle seconds hand with lume block and 4.6 mm tail), bracelet of three brushed columns (outer / centre / outer) with staggered joints and vertical joint lines that converge toward the end (no polished channels, no curl).

Region mean luminance (sRGB grey), render : photo: dial 1.026, dial outer ring 0.985, bezel 1.025, bracelet top 1.015, bracelet bottom 1.002, case top (lugs) 1.027, case bottom 1.011, crown 0.995, bright dial features (numerals, indices, hands) 1.001, dark dial 1.055.
Dial emission trials (dial mean : photo): 0.40 -> 1.053, 0.36 -> 1.038, 0.33 -> 1.026.

Known differences: drop shadow and background are not part of the asset; dark dial areas read about 5 percent lighter than the photo while the bright features match (one emission value cannot fix both; lowering it darkens the rehaut ring below 1); bezel about 2.5 percent and lug tops about 3 percent brighter; a thin light seam across the bottom centre bracelet column where the case slab ends (about 4 px); outer-column row ends and lug corners are slightly rounder than the photo's sharp corners; the crown has a flat cut where the photo shows a rounded end; the seconds hand is 0.06 mm off its photographed axis; hands' 3D bevels add a faint outline; the render is a little softer than the photo (2x upscale); heights are estimated (no side view, copied from the Royal builds). Not verified: designer approval.

## Template for the next Ranger 39 variants (M79950-0008 beige: same photo template, different dial)

Per variant `<sku>` (e.g. `m79950-0008`), photo already at `references/tudor-ranger-39-<sku>/tudor-<sku>_900x1200.png`, REFERENCE_PLAN.md and sources.md written:

```sh
cp config/watches/tudor-ranger39-m79950-0001-measure.json config/watches/tudor-ranger39-<sku>-measure.json   # then check the values below on the new photo
python3 -B -m pipeline.tudor_ranger39_prep <sku>        # 2x copy, trace, dial_photo.jpg, steel_photo.jpg
# spec: copy config/watches/tudor-ranger39-m79950-0001.json to tudor-ranger39-<sku>.json; change only model, note, trace, dial_map, steel_map (paths with <sku>) and, after a first render, dial.emission
# job: copy jobs/tudor-ranger39-m79950-0001.json to jobs/tudor-ranger39-<sku>.json; replace the id string everywhere (incl. the references list), keep step watch_tudor_ranger39 and the preset watch_kit_white_front_tudor_ranger39
python3 -B -m pipeline.jobs run jobs/tudor-ranger39-<sku>.json
cp outputs/jobs/tudor-ranger39-<sku>/tudor-ranger39-<sku>.glb models/watches/tudor-<sku>.glb
```

Template (same for any Ranger 39 photo with this crop and the 10:09:xx pose; verify by rendering and diffing against the 2x photo padded with offset (+122, -206)): the whole measure JSON (pivot 451, 615; case_edge_left_x 182; rings; crown box; tip_rows_px; hand tips, tails, hub_r; hand_lume) and the whole spec except the dial map and emission (case, bezel, crown, bracelet joints and centre_x lists, hand profiles, materials, steel emission). The preset (27.59 px/mm, 2048, centred) is shared as is.

Per dial: the dial map (the photographed hands/lume colour comes with it: hands carry the photo), dial emission (0.33 for the black dial; a light/beige dial will probably need about 0.5 to 0.55, tune from region means), and hands.emission if the lume strips read off. The prep's `date` box is a dummy at the pivot (no date window on any M79950); if a variant has a date window or a different hand shape, review the REFERENCE_PLAN first.
