# Baseline: PATEK PHILIPPE Cubitus 5821/1A (steel, green, 45 mm; saved 2026-11-07, awaiting designer approval)

Front-relief build on the 45 mm steel / olive green embossed dial / steel bracelet catalogue render (1920 x 2691, native size), NEW MODEL (Cubitus template; closest siblings the Aquanaut 5167A / 5168G builds). Three correction passes (emissions, bevels / gaps, triangle budget). Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/patek-58211a.glb`, 1,371,664 bytes, sha256 `0dc1bf7d9b8eb4d604e6daac1b3cdbc919a22de3d4b84e708f544059382ddc52` (GLB 2.0, declared length = file length, two embedded JPEG image bufferViews (steel map 1246 x 2048, dial map 912 x 912), no external URIs). 14 meshes, 7 materials, 14,780 triangles (18,856 vertices) |
| Comparison render | `baseline_cmp-front_1400.png` (1400 px, 16-bit PNG, white kit, 15.1222 px/mm = half of the native 30.2444 px/mm, pivot at the frame centre (700, 700); same pixel frame as the photo downscaled by 0.5 (INTER_AREA) with its pivot (488.55, 640.15) moved to (700, 700), sub-pixel shift), sha256 `0d0ee8e82776591f7290051853bd57a111946675578368d0d934a8246e6e887f` |
| Side by side | `baseline_vs_reference.png` (left: half-size reference on white in the 1400 frame, right: render), sha256 `4ed85df03bbdfe7826a4426e0045fc7def4f1abe882ea19d13d3c3d98c7626df`; `zoom_check.jpg` (3x crops, reference | render) |
| Reference | `../patek-58211a_original.png` (catalogue file, 1920 x 2691 RGBA, untouched; measuring and map source, no 2x copy) |
| Job / step / prep / spec | `jobs/patek-cubitus45-58211a.json`, `pipeline/steps/watch_patek_cubitus45.py`, `pipeline/patek_cubitus45_prep.py`, `config/watches/patek-cubitus45-58211a{,-measure,-trace}.json`, `baseline_spec.json`, `baseline_job.json` |
| Kit preset | `config/presets/watch_kit_white_front_patek_cubitus45.json` (15.1222 px/mm, 1400 square on the pivot) |

Rebuild: `python3 -B -m pipeline.patek_cubitus45_prep 58211a && python3 -B -m pipeline.jobs run jobs/patek-cubitus45-58211a.json --force`, then `cp outputs/jobs/patek-cubitus45-58211a/patek-cubitus45-58211a.glb models/watches/patek-58211a.glb`.

## Geometry (real layered mesh, front-locked)

Meshes: `case` (silhouette slab between the shoulders, 1452 tris), `bezel` (ring: measured octagon outer edge to the traced window edge at bezel_z 8.9, recessed rim down to the dial window at 8.2, 360 rays, 5.8k tris), `crystal` (flat polygon prism, alpha 0.02), `dial` (flat polygon prism with the native 912 px photo map), three hands (`hand_hour` / `hand_minute` / `hand_seconds`, two facets meeting at a ridge, at z 7.4 / 7.65 / 7.9) plus two lume inlays and a `hub` lathe (64 segments), `crown_3` (fluted-cylinder lathe, 64 segments), `bracelet_links_top` / `bracelet_links_bottom` (3 top and 5 bottom link pieces between the measured joints; outline = silhouette at every 0.25 mm row, so the shingled link edges follow the photo) and `bracelet_backing`. Depth is the 2.5D scale 0.35 (z 3.1 mm of visible relief); back flat. The 720-ray version of the same rings cost 50,424 triangles (bezel bevel facets 34.5k); 360 rays, no bevel and no hidden core prism bring it to 14,780 with no visible change (mean abs grey difference 3.07 versus 3.15 with the case bevel at 0.1).

Textures: steel map 1246 x 2048 (native crop of the whole watch, 1414 x 2321 px, INTER_AREA x 0.8823, JPEG q 90) projected from the front on case, bezel, crown, bracelet and hands; dial map 912 x 912 (native crop, q 93).

## State

Lighting vs the app's environment: every photo-projected part is emissive with specular 0 and roughness 0.6 (dial 0.35), so an environment light adds little. Emission strengths: steel parts (case, bezel, crown) 0.281; bracelet top 0.262, bottom 0.283 (non-metallic `strap_photo`, specular 0, roughness 0.6); hands / hub / lume 0.43 (`hands_photo`); dial photo map 0.334; crystal alpha 0.02 (black, no specular worth noting); dark `steel_gap` backing. No extra baked shadows.

Cubitus specific: scale 30.2444 px/mm = (right flank 1657.4 - left flank 296.0) / 45 mm (the photo is not centred on the pivot: case centre x 976.7, pivot (977.1, 1280.3), the hub centre); case slab between the shoulders at rows 608 (top, 22.25 mm) and 1978 (bottom, 23.0 mm), crown rows 1198..1384 replaced by the flank line; bezel outer = traced rounded octagon (top y 692, bottom y 1873, left x 383, right 1571, corner chamfers), window face edge = traced polygon (top 828.5, bottom 1726.5, left 528, right mirrored) with a 26 px recessed rim; bracelet joints (mm from the pivot) top 22.29 / 27.39 / 31.12 / 34 (end), bottom 22.9 (shoulder) / 28.99 / 34.71 / 38.34 / 41.49 / 41.9 (end); hands hour 302.84 deg (tip 8.66 mm), minute 50.81 deg (tip 13.02 mm), seconds 180 deg (tip 13.06 mm in the 6 o'clock index, counterweight tail 5.1 mm up to GENEVE); hub discs 40.2 / 21.4 px; crown radius 2.84 mm, axis y 1292 (12 px below the pivot), axial 1.63 mm.

Region mean luminance (sRGB grey, 1400 frame, render : photo): whole watch 1.003, dial plate 0.997 (62.1 grey levels), dial bright features (hands, indices, print) 1.005, bezel brushed face 1.004, bracelet top 1.007, bracelet bottom 1.002, case left wall 1.016, case right wall 0.985, crown 0.998, polished bottom band 1.001, shoulder top 1.023, shoulder bottom 0.963 (the last includes the bracelet's polished insert at the case end). Mean abs grey difference over the opaque silhouette 3.07, silhouette IoU 0.9926. Emission trials (first build -> kept): dial 0.325 -> 0.334 (plate 0.993 -> 0.997), bracelet top 0.285 -> 0.262 (1.012 -> 1.007), bracelet bottom 0.285 -> 0.283, steel 0.285 -> 0.281 (bezel 1.006 -> 1.004). Corrections that mattered: bracelet piece gap 0.06 -> 0 and bevel 0.25 -> 0 (the groove showed as a dark line through the polished inserts that straddle a joint), case bevel 0.35 -> 0 and flatter shoulder ramp (tip_z 3.4 -> 6.4; the sloped shoulders shaded 3 to 7 % differently top and bottom).

## Zoom check

`zoom_check.jpg` (3x, upper dial, hands / hub, lower dial). Sharp: "PATEK PHILIPPE", "GENEVE", "SWISS MADE", minute dots, applied indices with their lume inlays, the embossed grid, date, the hand edges and lume inlays line up with the photographed ones (no halo, no gap visible at 3x). Soft: all dial print and grid are the photo's own pixels (30 px/mm native, shown at 2x the half-frame), so small text is as soft as the photo, not sharper. Remaining: the render's thin seconds shaft is slightly darker and sharper than the photo's smoothly shaded hairline; the hub's lower dark ring and the soft shadows of the real hands are only the photograph's (the 3D hands sit on top and cast almost none); a 1 px light line sits across the bottom polished insert at the case end (row about 1971, +8 grey, a case / bracelet height step seen from the front); the bracelet polished inserts, brushed grain and link overlaps are flat photo texture (the links themselves are separate pieces).

Known differences: the background, the soft drop shadow under the bracelet and the alpha rim are not part of the asset; the embossed grid, applied indices, print, minute dots, date window, brushed / polished facets, crown flutes and the polished inserts are texture only; the 3D hands, crown, bezel / rim step, dial plane and bracelet link pieces are geometry; the left case wall (x 296..383) and the right guards are flat photo texture on the case slab; the hour / minute / seconds-shaft centre lines sit 0.8 to 1.4 px (native) left of the pivot in the photo (camera tilt), not modelled; the window and bezel outlines are traced polygons (within about 2 px native); heights have no side view (real case thickness about 9.6 mm), back flat.

## Template for the next Cubitus variants

Other Cubitus references (other dial colours, the 5821/1A in other metals) use the **same** prep and step, read-only:

```sh
key=<sku-normalized>                      # e.g. another 5821 row; reference folder references/patek-cubitus-<...>/ holds patek-$key_original.png
ref=references/patek-cubitus-5821-1a      # the prep reads references/patek-cubitus-5821-1a/patek-$key_original.png: copy the photo there or edit MODEL["ref"] in a prep copy
cp config/watches/patek-cubitus45-58211a-measure.json config/watches/patek-cubitus45-$key-measure.json     # then RE-CHECK on the new photo (list below)
python3 -B -m pipeline.patek_cubitus45_prep $key
sed "s/58211a/$key/g" config/watches/patek-cubitus45-58211a.json > config/watches/patek-cubitus45-$key.json
sed "s/58211a/$key/g" jobs/patek-cubitus45-58211a.json > jobs/patek-cubitus45-$key.json
python3 -B -m pipeline.jobs validate jobs/patek-cubitus45-$key.json && python3 -B -m pipeline.jobs run jobs/patek-cubitus45-$key.json --force
cp outputs/jobs/patek-cubitus45-$key/patek-cubitus45-$key.glb models/watches/patek-$key.glb
```

**Template (keep as is):** the step, prep, kit lighting, materials, pose, heights (case body_z 6.6, flat shoulders tip_z 6.4, bezel_z 8.9, rim z 8.2, dial z 7.0, hands z, crown z 5.0), bracelet gap 0 / bevel 0, hands emission 0.43, steel emission 0.281 as a start, the geometry of the 45 mm case (octagon and window polygons, shoulders 22.25 / 23.0, crown profile), 360 rays, the 1400 half-scale frame centred on the pivot.

**Per variant (re-check on the new photo, never trust these numbers):** pivot (hub centre, 4x crop), flank rows and the printed `scale_px_per_mm`, hand angles / tips / widths (perpendicular edge scans about the pivot, threshold ~100) and lume inlays, crown rows / profile, bracelet joints (silhouette steps and dark seams: `strap.bracelet.pieces_mm` and `tip_top` / `tip_bottom`), and the emissions: dial (colour dependent, nonlinear; olive green needed 0.334), bracelet top / bottom separately, steel. A different metal (gold) may need non-white lume / different `steel` roughness only.
