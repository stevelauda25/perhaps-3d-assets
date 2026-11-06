# Baseline: TUDOR Royal 40 M2840D1A0-0001 (saved 2026-11-07, awaiting designer approval)

Front-relief build made with the Royal 36 -0101/-0103 recipe on the 40 mm photo, tuned over five correction passes. This build also sets the **Royal 40 template**. Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/tudor-m2840d1a0-0001.glb`, 1,549,756 bytes, sha256 `34779a3f296d5b194adc56470011f52c6ba38bc1e7f5f4530a10f0d5abd871b3` (GLB 2.0, two embedded JPEG image bufferViews, no external URIs) |
| Comparison render | `baseline_cmp-front_2048.png` (2048 px, white kit, 27.8 px/mm, pivot at the frame centre; the same pixel frame as the 2x photo with its pivot (900, 1218) moved to (1024, 1024)), sha256 `9b1eeef0f6369b9a3b346cf32abc851ef116199038e0a441e34a9d3eda65a4cd`. 2048 not 1800: the bracelet runs 506 px (1x) below the pivot |
| Side by side | `baseline_vs_reference.png` (left: 2x reference padded into the 2048 frame, right: render) |
| Reference | `../tudor-m2840d1a0-0001_900x1200.png` (original), `../tudor-m2840d1a0-0001_1800x2400.png` (2x working copy) |
| Job / step / spec | `jobs/tudor-royal40-m2840d1a0-0001.json`, `pipeline/steps/watch_tudor_royal40.py`, `baseline_spec.json`, `baseline_job.json` |
| Inputs rebuilt by | `python3 -B -m pipeline.tudor_royal40_prep m2840d1a0-0001` (trace, dial map, steel map in `outputs/watches/tudor-royal40-m2840d1a0-0001/`) |

Rebuild: `python3 -B -m pipeline.tudor_royal40_prep m2840d1a0-0001 && python3 -B -m pipeline.jobs run jobs/tudor-royal40-m2840d1a0-0001.json --force`

State: steel parts carry the reference photo projected from the front; hands/hub/lume use the same photo through their own material (`hands_photo`, emission 0.42); bracelet is flat with rows and polished pieces at the photo's measured joints (gap 0.06 mm, outline inset 0.04 mm); the case and bracelet outlines use the photo's real left and right silhouette (alpha > 128); dial is the 2x photo map (day and date windows, indices, print flat in it); steel emission 0.33, dial emission 0.40, dial specular 0, crystal alpha 0.02.

Region mean luminance (sRGB grey), render : photo: dial 1.059, dial outer ring 1.024, bezel 1.015, bracelet top 1.018, bracelet bottom 1.005, case top 1.030, case bottom 0.966, polished channels (top) 1.027, gold features (indices, hands) about 0.99.

Known differences: drop shadow and background are not part of the asset; dial dark areas read a little lighter than the photo (about 5 percent mean) while the gold features match; case top reads about 3 percent brighter and case bottom about 3 percent darker (lighting on the sloped lugs); a thin dark joint line (0.06 mm) and a 1 px outline fringe at the bracelet row ends and lug edges remain; hands/hub 3D bevels add a faint outline; heights are estimated (no side view, values copied from the Royal 36).

## Template for the next Royal 40 variants (-0002, -0003: same photo template, different dial)

Per variant `<sku>` (e.g. `m2840d1a0-0002`), with the photo already at `references/tudor-royal-40-<sku>/tudor-<sku>_900x1200.png` and REFERENCE_PLAN.md / sources.md written:

```sh
cp config/watches/tudor-royal40-m2840d1a0-0001-measure.json config/watches/tudor-royal40-<sku>-measure.json   # then check the per-dial values below
python3 -B -m pipeline.tudor_royal40_prep <sku>        # 2x copy, trace, dial_photo.jpg, steel_photo.jpg
# spec: copy config/watches/tudor-royal40-m2840d1a0-0001.json to tudor-royal40-<sku>.json; change only model, note, trace, dial_map, steel_map (paths with <sku>)
# job: copy jobs/tudor-royal40-m2840d1a0-0001.json to jobs/tudor-royal40-<sku>.json; replace the id string everywhere, keep step watch_tudor_royal40 and the Royal 40 preset
python3 -B -m pipeline.jobs run jobs/tudor-royal40-<sku>.json
cp outputs/jobs/tudor-royal40-<sku>/tudor-royal40-<sku>.glb models/watches/tudor-<sku>.glb
```

Template values (same for all Royal 40 photos, if the photo frame is the same): pivot, case_edge_left_x, bezel/crystal rings, crown box, tip_rows_px, channel_mm, segments, all hand lengths/angles/tails (the catalogue time is 10:09:xx), and in the spec: case, bezel, crown, bracelet rows/pieces/gap/inset, hands, materials, steel emission. Check them on the new photo by overlaying (render vs the 2x padded photo, same frame); a different photo crop would change them.

Per dial: the dial/hand colours in the photo (hands may be steel or gold: nothing to set, the hands carry the photo), dial emission (0.40 black; raise for light dials only if the render reads darker), the date window box in the measure JSON (metadata only), lume ranges (hand_lume, only affect the lume strip geometry), and whether the day window exists (flat in the dial map). If a dial has Roman numerals or a different bezel, review the REFERENCE_PLAN first.
