# Baseline: TUDOR Black Bay GMT M79830RB-0001 (saved 2026-11-07, awaiting designer approval)

Front-relief build with the Royal / Ranger / Black Bay 54 recipe on the 41 mm Black Bay GMT photo, new model-specific step and prep, two render passes (pass 1 dial emission 0.29, pass 2 0.28). This build sets the **Black Bay GMT template**. Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/tudor-m79830rb-0001.glb`, 1,094,744 bytes, sha256 `1bfc21b4f5e90b9536d07c7f8a4b0e2b8f279466933a1c7ecea226cd66c8aca2` (GLB 2.0, declared length = file size, two embedded JPEG image bufferViews, no external URIs) |
| Comparison render | `baseline_cmp-front_2048.png` (2048 px, 16-bit, white kit, 27.122 px/mm, pivot at the frame centre; same pixel frame as the 2x photo with its pivot (900, 1220) moved to (1024, 1024), i.e. offset (+124, -196)), sha256 `e81e46389c20c53a4f6d4dcfad77cf49ac161f677e2883203ddc7c130ce0f4d4` |
| Side by side | `baseline_vs_reference.png` (left: 2x reference composited on white and padded into the 2048 frame, right: render), sha256 `30c05725cc9b35f7cd2fa34ac61021b2b1e85f7fd75279896e7a226e12f0435c` |
| Reference | `../tudor-m79830rb-0001_900x1200.png` (original), `../tudor-m79830rb-0001_1800x2400.png` (2x working copy) |
| Job / step / spec | `jobs/tudor-bbgmt-m79830rb-0001.json`, `pipeline/steps/watch_tudor_bbgmt.py`, `baseline_spec.json`, `baseline_job.json`, kit preset `config/presets/watch_kit_white_front_tudor_bbgmt.json` |
| Inputs rebuilt by | `python3 -B -m pipeline.tudor_bbgmt_prep m79830rb-0001` (trace, dial map, steel map in `outputs/watches/tudor-bbgmt-m79830rb-0001/`; copy of `pipeline/tudor_bb54_prep.py` that adds the fourth, GMT hand to the trace) from `config/watches/tudor-bbgmt-m79830rb-0001-measure.json` |

Rebuild: `python3 -B -m pipeline.tudor_bbgmt_prep m79830rb-0001 && python3 -B -m pipeline.jobs run jobs/tudor-bbgmt-m79830rb-0001.json --force && cp outputs/jobs/tudor-bbgmt-m79830rb-0001/tudor-bbgmt-m79830rb-0001.glb models/watches/tudor-m79830rb-0001.glb`

State: steel parts (case, bezel, crown, bracelet) carry the reference photo projected from the front; hands/hub/lume use it through `hands_photo` (emission 0.43); dial is the 2x photo map (print, indices, date window, minute track, photographed hands stay in it); case and bracelet outlines follow the photo's alpha silhouette (straight diagonal lug flanks, rivet ears); steel emission 0.31 with specular 0, dial emission 0.28, dial specular 0, crystal alpha 0.02. Black Bay GMT specific: bezel = one lathe with a 1.475 mm polished flange sloping up to the insert, the blue/red insert and the coin-edge ring (colours, numerals, pearls, triangle from the projected photo); case 41 mm with lug tips 24.22 mm (top) / 24.55 mm (bottom) from the pivot, ramp from 19 mm; four hands: hour snowflake (diamond 2.1 mm half width at 6.75 mm), minute sword with long taper, seconds needle with a rhombus lume and 8 px tail stub, red GMT hand = shaft as a profile hand plus the arrow head as a free polygon (red frame, inset white lume; `hands.polygons`, mm); crown with a neck (radius fraction 0.78) and 56-tooth fluted body (the photo has about 80 flutes); three-column bracelet with joints measured top and bottom separately (centre column has 0.5 mm dark bands at 27.2..27.7 mm top and 27.95..28.4 / 36.2..36.6 mm bottom).

Region mean luminance (sRGB grey), render : photo (pass 2): dial 1.031, dial outer ring (black rehaut) 1.085, polished flange 1.016, bezel insert 1.017 (blue 1.023, red 1.029, numerals 1.005), coin-edge ring 1.013, bracelet top 1.012, bracelet bottom 0.997, centre column top 1.014 / bottom 0.997, outer columns top 1.021 / bottom 1.006, lug top 1.013, lug flanks 0.986 / 1.004, crown 1.023, crown neck 0.959, bright dial features (indices, hands, print) 0.980, dark dial 1.223 (about 3 grey levels on 12), whole watch 1.011. Red GMT hand: 3766 photo px vs 3844 render px, 3722 shared.
Emission trials: pass 1 dial 0.29 -> dial 1.034, dark 1.231, bright 0.983; pass 2 dial 0.28 -> 1.031, 1.223, 0.980 (no useful further gain: dark areas stay about 3 grey levels light while bright features sit 2 percent low, as on the Black Bay 54).

Known differences: drop shadow and background are not part of the asset (the photo's grey shadow right of the watch reads as white in the render); dark dial and the black rehaut read about 3 grey levels lighter than the photo; the bracelet joint lines carry a slightly stronger dark 3D-bevel line than the photo; the crown neck is 4 percent darker, the crown flutes are texture only (56 teeth vs about 80 in the photo) and the crown edge is a little squarer; the bezel numerals, pearls, triangle, date and dial print are texture only (no geometry); hands' 3D bevels add a faint outline and the hour hand end bar is symmetric where the photographed one is slightly tilted; the render is a little softer than the photo (2x upscale); heights are estimated (no side view, copied from the Black Bay 54 build). Not verified: designer approval.

## Template for the next Black Bay GMT variants

No further variants are queued. Registry entry `m79830rb` (`tudor-black-bay-gmt` / `tudor-bbgmt`, 41 mm). For another SKU `<sku>` (for example a different bezel colour, a rubber/fabric strap or a different dial) of the same photo crop:

```sh
mkdir -p references/tudor-black-bay-gmt-<sku>       # photo + sources.md + REFERENCE_PLAN.md as for -0001
cp config/watches/tudor-bbgmt-m79830rb-0001-measure.json config/watches/tudor-bbgmt-<sku>-measure.json   # re-check pivot (450, 610), case_edge_left_x 172, hand tips, crown box on the new photo
python3 -B -m pipeline.tudor_bbgmt_prep <sku>        # 2x copy, trace, dial_photo.jpg, steel_photo.jpg
cp config/watches/tudor-bbgmt-m79830rb-0001.json config/watches/tudor-bbgmt-<sku>.json   # change model, trace, dial_map, steel_map paths
cp jobs/tudor-bbgmt-m79830rb-0001.json jobs/tudor-bbgmt-<sku>.json                       # replace the id / paths, keep step watch_tudor_bbgmt and the kit preset
python3 -B -m pipeline.jobs run jobs/tudor-bbgmt-<sku>.json
cp outputs/jobs/tudor-bbgmt-<sku>/tudor-bbgmt-<sku>.glb models/watches/tudor-<sku>.glb
```

Template (same for any Black Bay GMT photo with this crop and the 10:09:xx pose; check by diffing the render against the 2x photo padded with offset (+124, -196)): case (tip_top / tip_bottom, ramp, heights), bezel rings and heights, crystal, crown with neck, hand profiles and lume polygons, GMT arrow-head polygon, materials, pose, steel emission 0.31 / specular 0, bracelet pieces and column x lines. Per variant: the dial map (comes with the photo), dial emission, hand angles (`hour_tip` ... `gmt_tip` in the measure JSON; the GMT hand angle changes with the time zone, the head polygon in `hands.polygons.gmt.outline_mm` / `lume_mm` is in mm about the pivot and must be rotated about it by the angle change, the shaft follows the trace), the strap section if it is not this bracelet (`strap.kind = rubber` is build-tested only in the Black Bay 54 step), crown box and silhouette if the case differs. A black or other-colour bezel needs nothing: the insert is the projected photo.
