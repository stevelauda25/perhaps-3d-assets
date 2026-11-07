# Baseline: OMEGA Seamaster 300 41 mm 234.30.41.21.01.001 (saved 2026-11-07, awaiting designer approval)

Front-relief build on the 41 mm steel / black vintage dial / black ceramic bezel with knurled steel coin ring / steel bracelet catalogue render, with the Omega Aqua Terra recipe (own step and prep copies, no code change, first render pass accepted, no correction pass). It sets the **Omega Seamaster 300 template** (see the last section). Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/omega-23430412101001.glb`, 1,127,188 bytes, sha256 `246786ada88f0520059a404761dc805a2c48c5bdabd388b53db740fa10130f0d` (GLB 2.0, declared length = file length, two embedded JPEG image bufferViews, no external URIs) |
| Comparison render | `baseline_cmp-front_2048.png` (2048 px, white kit, 26.8976 px/mm; the frame is exactly the frame of the 2x working photo, pivot (509.03, 470.11) of the 1024 photo at (1018.06, 940.22), no padding or shift), sha256 `c01017e329fb5319d955e27052491c237c092f04d203dc07df4049b5cd8a4cee` |
| Side by side | `baseline_vs_reference.png` (left: 2x reference on white, right: render, 8-bit), sha256 `910059ee2f849cb15d856efe8340815651a064f9da786a4de20896373989efcb` |
| Reference | `../omega-23430412101001_original.png` (original, 1024 x 1024 RGBA), `../omega-23430412101001_2048x2048.png` (2x working copy; enlargement only) |
| Job / step / spec | `jobs/omega-seamaster300-23430412101001.json`, `pipeline/steps/watch_omega_seamaster300.py`, `baseline_spec.json`, `baseline_job.json` |
| Inputs rebuilt by | `python3 -B -m pipeline.omega_seamaster300_prep` (reads `config/watches/omega-seamaster300-23430412101001-measure.json`; writes the 2x copy, `-trace.json`, `outputs/watches/omega-seamaster300-23430412101001/{dial_photo,steel_photo}.jpg`) |
| Kit preset | `config/presets/watch_kit_white_front_omega_seamaster300.json` (26.8976 px/mm = 2 x 13.4488, 2048 square, pivot at (1018.06, 940.22)) |

Rebuild: `python3 -B -m pipeline.omega_seamaster300_prep && python3 -B -m pipeline.jobs run jobs/omega-seamaster300-23430412101001.json --force`, then `cp outputs/jobs/omega-seamaster300-23430412101001/omega-seamaster300-23430412101001.glb models/watches/omega-23430412101001.glb`.

State: steel parts (case, bezel, crown, bracelet) carry the reference photo projected from the front (steel emission 0.30, specular 0); hands, hub and lume use `hands_photo` (emission 0.43); the dial is the 2x photo map (print, lume triangles, numerals, minute track, the polished inner flange and the photographed hands stay in it; emission 0.30, specular 0); crystal alpha 0.02; case outline = the alpha silhouette including the coin-ring teeth. Seamaster 300 specific: 41 mm anchored on the circle of the knurled coin-ring tooth tips (alpha edge on rays, centre (509.61, 468.37), r 275.70 px, 13.4488 px/mm; cross-check bracelet between the lugs 274 px = 20.4 mm); pivot (509.03, 470.11) from the three hand axes (the minute and seconds lines sit 1.2 px off it: hands carry their own signed outlines); one ring centre 3.1 px above the pivot (`ring_centre_mm` [0.028, 0.231]); **bezel = black ceramic insert (r 227.0..268.4 px, flat) inside a steel coin ring (r 268.4..275.2 px, 0.2 mm lower)**; no crown guards, no helium valve; crown x 779..827.6 px, 6.5 mm tall, 16 flutes, cap from x 816; lugs at y 163 / 803.5 px (tip_top 22.75, tip_bottom 24.75 mm); hands are **solid signed outlines** (broad arrow hour hand with a lume triangle, sword minute hand with a lume strip, lollipop seconds hand with a lume disc and a round counterweight boss) measured per 2..4 px in rotated strips; **three-column steel bracelet** (polished outer links, brushed centre link) with joints measured per column (outer top 12 / 35 / 88 / 152.5, centre top 19.5 / 64.5 / 123.5, outer bottom 815.2 / 894.5 / 962 / 1010, centre bottom 762 / 845.5 / 924 / 986 px rows), joint gaps over a `steel_photo` backing (they show the photographed pixels).

Region mean luminance (sRGB grey, in the 2048 frame, render : photo): dial dark 1.048 (28.1 vs 26.8 grey levels), dial mid 0.969, dial bright print / lume 0.993, dial inner flange 0.978, bezel ceramic dark 1.020, bezel numerals 0.996, coin ring 1.002, lug top 1.021, lug bottom 1.001, bracelet top (outer L 1.026, centre 1.013, outer R 1.025), bracelet bottom (outer L 1.003, centre 1.002, outer R 1.001), crown 0.988, hands zone 0.998, whole watch 1.010. Mean abs grey difference over the silhouette 5.4 (edge pixels, the bracelet ends, the soft alpha rim). Emission was not retuned (first pass: dial 0.30 / steel 0.30 / hands 0.43 as the Aqua Terra and Diver builds).

Known differences: the background and the soft alpha rim are not part of the asset; dark dial areas read about 1.3 grey levels light (the dark floor is base-colour lighting); the bracelet is flat pieces with the projected photo (brushing, polished facets and joint shadows are texture, no 3D relief); joints are straight cuts at the measured rows (the photo's outer-link joints are slightly curved, the two outer columns use the same rows); the bracelet ends are straight cuts 2 px inside the photo ends (the photo has rounded outer corners and a darker end bevel; the render shows a thin black band at the bottom end); the top outer links read about 2.5 percent light; the knurled teeth are in the silhouette and the texture only, the coin ring is a smooth lathe; the crown cap is a smooth lathe and the flutes are 16 even teeth; the hands are flat extrusions (facets, the hub detail and the lume are texture); the sub-pixel parallax between bezel, inner rim, tooth circle and hands (1.7 to 4 px) is flattened to one ring centre; the source is a 1024 px render, so everything is softer than the Tudor builds; heights are copied from the Aqua Terra / Diver builds (no side view). Not verified: designer approval.

## Template for the next Omega Seamaster 300 variants (other 41 mm dials, 300 on a strap)

Prep, step and kit preset are generic: a variant normally needs only new measure / spec / job JSON plus a copy of the prep with another MODEL name. Nothing of this build is to be edited, copy it.

```sh
sku=<lower-case sku, letters and digits only>
ref=references/omega-seamaster-300-$sku                      # folder that already holds omega-$sku_original.png
cp pipeline/omega_seamaster300_prep.py pipeline/omega_seamaster300_<variant>_prep.py   # change MODEL["name"] (e.g. omega-seamaster300-<variant>) and the default sku
cp config/watches/omega-seamaster300-23430412101001-measure.json config/watches/omega-seamaster300-<variant>-$sku-measure.json   # RE-MEASURE every value (list below)
python3 -B -m pipeline.omega_seamaster300_<variant>_prep $sku
cp config/watches/omega-seamaster300-23430412101001.json config/watches/omega-seamaster300-<variant>-$sku.json   # model, trace, dial_map, steel_map, hands, crown, ring_centre_mm, emissions, bracelet joints
cp jobs/omega-seamaster300-23430412101001.json jobs/omega-seamaster300-<variant>-$sku.json                         # ids / output / spec / trace strings; the step stays watch_omega_seamaster300
cp config/presets/watch_kit_white_front_omega_seamaster300.json config/presets/watch_kit_white_front_omega_seamaster300_<variant>.json   # scale = 2 x px_per_mm, center_px = 2 x pivot
python3 -B -m pipeline.jobs validate jobs/omega-seamaster300-<variant>-$sku.json && python3 -B -m pipeline.jobs run jobs/omega-seamaster300-<variant>-$sku.json --force
cp outputs/jobs/omega-seamaster300-<variant>-$sku/omega-seamaster300-<variant>-$sku.glb models/watches/omega-$sku.glb
```

(Same photo geometry: only change `MODEL["name"]` so the output folders do not collide; the template's kit fits as is.)

**Template (keep as is):** the step `pipeline/steps/watch_omega_seamaster300.py` (case from the silhouette, ceramic insert + coin ring lathe, crystal, dial lathe with the photo map, signed solid hands, crown, column-driven bracelet with `edge_from` and a `steel_photo` backing), kit lighting and camera, materials, pose and depth scale, heights, steel emission 0.30, hands 0.43, dial 0.30 for a black dial (a lighter dial needs checking both ways, the response is nonlinear), cmp / regions conventions (frame = 2x photo frame).

**Per watch (re-measure on the photo, never copy):** scale (tooth-tip circle on rays, 41 mm), pivot (hand axes in rotated strips, grey > 65 on a dark dial; use saturation on a light dial), rings (inner ceramic edge, ceramic outer edge, tooth tips), `ring_centre_mm`, hand outlines and lume, crown box, lug rows, bracelet joint x lines (`bounds_x_mm`) and link rows (`pieces_mm`), emissions per region (`regions.py` of the scratch folder).
