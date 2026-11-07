# Baseline: PATEK PHILIPPE Aquanaut 5168G green (saved 2026-11-07, awaiting designer approval)

Front-relief build on the 42.2 mm white gold / khaki green embossed dial / green composite rubber strap catalogue render (1920 x 2691, native size), follower of the Aquanaut 5167A-001 template (step and kit lighting unchanged; one correction pass, emissions only). Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/patek-5168g-green.glb`, 2,424,896 bytes, sha256 `c931de0e9b70a802cf6092deb29f49bfef8f67a84288fe5ff116f12ad814ac38` (GLB 2.0, declared length = file length, two embedded JPEG image bufferViews (dial map 978 x 978, steel map 1378 x 2179, both native size), no external URIs, 15 meshes) |
| Comparison render | `baseline_cmp-front_1280.png` (1280 px, 16-bit PNG, white kit, 14.9249 px/mm = half of the native 29.8498 px/mm, pivot at the frame centre; same pixel frame as the photo downscaled by 0.5 (INTER_AREA) with its pivot (479.5, 677.25) moved to (640, 640)), sha256 `1302c036f38334e5fad47c692d75623c5a10049109f19647c5fb6f0714bc8021` |
| Side by side | `baseline_vs_reference.png` (left: half-size reference on white in the 1280 frame, right: render), sha256 `794d4afe643a265d837eed1fa34fc6e7c01eb55a367bc64e2e1c9997911a269b` |
| Reference | `../patek-5168g-green_original.png` (catalogue file, 1920 x 2691 RGBA, untouched; measuring and map source, no 2x copy) |
| Job / step / spec | `jobs/patek-aquanaut42-5168g-green.json`, `pipeline/steps/watch_patek_aquanaut40.py` (the 5167A template step, read-only, no code change needed), `baseline_spec.json`, `baseline_job.json` |
| Inputs rebuilt by | `python3 -B -m pipeline.patek_aquanaut42_prep 5168g-green 5168g-green` (reads `config/watches/patek-aquanaut42-5168g-green-measure.json`; writes `-trace.json`, `outputs/watches/patek-aquanaut42-5168g-green/{dial_photo,steel_photo}.jpg`) |
| Kit preset | `config/presets/watch_kit_white_front_patek_aquanaut42.json` (14.9249 px/mm, 1280 square on the pivot) |

Rebuild: `python3 -B -m pipeline.patek_aquanaut42_prep 5168g-green 5168g-green && python3 -B -m pipeline.jobs run jobs/patek-aquanaut42-5168g-green.json --force`, then `cp outputs/jobs/patek-aquanaut42-5168g-green/patek-aquanaut42-5168g-green.glb models/watches/patek-5168g-green.glb`.

State: as the 5167A (steel parts carry the photo projected from the front, steel emission 0.285; non-metallic `strap_photo` rubber, emission 0.22 top / 0.305 bottom; hands / hub / lume `hands_photo` 0.43; native dial photo map emission 0.325; crystal alpha 0.02; case outline = alpha silhouette with the crown rows 1273..1440 replaced by the line at 42.2 mm from the left flank). 5168G specific: scale 29.8498 px/mm anchored on the left flank (329.17 px = 21.1 mm from the pivot (959.0, 1354.5)); bezel outer superellipse centre (0, -0.01) mm, half axes 21.1 x 20.85 mm, exponent 2.25; window scanned 15.8 to 17.2 mm from the pivot; case tips y +24.75 / -25.75 mm; strap pieces 18.8 to 32.15 (top) and 39.9 (bottom) mm; strap inner walls inside the lug zone are straight flaring / tapering lines (`top_end`, `bottom_end`; the prep copy supports them); hands hour 302.6 deg (10.39 mm), minute 50.6 deg (14.64 mm), seconds 180.28 deg (15.01 mm, counterweight tail 5.13 mm), hub discs 40 / 21 px; crown radius 2.78 mm, axial 3.89 mm.

Region mean luminance (sRGB grey, 1280 frame, render : photo): whole watch 1.002, dial plate 0.999 (109.3 vs 109.4 grey levels), dial bright features 1.009, dial dark areas 0.994, bezel face 1.006 (top 1.008, bottom 1.004, left 1.007, right 1.006), polished band 0.998, strap top 0.996, strap bottom 0.994, lug top 1.023, lug bottom 0.973, crown 1.003. Mean abs grey difference over the silhouette 3.8. Silhouette IoU 0.990 (the only blue area in the difference is the photo's white polished band at the strap / bezel junction, which the near-white mask test reads as background). Hand registration (bright masks in the hand zones): IoU hour 0.97, minute 0.98, seconds 0.95, centre-line offsets 0.2 half-px or less. Emission trials (first build -> kept): dial 0.31 -> 0.325 (plate 0.992 -> 0.999), strap top 0.18 -> 0.22 (0.977 -> 0.996), strap bottom 0.25 -> 0.305 (0.967 -> 0.994); steel 0.285 unchanged (bezel 1.006).

Known differences: the background, the soft drop shadow and the alpha rim are not part of the asset; the embossed grid, applied numerals, indices, minute-track flange, date window, brushed / polished facets, crown flutes and the strap's embossed pad are texture only; the 3D hands, crown, bezel / chamfer step and dial plane are geometry; lug inner walls and polished lug facets are flat photo texture (lug top reads 2 % light, lug bottom 3 % dark, a shading difference between the photo's facets and the projection); the strap / lug junction is a flat overlay; the hour hand's centre line is about 1.5 to 2.7 px (native) left of the pivot and the minute hand's about 1 px right in the photo (camera tilt), not modelled (the pivot is the hub centre); the hand pivot offsets by height are not modelled; heights have no side view (real thickness about 8.1 mm), back flat; the strap flare between lug start and bezel is a straight line (within about 2 px native); the khaki strap colour field is not stated for catalog row 102 (the photo, not the row text, is followed).

## Template for the next 5168G variants (blue row 104)

The blue 5168G is the same watch with a blue dial and strap (the studio render and geometry are the same, so the measure file differs only slightly); run the **same** prep and step, read-only:

```sh
key=5168g-blue
ref=references/patek-aquanaut-$key                                       # holds patek-$key_original.png
cp config/watches/patek-aquanaut42-5168g-green-measure.json config/watches/patek-aquanaut42-$key-measure.json   # then RE-CHECK on the blue photo (list below)
python3 -B -m pipeline.patek_aquanaut42_prep $key $key                   # trace, dial_photo.jpg, steel_photo.jpg; prints scale_px_per_mm
sed "s/5168g-green/$key/g" config/watches/patek-aquanaut42-5168g-green.json > config/watches/patek-aquanaut42-$key.json
sed "s/5168g-green/$key/g" jobs/patek-aquanaut42-5168g-green.json > jobs/patek-aquanaut42-$key.json            # step stays watch_patek_aquanaut40, kit preset watch_kit_white_front_patek_aquanaut42.json (reuse it only if the scale and pivot agree within a pixel, else copy it with the new numbers)
python3 -B -m pipeline.jobs validate jobs/patek-aquanaut42-$key.json && python3 -B -m pipeline.jobs run jobs/patek-aquanaut42-$key.json --force
cp outputs/jobs/patek-aquanaut42-$key/patek-aquanaut42-$key.glb models/watches/patek-$key.glb
```

(also sed the strings in the copied spec's `model` / note text, and replace `REFERENCE_PLAN.md` in the job's references with the blue folder's.)

**Template (keep as is):** `pipeline/patek_aquanaut42_prep.py`, `pipeline/steps/watch_patek_aquanaut40.py`, the kit lighting, materials, pose, heights (`case` body_z 6.6, bezel_z 8.9, chamfer_z 8.2, dial z 7.0, hands z, crown z 5.0), strap roughness / gap / lift / bevels, hands emission 0.43, steel emission 0.285 as a start, the 5168G geometry (case tips 24.75 / 25.75, ramp 20.5, hand lengths and profile shapes, crown profile, lug rows, strap piece start 18.8), the comparison conventions (half native scale, 1280 frame, pivot at the centre).

**Per variant (re-check on the blue photo, never trust the green numbers):** pivot (hub centre, 5x crop; the photos are the same render so expect a pixel or two), left flank x and the printed `scale_px_per_mm` (about 29.85; the brief expects the blue watch 1365 x 2162 px, a few px smaller than the green, so re-read the flank, crown rows, strap end rows and lug rows), hand angles (re-fit: the hands sit at a different time, edge fits in rows rotated about the pivot, lume thr 205) and tips, strap inner walls (saturation scan: for green S > 45 and V < 170; the blue strap needs its own thresholds), strap ends (`pieces_mm` ends = silhouette range less 0.1 mm, from the prep print `silhouette_rows_mm`), `crowns` base / rows, and the emissions: dial (nonlinear; green needed 0.325), strap top / bottom separately (green 0.22 / 0.305), steel (0.285 gave bezel 1.006 here).
