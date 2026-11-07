# Baseline: TUDOR Black Bay 54 M79000N-0001 (saved 2026-11-07, awaiting designer approval)

Front-relief build with the Royal / Ranger recipe on the 37 mm Black Bay 54 photo, new model-specific step, three render passes. This build also sets the **Black Bay 54 template** (rubber strap M79000N-0002). Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/tudor-m79000n-0001.glb`, 993,732 bytes, sha256 `d69b763ec4dd5704dcf3d4d6ba4aaf5ef36ccc94279976bc6537ab9eed50474c` (GLB 2.0, two embedded JPEG image bufferViews, no external URIs) |
| Comparison render | `baseline_cmp-front_2048.png` (2048 px, white kit, 27.89 px/mm, pivot at the frame centre; same pixel frame as the 2x photo with its pivot (902, 1306) moved to (1024, 1024), i.e. offset (+122, -282)), sha256 `7c8d5905da8c543307c361adfe581684e6ebc301dea15886a42c006baa1ae18b`. 2048 so the whole watch fits (bracelet 467 px below the pivot at 1x) |
| Side by side | `baseline_vs_reference.png` (left: 2x reference padded into the 2048 frame, right: render), sha256 `086605136c772b07dec0eb3ca2b461058f7a32ac981d346106babb63919b2d52` |
| Reference | `../tudor-m79000n-0001_900x1200.png` (original), `../tudor-m79000n-0001_1800x2400.png` (2x working copy) |
| Job / step / spec | `jobs/tudor-bb54-m79000n-0001.json`, `pipeline/steps/watch_tudor_bb54.py`, `baseline_spec.json`, `baseline_job.json` |
| Inputs rebuilt by | `python3 -B -m pipeline.tudor_bb54_prep m79000n-0001` (trace, dial map, steel map in `outputs/watches/tudor-bb54-m79000n-0001/`); prep is a variant copy of `pipeline/tudor_ranger39_prep.py` (crown rows follow the crown box; trace notes for the dive bezel / strap) |

Rebuild: `python3 -B -m pipeline.tudor_bb54_prep m79000n-0001 && python3 -B -m pipeline.jobs run jobs/tudor-bb54-m79000n-0001.json --force`

State: steel parts (case, bezel, crown, bracelet) carry the reference photo projected from the front; hands/hub/lume use it through `hands_photo` (emission 0.43); dial is the 2x photo map (print, indices, minute track, photographed hands stay in it); case and strap outlines follow the photo's alpha silhouette (including the bracelet rivet ears); steel emission 0.31 with specular 0, dial emission 0.29, dial specular 0, crystal alpha 0.02. Black Bay 54 specific: bezel = steel coin-edge ring around a black insert (one lathe, numerals / markers / triangle come from the projected photo), shallow domed crystal, hands from measured outline profiles plus lume polygons (snowflake hour hand with lume strip and diamond, sword minute hand, seconds needle with counterweight disc and lume disc), fluted crown without guards (22 teeth, narrower end ring), lugs that rise above the round bezel (case tip z 3.3 so the strap pieces sit on top: no seam at the lug ends), `strap.kind` in the spec picks `bracelet` (built: outer / centre / outer brushed columns, joints measured top and bottom separately, vertical joint lines slightly converging toward the bottom end) or `rubber` (one continuous column over the silhouette; build-tested only with placeholder values).

Region mean luminance (sRGB grey), render : photo: dial 1.031, dial outer ring (rehaut) 0.988, bezel insert 1.025, coin-edge ring 1.019, bracelet top 1.015, bracelet bottom 0.997, centre column top 1.021 / bottom 0.999, lug top 1.024, lug bottom 0.985, case flank 0.997, crown 0.978, bright dial features (indices, hands, print) 0.983, dark dial 1.180 (about 3 grey levels on 17), whole watch 1.011.
Emission trials (dial : photo, steel specular 0 from pass 2): pass 1 dial 0.33 / steel 0.32 / spec 0.03 -> dial 1.046, bezel 1.050; pass 2 dial 0.31 / steel 0.31 -> 1.038, 1.025; pass 3 dial 0.29, hands 0.43 -> 1.031, 1.025. Pass 3 also lowered the case tip_z 3.7 -> 3.3 (seam).

Known differences: drop shadow and background are not part of the asset; dark dial areas read about 3 grey levels lighter than the photo while bright features match (one emission value cannot fix both; lowering it darkens the rehaut ring below 1); bezel insert 2.5 percent and lug tops 2.5 percent brighter, crown 2 percent darker; the crown end is squarer and its top/bottom edge flatter than the photo's rounded flutes, and it sits about 2 px (1x) further out at the end; the bracelet joints and column sides carry a thin dark 3D-bevel line that is a little darker than the photo's; lug corners on the left are slightly rounder than the photo's; hands' 3D bevels add a faint outline; the render is a little softer than the photo (2x upscale); the bezel triangle pearl, numerals and coin teeth are texture only (no geometry); heights are estimated (no side view, copied from the Royal/Ranger builds); the photo is about 3 px off-centre on the pivot (case anchored on the left edge, 13.946 px/mm), so the right bezel edge under the crown is about 6 px (0.4 mm) wider than photographed. Not verified: designer approval.

## Template for the Black Bay 54 rubber-strap variant (M79000N-0002)

Registry entry `m79000n` serves both SKUs. Photo, REFERENCE_PLAN.md and sources.md are written per variant at `references/tudor-black-bay-54-<sku>/`. Commands for `<sku>` = `m79000n-0002`:

```sh
cp config/watches/tudor-bb54-m79000n-0001-measure.json config/watches/tudor-bb54-m79000n-0002-measure.json   # then check the values below on the new photo
python3 -B -m pipeline.tudor_bb54_prep m79000n-0002      # 2x copy, trace, dial_photo.jpg, steel_photo.jpg
cp config/watches/tudor-bb54-m79000n-0001.json config/watches/tudor-bb54-m79000n-0002.json
# in the new spec change: model, note, trace, dial_map, steel_map (paths with m79000n-0002), strap.kind -> "rubber", strap.rubber.*, verified_mm only if the diameter differs
cp jobs/tudor-bb54-m79000n-0001.json jobs/tudor-bb54-m79000n-0002.json                                     # replace the id string everywhere (incl. references), keep step watch_tudor_bb54
cp config/presets/watch_kit_white_front_tudor_bb54.json config/presets/watch_kit_white_front_tudor_bb54_0002.json   # only if the pivot differs; otherwise reuse the preset as is
python3 -B -m pipeline.jobs run jobs/tudor-bb54-m79000n-0002.json
cp outputs/jobs/tudor-bb54-m79000n-0002/tudor-bb54-m79000n-0002.glb models/watches/tudor-m79000n-0002.glb
```

Template (same for any Black Bay 54 photo with this crop and the 10:09:xx pose; verify by diffing the render against the 2x photo padded with offset (+122, -282) for pivot (451, 653)): in the measure JSON the pivot, `case_edge_left_x`, `rings`, `crown`, the hand tips / tails / `hub_r` / lumes, `tip_rows_px` lug rows; in the spec the case, bezel, crystal, crown, hands (profiles and lume polygons), materials, pose, steel emission 0.31 / specular 0, dial emission 0.29. If the -0002 photo has the pivot elsewhere, re-measure the pivot, scale (`case_edge_left_x`), rings, crown and hand axes first; the preset and the padding offset follow the pivot (2x photo pivot at (1024, 1024)).

Per variant: the dial map (comes with the photo; the rubber-strap watch may have a different dial and hands: check the hand lengths / angles in the measure JSON and the hands profiles if the hands differ; a different time changes hand angles), dial emission (tune from region means), hands.emission if the lume or gold reads off, and the strap section:

- `strap.kind = "rubber"` builds one column over the whole silhouette from `strap.rubber.pieces_mm.strap.top|bottom` = `[[y0, y1], ...]` (mm from the pivot, ordered outward, top and bottom separately; start at the lug tip `case.tip_top` / `tip_bottom`, split at any transverse groove or end piece that the photo shows; gap 0.06 mm between pieces), heights `z_strap` (and `z0`, `bevel`, `backing_z`, `inset`, `backing_inset`). `centre_x_mm` is unused for `rubber` (keep the placeholder).
- Measure the strap joints on the -0002 photo like the bracelet: pixel-grid crops at 3-6x plus brightness-gradient scans down a few columns, top and bottom separately; convert with 13.946 px/mm about the pivot (mm = (px - pivot) / S). The strap section is the only geometry that differs; if the lug tips differ, update `case.tip_top` / `tip_bottom` (and keep `case.tip_z` below the strap's z so the strap pieces sit on top of the lug ends).
- Rubber reads differently from steel: the steel projected-photo material is reused (steel emission 0.31, specular 0); check the strap region mean and tune `steel.emission` only if the whole case/strap is off, or add a strap-only material in the step if the strap needs its own value.
- `strap.kind = "rubber"` was only build-tested (it runs and produces geometry); its look is not verified.
