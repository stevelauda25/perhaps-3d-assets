# Baseline: OMEGA Seamaster Planet Ocean 600M 42 mm 217.30.42.21.01.001 (saved 2026-11-07, awaiting designer approval)

Front-relief build on the 42 mm steel / black dial / black ceramic bezel with serrated steel coin ring / steel bracelet catalogue render, **follower / adapt** of the Omega Diver 300M template (step `watch_omega_diver300m`, bracelet build 210.30.42.20.03.001, see its `BASELINE.md`). One first build and two correction passes (crown guard edge, steel / dial emission, column gap). Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/omega-21730422101001.glb`, 995,340 bytes, sha256 `28b8c5e8a93154ab7ab14f0cfa47e0950fd25aa5d3057aea5dfd3993be9c3d3e` (GLB 2.0, declared length = file length, two embedded image bufferViews, no external URIs) |
| Comparison render | `baseline_cmp-front_2048.png` (2048 px, 16-bit PNG, white kit, 25.9 px/mm = 2 x 12.95; the frame is exactly the frame of the 2x working photo, pivot (512.1, 462.25) of the 1024 photo at (1024.2, 924.5)), sha256 `2f17310f6215b5a96ba0e05a4f1996807cb8be492cc813f381153242487221c2` |
| Side by side | `baseline_vs_reference.png` (left: 2x reference on white, right: render, 8-bit), sha256 `914409f38aee31c47c710c000f88106e16d401bf0572b262fbb543182d5d4485` |
| Reference | `../omega-21730422101001_original.png` (original, 1024 x 1024 RGBA), `../omega-21730422101001_2048x2048.png` (2x working copy; enlargement only) |
| Job / step / spec | `jobs/omega-planetocean42-21730422101001.json`, `pipeline/steps/watch_omega_diver300m.py` (read-only, template), `baseline_spec.json`, `baseline_job.json` |
| Inputs rebuilt by | `python3 -B -m pipeline.omega_planetocean42_prep 21730422101001` (copy of the Diver prep; reads `config/watches/omega-planetocean42-21730422101001-measure.json`) |
| Kit preset | `config/presets/watch_kit_white_front_omega_planetocean42.json` (25.9 px/mm, 2048 square, pivot at (1024.2, 924.5)); the Diver kits do not fit this photo |

Rebuild: `python3 -B -m pipeline.omega_planetocean42_prep 21730422101001 && python3 -B -m pipeline.jobs run jobs/omega-planetocean42-21730422101001.json --force`, then `cp outputs/jobs/omega-planetocean42-21730422101001/omega-planetocean42-21730422101001.glb models/watches/omega-21730422101001.glb`.

State: steel parts (case, bezel, crown, bracelet) carry the reference photo projected from the front (steel emission 0.30, specular 0), hands and hub `hands_photo` 0.43, dial = 2x photo map (emission 0.29), crystal alpha 0.02, case outline = alpha silhouette (angular lugs, crown guards). What differs from the Diver template:
- **Registration is new**: this photo is not the Diver frame. The left silhouette at the case middle is the serrated steel coin ring, outer radius about 272 px = 21 mm (42 mm case diameter of the Catalog row); the bracelet between the lugs is 271 px = 21 mm, so 12.95 px/mm (the Diver rubber photo's value). Pivot (512.1, 462.25) = intersection of the three hand axes (each hand symmetric about its axis within 0.3 px; hub pin hole 1.1 px lower). `ring_centre_mm` [-0.016, 0.151] (outer ceramic circle (511.73, 460.96) weighted 2:1 with the inner edge circle (512.2, 458.9); they differ 2 px in y).
- **Bezel** = black ceramic r 14.9..19.57 mm with the steel flange (sloped, chamfer 0.8 mm) inside and a **serrated steel coin ring** r 19.57..21.0 mm outside (coin-ring branch of the Diver step, `insert_out` < `bezel_out`, teeth are photo texture).
- **Hands** are solid: arrow hour (tip 110.8 px) and minute (arrow tip 166.4 px) hands and a lozenge seconds hand (ends 171.5 px), traced as signed outlines in the spec (`hands.parts`, `mirror` false, frame only, no lume polygons; the lume panels are texture).
- **Crown** 7.1 mm tall (rows 422..514 px), 10 wide flutes, `guard_x` 800.5 px: the prep copy takes the crown-guard edge instead of the mirrored left edge for the crown rows (the mirrored edge left a visible shelf at the crown corners).
- **No helium valve** in the silhouette; lug tips at rows 163.5 / 775.5 px (`tip_top` 23.0, `tip_bottom` 24.25 mm).
- **Bracelet** (`strap.kind` "bracelet"): three columns (brushed outer, polished centre, brushed outer), each with its own `pieces_mm` list top and bottom: joints = dark-line centroids from brightness scans, e.g. top outer L 24.07 / 28.24 / 32.24 mm, outer R 24.00 / 28.18 / 32.18, centre 25.02 / 26.43 / 30.14 / 33.38; bottom outer L 25.89 / 30.44 / 35.31 / 39.17 / 42.03, outer R 25.75 / 30.44 / 35.31 / 39.12 / 42.03, centre 26.89 / 32.61 / 37.01 / 41.14 (mm from the pivot); column boundaries x -5.01 / +5.04 mm at the top, the right one tapering to +4.52 mm at the bottom end; column gap `groove` 0.05, bevel 0.1.

Region mean luminance (sRGB grey, in the 2048 frame, render : photo): dial dark 1.048 (34.3 vs 32.7), dial grey 1.003, dial bright print / indices 0.983, steel flange 1.011, ceramic dark 1.331 (4.9 vs 3.7 grey levels, absolute), ceramic white 0.996, coin ring 1.018, lug top L 1.026 / R 1.021, lug bottom L 1.001, bracelet top (outer L 1.020, centre 1.006, outer R 1.018), bracelet bottom (outer L 1.005, centre 1.004, outer R 1.004), crown 1.002, crown guard 0.996, hands zone 0.987, whole watch 1.007. Mean abs grey difference over the silhouette 5.0 (edge pixels, bracelet ends, the soft alpha rim).

Known differences: the background and the soft alpha rim are not part of the asset; dark dial and ceramic areas read 1 to 2 grey levels lighter than the photo (dark floor is base-colour lighting); the bracelet is flat pieces with the projected photo (brushing, polished facets and joint shadows are texture, no 3D relief; thin facet lines inside a link are not joints and are not cut); the bracelet ends are straight cuts 2 px inside the alpha end; the double line of the bottom centre joint (rows 882 / 886) is one joint; the ceramic outer / inner circles and the flange are flattened to one ring centre (up to 1 px off); crown is a fluted prism with a smooth lathe cap (the three flat bands, the lower-left shadow and the cap edge are texture); hands are flat extrusions (the photographed lume panel and bevels are texture, the hub zone shape is inferred from the visible stubs); heights are the Diver template's (no side view). Not verified: designer approval.

## Template for the next Omega Planet Ocean 600M 42 mm variants

Same commands as above with `sku` replaced; copy, never edit, the files of this build:

```sh
sku=<normalised sku>; ref=references/omega-seamaster-planet-ocean-600m-42-$sku     # holds omega-$sku_original.png
cp config/watches/omega-planetocean42-21730422101001-measure.json config/watches/omega-planetocean42-$sku-measure.json   # re-check the registration by overlay first
python3 -B -m pipeline.omega_planetocean42_prep $sku                                # 2x copy, trace, dial_photo.jpg, steel_photo.jpg
cp config/watches/omega-planetocean42-21730422101001.json config/watches/omega-planetocean42-$sku.json   # trace / dial_map / steel_map paths, dial + steel emission, hands.parts, bracelet pieces
sed 's/21730422101001/'$sku'/g' jobs/omega-planetocean42-21730422101001.json > jobs/omega-planetocean42-$sku.json
python3 -B -m pipeline.jobs validate jobs/omega-planetocean42-$sku.json && python3 -B -m pipeline.jobs run jobs/omega-planetocean42-$sku.json --force
cp outputs/jobs/omega-planetocean42-$sku/omega-planetocean42-$sku.glb models/watches/omega-$sku.glb
```

Template (keep): step `watch_omega_diver300m`, prep copy, kit preset if the photo has the same frame (25.9 px/mm, pivot (512.1, 462.25); otherwise copy it with `scale_px_per_mm` = 2 x S and `center_px` = 2 x pivot), case / bezel / crystal / dial / crown heights, coin-ring bezel radii (rings in mm), crown, hand outlines for the same hand style, bracelet column layout, emissions (steel 0.30, hands 0.43, black dial 0.29). Per watch (re-measure): pivot and scale (hands are symmetric about their axes only for the right pivot), hand outlines and lengths (other dial colours / hand styles), dial emission by colour (check both ways), bezel colour / ring centres, bracelet joints and column boundaries, silhouette-dependent values (`tip_rows_px`, crown box, `guard_x`).
