# Baseline: OMEGA Speedmaster Calibre 321 Chronograph 39.7 mm 311.30.40.30.01.001 (saved 2026-11-07, awaiting designer approval)

Front-relief build on the 39.7 mm steel / black dial / steel bracelet catalogue render: follower of the Omega Moonwatch template (`pipeline/steps/watch_omega_moonwatch.py`, copied unchanged as `watch_omega_calibre321.py`), every number re-measured on this photo (one build pass plus one emission correction). Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/omega-31130403001001.glb`, 1,209,924 bytes, sha256 `9fb975976b717ae6f1bf45e8c3f3db6d4e98d2c96f5f2f0c7c41abe38c56bc14` (GLB 2.0, declared length = file length, two embedded JPEG image bufferViews, no external URIs) |
| Comparison render | `baseline_cmp-front_2048.png` (2048 px, 16-bit PNG, white kit, 28.4 px/mm; the frame is exactly the frame of the 2x working photo, pivot (511.72, 461.76) of the 1024 photo at (1023.44, 923.52)), sha256 `7cdc70a0ea484381d1d3d88af96d62a93ac59451cb656948a753a509af58ffb1` |
| Side by side | `baseline_vs_reference.png` (left: 2x reference on white, right: render, 8-bit), sha256 `d7a6158e02635ba984fc131c30959d8358aa6b4e7e5b0f5405ff002fd4c061d4` |
| Reference | `../omega-31130403001001_original.png` (original, 1024 x 1024 RGBA), `../omega-31130403001001_2048x2048.png` (2x working copy; enlargement only) |
| Job / step / spec | `jobs/omega-calibre321-31130403001001.json`, `pipeline/steps/watch_omega_calibre321.py`, `baseline_spec.json`, `baseline_job.json` |
| Inputs rebuilt by | `python3 -B -m pipeline.omega_calibre321_prep` (reads `config/watches/omega-calibre321-31130403001001-measure.json`; writes the 2x copy, `-trace.json`, `outputs/watches/omega-calibre321-31130403001001/{dial_photo,steel_photo}.jpg`) |
| Kit preset | `config/presets/watch_kit_white_front_omega_calibre321.json` (28.4 px/mm = 2 x 14.2, 2048 square, pivot at (1023.44, 923.52)) |

Rebuild: `python3 -B -m pipeline.omega_calibre321_prep && python3 -B -m pipeline.jobs run jobs/omega-calibre321-31130403001001.json --force`, then `cp outputs/jobs/omega-calibre321-31130403001001/omega-calibre321-31130403001001.glb models/watches/omega-31130403001001.glb`.

State: steel parts (case with straight lugs, bezel, crown, pushers, bracelet links) carry the reference photo projected from the front (steel emission 0.30, specular 0); hands, hub, sub-dial hands / hubs and lume use `hands_photo` (emission 0.402); the dial is the 2x photo map (emission 0.325, specular 0; print, tachymeter-style minute track, sub-dial rings and the photographed hands stay in it); crystal alpha 0.02; case outline = the alpha silhouette with the crown and pusher rows replaced by the case flank circle (`right_override_px`, 12-row chords of the circle (513.3, 460.7) r 281.6). Calibre 321 specific: scale **14.2 px/mm** from the case width 39.7 mm (left flank circle, r 281.2 .. 282.4 px), lug to lug 47.5 mm as built (47.3 measured on the photo, no published figure used, so `verified_mm.lug_to_lug` is not an independent check); pivot (511.72, 461.76) (hand axis residuals <= 0.05 px); bezel outer circle (513.3, 460.7) r 275.12, `ring_centre_mm` [0.111, 0.075]; bezel one black ring with a wide inner chamfer (r 212 .. 243); no crown guards (round flank); hour 303.468 deg / 136.3 px, minute 47.898 deg / 209.6 px, chrono seconds 221.828 deg / 210.7 px with a 52 px counterweight tail, beige lume strips; sub-dial batons with a pointed tip, hubs r 9.9 px; fluted crown to x 825 px (r 47.5) with a domed cap to 833.4; pushers +24.7 / -25.7 deg with own origins; **three-column bracelet** (outer, centre, outer; joints top x 440 / 576..582, bottom 442.5 / 583..577.5 px; outer rows top 20.15, 50, 88.1, 129.35, bottom 806.9, 862, 914.6, 958.9, 992.8; centre rows top 32.5, 69.1, 109.3, 163.4, bottom 768.3, 829.5, 889.5, 937, 978, 1008.3 px), 34 link pieces, gap 0.08 mm.

Region mean luminance (sRGB grey, in the 2048 frame, render : photo): dial dark 1.007, dial upper 1.010, dial lower right 1.006, sub-dial 9 1.005, sub-dial 6 1.001, bezel black top-left 1.021, bezel black bottom 1.028, case steel ring left (7 px wide strip at the silhouette edge) 0.887, inner chamfer left 1.009, lug top-left 1.017 / top-right 1.015, lug bottom 0.999 .. 1.005, bracelet top (outer L 1.014, centre 1.037, outer R 1.006), bracelet bottom (outer L 1.006, centre 1.005, outer R 1.003), crown 1.000, pusher up 1.004, pusher down 1.019, hour hand 1.030, minute hand 1.026, whole watch 1.001. Mean abs grey difference over the eroded silhouette 4.7. Emission trial: hands 0.415 -> 0.402 (hour / minute 1.034 / 1.030 -> 1.030 / 1.026; the photographed hands under the 3D hands limit the response).

Known differences: the background and the soft alpha rim are not part of the asset (the render's outer steel ring at the left silhouette edge is 1-2 px (2x) softer, hence 0.887 in the thin strip); the case and straight lugs are flat plates (the lug flank and the bezel steel ring carry the photo, no relief); the crown barrel end is square where the photo has a rounded end; the pushers are plain cylinders (their photographed dark bands are texture) with slightly flatter end faces; joint gaps are single 0.08 mm slits, the polished double joint lines of the bracelet links are only photo texture; the centre links at the top of the bracelet read about 4 percent bright; hands about 3 percent bright, the 3D hand edges can differ by 0.5 px from the photographed ones; the dark floor of the black dial and the bezel black are 1 to 3 percent light; the source is a 1024 px render, so everything is softer than the Tudor builds; heights are copied from the Moonwatch / Chronomat builds (no side view). Not verified: designer approval.

## Template for the next Calibre 321 style variants (three-column bracelet, no crown guards)

Same commands as the Moonwatch template, with the Calibre 321 names:

```sh
sku=<sku>; name=omega-calibre321
cp pipeline/omega_calibre321_prep.py pipeline/<new>_prep.py     # edit MODEL ref / name and the default sku
cp config/watches/omega-calibre321-31130403001001-measure.json config/watches/$name-$sku-measure.json   # measure every value again
python3 -B -m pipeline.<new>_prep $sku
cp config/watches/omega-calibre321-31130403001001.json config/watches/$name-$sku.json
cp jobs/omega-calibre321-31130403001001.json jobs/$name-$sku.json
python3 -B -m pipeline.jobs validate jobs/$name-$sku.json && python3 -B -m pipeline.jobs run jobs/$name-$sku.json --force
```

Template (keep): step, kit lighting / camera (only scale and centre), materials, heights, emissions 0.30 steel / 0.325 black dial / about 0.40 hands. Per watch: scale, pivot, rings, hands, sub-dial hubs, crown, pushers, bracelet joints, `right_override_px`.
