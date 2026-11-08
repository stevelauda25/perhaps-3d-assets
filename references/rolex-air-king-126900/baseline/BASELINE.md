# Baseline: ROLEX Air-King 126900 (saved 2026-11-08, awaiting designer approval)

Front-relief build on the 40 mm steel / black dial / Oyster bracelet catalogue render (1920 x 2857, native size). NEW MODEL: this is the Rolex Air-King template (round Oyster case with a domed polished bezel and Oyster bracelet; other round Oyster-case Rolex follow). One build, then 4 correction passes (seconds-hand outline order, crown / guard silhouette rows, bezel dome / bevel flattening, dial emission). Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/rolex-126900.glb`, 1,190,768 bytes, sha256 `fcaddac742b7a1e98bf822081ef6cfa19b04347af9e168e52b5b557f83d1bb12` (GLB 2.0, declared length = file length, two embedded JPEG image bufferViews (dial map 802 x 802 native, steel map 1000 x 1836 native, scale 1.0: the 2048 px cap does not bite), no external URIs) |
| Geometry (glb_audit) | 15 meshes, 15 primitives, 7 materials, 18,698 vertices, 30,224 triangles; size 44.0 x 80.9 x 3.1 mm (depth scaled 0.35) |
| Comparison render | `baseline_cmp-front_1280.png` (1280 px, 16-bit PNG, white kit, 11.2931 px/mm = half of the native 22.5861 px/mm, pivot at the frame centre; same pixel frame as the photo downscaled by 0.5 (INTER_AREA) with its pivot (479.6, 712.5) moved to (640, 640)), sha256 `8c0ae5f98dd42a86a55949199fa280be478c129c80e493e11911896dfee9ecf4` |
| Side by side | `baseline_vs_reference.png` (left: half-size reference on white in the 1280 frame, right: render), sha256 `6ea0f7d235c6ff82c0220f3b4069185e09e8f7eb713d6f47f17041286123ca5b` |
| Reference | `../rolex-126900_original.png` (Rolex catalogue render, 1920 x 2857 RGBA, untouched; measuring and map source, no 2x copy; URL in `../sources.md`) |
| Job / step / spec | `jobs/rolex-airking-126900.json`, `pipeline/steps/watch_rolex_airking.py` (NEW, the Air-King template step), `pipeline/rolex_airking_prep.py` (NEW), `config/watches/rolex-airking-126900{,-measure,-trace}.json`, `baseline_spec.json`, `baseline_job.json` |
| Inputs rebuilt by | `python3 -B -m pipeline.rolex_airking_prep 126900` (reads `config/watches/rolex-airking-126900-measure.json`; writes `-trace.json`, `outputs/watches/rolex-airking-126900/{dial_photo,steel_photo}.jpg`) |
| Kit preset | `config/presets/watch_kit_white_front_rolex_airking.json` (11.2931 px/mm, 1280 square on the pivot) |

Rebuild: `python3 -B -m pipeline.rolex_airking_prep 126900 && python3 -B -m pipeline.jobs run jobs/rolex-airking-126900.json --force`, then `cp outputs/jobs/rolex-airking-126900/rolex-airking-126900.glb models/watches/rolex-126900.glb`.

State: steel parts (case with lugs and crown guards, bezel, crown, bracelet backing) carry the photo projected from the front (steel_photo material, specular 0, roughness 0.6, emission 0.285); bracelet rows and centre-link pieces use the same photo with their own emissions (top 0.275, bottom 0.29); the three hands (traced photo outlines, flat polygons at z 7.4 / 7.65 / 7.9, thickness 0.12, depth scale 0.35) use `hands_photo`, emission 0.40 (the photographed hands stay in the dial map); dial plate = native photo map with emission 0.30, specular 0 (the rehaut ring and the minute track are part of the map); crystal alpha 0.02 (alpha-blended); window core dark `steel_gap`. Case outline = alpha silhouette (lugs and crown guards included) between the end-link tips (+22.75 / -25.0 mm), crown rows 1357..1508 replaced by the notch line at x 1408. Measured here: scale 22.5861 px/mm (left flank 507.5 to pivot 959.2 = 20.0 mm), bezel outer ellipse half axes 452 x 445 px centred (959.4, 1427.5), bezel inner edge circle r 392.4 px centred (958.8, 1421.3) (window 17.2 to 17.5 mm from the pivot), hands hour 304.6 deg (arrowhead tip 8.9 mm) / minute 63.1 deg (14.1 mm) / seconds 186.1 deg (14.8 mm, lume ring r 0.93 mm, head disc at -5.0 mm), hub discs 25 / 19.5 px, crown axis y 1436 radius 78 px axial 92 px.

Emissive parts and strengths (all in the spec): steel_photo 0.285, bracelet top 0.275, bracelet bottom 0.29, hands_photo 0.40, dial 0.30; no specular on photo parts, no baked shadows beyond the photo's own.

Region mean luminance (sRGB grey, 1280 frame, render : photo): whole watch 1.000, dial plate 1.015 (69.3 vs 68.3), dial bright features 1.012, dial dark areas 1.000, rehaut ring 0.961, bezel face 1.006, bracelet top 1.006, bracelet bottom 0.995 (centre 0.994, outer 0.998), lug top L / R 1.014 / 1.007, lug bottom L / R 0.992 / 0.989, case flank L 1.009, crown 1.013. Mean abs grey difference over the photo silhouette 3.5. Silhouette IoU 0.944 against the "render not near-white" test, which reads the photo's white polished bezel highlights as background. Emission trials: dial 0.33 -> 0.325 -> 0.30 (plate 1.027 -> 1.026 -> 1.015; the response is nonlinear), bezel dome slope and edge bevel flattened (a 0.2 mm bevel on the outer bezel wall lit a light rim that the photo does not have).

Known differences: the background and the alpha rim are not part of the asset; the dial print, numerals, minute track, rehaut engraving, brushed grain, bezel highlights and the black reflection at the upper right, crown flutes, Mercedes lines in the hour hand and the lume are texture only; the hands, crown, bezel, dial plane, bracelet rows and centre links are geometry; joints between rows are the photo's own dark lines plus a 0.05 mm gap over the dark backing; the case slab end-link tips slope toward the bracelet by a straight ramp; the centre-link pieces are flat-topped rounded rectangles (the photo's rounded link ends are texture); the rehaut ring reads 4 % dark (dial emission is shared with the plate); the seconds line sits within 1 px of the photo; hands are flat (no facets); the hour / minute / seconds axes pass 3 / 2 / 0.6 px off the hub in the photo (camera tilt) and are modelled as photographed; heights have no side view, back flat.

## Zoom check

`zoom_check.jpg` (3x crops, reference | render). The tool centres its crops on the non-white bounding box of the whole render (the watch plus bracelet), so its three crops land on the lower dial (Air-King script, SUPERLATIVE CHRONOMETER, seconds lume ring, 6, SWISS MADE, bezel edge), not on the hands; the hands, hub and upper dial were checked with extra 3 to 8x crops and difference images (outside this file). Sharp: all print, numerals and the lume ring (the dial map and hands are the photo's own native pixels at 22.6 px/mm); the hour (Mercedes disc, arrowhead) and minute hand edges line up within about 1 px, the seconds hand shaft, ring, head disc and tip line up within 1 px; the crown flutes and guards. Soft: the dial print and brushed grain are exactly as soft as the photo (JPEG-compressed render); the steel map is native (scale 1.0). Fixed during the passes: a mis-ordered seconds outline (half of the lume ring showed the unmasked dial map), a white wedge under the crown, a light rim on the bezel outer edge. No halos, dark gaps, stair-steps or misplaced hand edges remain visible in the crops; the faint outlines in the difference image around numerals and hands are 1 px registration residue.

## Template for the next Air-King / round Oyster-case Rolex variants (e.g. another Air-King dial; the same case and Oyster bracelet)

Run, per variant (key = normalized SKU; folder = references/rolex-<model>-<sku>):

```sh
key=126900; ref=references/rolex-air-king-126900
cp config/watches/rolex-airking-126900-measure.json config/watches/rolex-airking-$key-measure.json     # then RE-MEASURE everything marked "per photo" below; set "reference_dir"
python3 -B -m pipeline.rolex_airking_prep $key       # prints scale_px_per_mm, bracelet rows / pieces in mm, aperture range, map sizes
sed "s/126900/$key/g" config/watches/rolex-airking-126900.json > config/watches/rolex-airking-$key.json   # spec: model / note text, verified_mm.diameter, emissions
sed "s#rolex-air-king-126900#<ref folder name>#g; s/126900/$key/g" jobs/rolex-airking-126900.json > jobs/rolex-airking-$key.json
cp config/presets/watch_kit_white_front_rolex_airking.json config/presets/watch_kit_white_front_rolex_airking_$key.json   # set cameras.front_ortho.ortho.scale_px_per_mm = (trace scale_px_per_mm) / 2 and point the job's kit stage at it
python3 -B -m pipeline.jobs validate jobs/rolex-airking-$key.json && python3 -B -m pipeline.jobs run jobs/rolex-airking-$key.json --force
cp outputs/jobs/rolex-airking-$key/rolex-airking-$key.glb models/watches/rolex-$key.glb
python3 -B -m pipeline.glb_audit models/watches/rolex-$key.glb /tmp/x.md
```

(The prep reads the one `rolex-*_original.*` in the reference folder; the sibling Oyster Perpetual 41 uses its own files.)

**Template (keep as is):** `pipeline/steps/watch_rolex_airking.py` and `pipeline/rolex_airking_prep.py` (read-only unless a code change is needed), kit lighting, materials, pose, heights (`case` body_z 6.6, bezel_z 8.9, chamfer_z 8.2, bezel dome dz 0.08 / 0.04, bezel_bevel 0.04, dial z 7.0, hands z 7.4 / 7.65 / 7.9, crown z 5.0, bracelet z0 / z_side / lift / piece_lift / bevels / gap 0.05), `rays` = `aperture.n` = 180 (they must match), the structure of the measure file, the comparison conventions (kit frame 1280 square at half the working scale, pivot at the centre).

**Per photo (measure, never trust the 126900 numbers):**
1. `pivot` (hub centre, 8x crop with a 10 px grid), `anchor.rows` (rows near the pivot where the left silhouette is the bezel flank) and `case_mm` 40: the prep derives the scale from pivot-to-left-flank = case_mm / 2.
2. `crown_replace` rows and x (the notch = bezel edge hidden by the crown barrel; stop at the barrel's top and bottom rows so the guards stay in the silhouette) and the crown `base_px` / `profile_px` (radius, axial px; axis y can sit below the pivot).
3. `bezel_outer` (centre, half axes, exponent 2: gradient edge at 12 / 6 o'clock and the silhouette at 9) and `aperture.circle` (fit a circle to the last strong radial edge in the band just outside the rehaut; std about 2.5 px) and `chamfer_px`.
4. `hands[name].polygon_px`: outlines as [dx, dy up] px from the pivot, built from strip crops rotated about the pivot (width scans on a bright mask miss dark facets: read arrowheads and tips on a 10x strip by eye) and `hub_r_px`.
5. `bracelet.rows_px` (outer-link joints at an outer column) and `pieces_px` (centre-link joints at the centre column, 2 px each side of the dark joint line); case tips `case.tip_top` / `tip_bottom` in the spec (joint distance rounded up to 0.25 mm).
6. Emissions: dial (dark black dials land near 0.30; light dials higher), steel, bracelet top / bottom, hands, so region means are within a few percent.
