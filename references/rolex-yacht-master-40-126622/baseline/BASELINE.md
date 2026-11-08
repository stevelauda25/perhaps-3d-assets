# Baseline: ROLEX Yacht-Master 40 126622 (40 mm Rolesium: steel case, platinum bidirectional bezel, slate dial, date with Cyclops lens, Oyster bracelet) (saved 2026-11-08, awaiting designer approval)

Front-relief build on the 40 mm steel / platinum catalogue render from the Rolex image host (1920 x 2857, native size). NEW MODEL: the Yacht-Master 40 template (the Yacht-Master 42 226627 follows), adapted from the Submariner Date 41 template (rings, coin edge, Cyclops lens as real geometry). Three builds (first build, two emission passes; no geometry correction was needed after the first). Approval is the designer's; this file is not a similarity score and says nothing about photorealism.

| Item | Value |
| --- | --- |
| GLB | `models/watches/rolex-126622.glb`, 1,479,124 bytes, sha256 `e96b03b9b5331a55998da903960f8319d92d783d4129cb4385631e1d72a81b86` (GLB 2.0, declared length = file length, two embedded JPEG image bufferViews: steel map 1038 x 1844 and dial map 716 x 716, both NATIVE, scale 1.0, no external URIs) |
| Geometry (glb_audit) | 15 meshes / primitives, 7 materials, 19,340 vertices, 24,853 triangles; size 44.7 x 79.8 x 3.1 mm (depth scaled 0.35); meshes: case (with crown guards), bezel (matte platinum band + polished ring), bezel_coin_edge (60-scoop toothed edge ring), crystal, dial, date_cyclops, hour / minute / seconds hands, hub, crown, crown neck, crown cap, bracelet links, bracelet backing |
| Comparison render | `baseline_cmp-front_1280.png` (1280 px, white kit, 11.5 px/mm, pivot at the frame centre; same pixel frame as the photo composited on white, pivot (961, 1425) moved to (1280, 1280) on a 2560 canvas and downscaled by 0.5 with INTER_AREA), sha256 `15ac9df5db53d2509725c4ad598769cc6b105f2e0914277313ad85a3567493c3` |
| Side by side | `baseline_vs_reference.png` (left: reference in the 1280 frame, right: render), sha256 `d57199fcdd9723a21743809d0680fe1e91b83f1d46c401952325c0d44df7dae0` |
| Reference | `../rolex-126622_original.png` (1920 x 2857 RGBA, untouched; measuring and map source, no working copy; URL in `../sources.md`) |
| Job / step / spec | `jobs/rolex-yachtmaster40-126622.json`, `pipeline/steps/watch_rolex_yachtmaster40.py` (NEW, copy of the Submariner Date 41 step + platinum bezel scoop phase / power), `pipeline/rolex_yachtmaster40_prep.py` (NEW, copy of the Submariner Date 41 prep), `config/watches/rolex-yachtmaster40-126622{,-measure,-trace}.json`, `baseline_spec.json`, `baseline_job.json` |
| Kit preset | `config/presets/watch_kit_white_front_rolex_yachtmaster40.json` (own copy: 11.5 px/mm, pivot (961, 1425)) |

Rebuild: `python3 -B -m pipeline.rolex_yachtmaster40_prep 126622 && python3 -B -m pipeline.jobs run jobs/rolex-yachtmaster40-126622.json --force`, then `cp outputs/jobs/rolex-yachtmaster40-126622/rolex-yachtmaster40-126622.glb models/watches/rolex-126622.glb`.

State: steel parts (case, bezel band, toothed edge, crown, bracelet) carry the photo projected from the front (`steel_photo.jpg`, planar UV), emission 0.27 (bezel band 0.265), hands 0.335 (traced photo outlines as flat polygons at z 7.7 / 7.95 / 8.2), dial map emission 0.325 (slate), Cyclops lens 0.255 (the projected photo: bright frame, glass reflection, window and numeral as photographed), crystal alpha 0.02, specular 0, no baked shadows beyond the photo.

Scale decision for the designer: the render is 920 px across the toothed bezel edge (scoop tips, radius 460 px), taken as the 40 mm anchor -> 23.0 px/mm (the Submariner's camera is 22.785). The case flank beside the bezel (x 484..1513 with the crown) is the lug body and reaches 20.7 mm radius at this scale; lug-to-lug is 46.4 mm and the bracelet lug gap 19.4 mm. If the designer prefers the flank as 40 mm (S = 23.78) or the Submariner's camera scale (S = 22.785), only `case_edge_left_x` in the measure file changes (the model scales; the kit preset's `scale_px_per_mm` is S / 2).

Registration checks (overlays on 1.3x..4x crops): rings (dial flat, crystal edge, bezel inner edge, matte band outer, polished ring, tooth tips) on the photographed edges; hand outlines on the photographed hands (hour Mercedes ring, minute, seconds needle + tail disc + lollipop); Cyclops outline on the lens. The render is a slightly tilted view (about 6 deg): lower parts shift down (bezel inner edge centre y 1424.3, toothed edge ~1427, flank 1437), so one ring centre (959.6, 1424.5) is used for all rings; the toothed edge ends up about 2 px high at the bottom (not visible in the cmp).

Region mean luminance (sRGB grey, 1280 frame, render : photo): whole watch 1.003, dial plate (hands and lens masked) 1.004 (123.1 vs 122.6), dial dark areas 1.023, dial bright features 0.978 (white indices / print clip a little, the usual bright-detail residue), rehaut ring 0.999, bezel matte band 1.009, polished ring not separated, toothed edge 1.011, bracelet top 1.009, bracelet bottom 0.998, case lug top 1.010, lug bottom 0.984, crown 1.008, hands (traced polygons) hour 1.005 / minute 1.002 / seconds 1.020, Cyclops lens 1.007. Mean abs grey difference over the photo silhouette 5.7 (mostly 1 px edges of print, numerals and brushed grain). Silhouette IoU 0.994 (render not-background = flood fill from the frame over min channel >= 238, vs the photo's alpha; 756 px render-only, 950 photo-only). Emission trials (steel / bezel / dial / hands / lens): 0.29 / 0.29 / 0.34 / 0.35 / 0.26 gave whole 1.012; 0.285 / 0.285 / 0.335 / 0.34 / 0.255 gave 1.010; 0.275 / 0.272 / 0.325 / 0.335 / 0.255 gave 1.005; 0.27 / 0.265 (kept) gave 1.003.

Known differences: the background and alpha rim are not part of the asset; the dial print, rehaut engraving, applied indices (including the white lume discs and bars), date window and numeral, the raised engraved bezel numerals / minute scale / triangle with their black fills and polished edges, the toothed-edge scoop shading, the lume strips and facets of the hands, the crown flutes' shading and the bracelet's brushed grain and mirror reflections are texture only (photo projection); the 3D hands (flat traced outlines), crown (16 coarse flutes), bezel band, polished ring, toothed edge (60 scoops as an outline wave, the scoop depth is texture), crystal, dial plane, Cyclops lens (faceted polygon with two bevel steps, not a true magnifier), bracelet links and case slab are geometry; the raised bezel numerals are NOT separate geometry (the brief: they are part of the bezel surface); the minute hand's outline touches the print at "DATE" by a few px and follows the glint above the hub by 1 to 2 px; case slab ends slope by a straight ramp; crown guards are flat case outline; no lume geometry; heights have no side view, back flat.

## Zoom check

`zoom_check.jpg` (3x crops of the 1280 frames, reference | render): upper dial (triangle, coronet, ROLEX, OYSTER PERPETUAL DATE, hour hand ring, lens edge), hands and hub, lower dial (YACHT-MASTER, SUPERLATIVE CHRONOMETER, seconds lollipop, 6 bar, SWISS MADE, 30 on the bezel). Separate 3x crops of the toothed edge at 12 and 3 o'clock, the crown and the bracelet top were compared too. Sharp: the Mercedes hour hand, the minute hand with lume strip, the cyan seconds needle with its tail disc and lollipop, the hub, indices and their polished frames, the dial print, the bezel scale and numerals, the toothed-edge scoops, the crown, the bracelet joints and the date window and numeral inside the lens. Soft: dial print and indices are as soft as the half-size photo (the shipped textures are native, 2x sharper in the app); the lens frame highlight and glass arc are a little weaker than in the photo; the dark dial is about 2 % light; the seconds hand paint is about 2 % bright. The seconds hand shows a hairline of the dial's dark shadow left of the lollipop (photo shadow, projected). No misplaced hand edges, dark gaps or stair-steps were visible.

## Template for the next Yacht-Master variants (YM42 226627 titanium)

Use this build as the template; the step, prep and kit preset are generic (spec / measure / trace driven; variant-named for the Yacht-Master family and used read-only by key). The YM42 photo is `references/rolex-yacht-master-42-226627/rolex-226627_original.png` (check with `ls references | grep yacht-master`).

```sh
k=226627; ref=rolex-yacht-master-42-$k; photo=$(ls references/$ref/*_original.png)
python3 - "$k" "$photo" <<'PY'
import json, sys
k, photo = sys.argv[1], sys.argv[2]
m = json.load(open("config/watches/rolex-yachtmaster40-126622-measure.json")); m["photo"] = photo
json.dump(m, open("config/watches/rolex-yachtmaster40-%s-measure.json" % k, "w"), indent=1)
s = json.dumps(json.load(open("config/watches/rolex-yachtmaster40-126622.json"))).replace("126622", k)
json.dump(json.loads(s), open("config/watches/rolex-yachtmaster40-%s.json" % k, "w"), indent=1)
j = json.dumps(json.load(open("jobs/rolex-yachtmaster40-126622.json"))).replace("rolex-yachtmaster40-126622", "rolex-yachtmaster40-" + k).replace("rolex-yacht-master-40-126622", "rolex-yacht-master-42-" + k)
json.dump(json.loads(j), open("jobs/rolex-yachtmaster40-%s.json" % k, "w"), indent=1)
PY
python3 -B -m pipeline.rolex_yachtmaster40_prep $k            # trace, dial_photo.jpg, steel_photo.jpg
python3 -B -m pipeline.jobs validate jobs/rolex-yachtmaster40-$k.json   # needs references/$ref/REFERENCE_PLAN.md
python3 -B -m pipeline.jobs run jobs/rolex-yachtmaster40-$k.json --force
cp outputs/jobs/rolex-yachtmaster40-$k/rolex-yachtmaster40-$k.glb models/watches/<glb from rolex_map.json>
```

Edit the new spec's and job's `model` / `note` / `baseline` text by hand, and point the job's `kit_preset` / `references` at a kit preset of your own (copy `config/presets/watch_kit_white_front_rolex_yachtmaster40.json`, set `scale_px_per_mm` = S / 2 and the pivot in the note): the YM42 is a different case size, so the camera scale and pivot are NOT the same as here.

**Same code for every Yacht-Master (do not touch):** the step (ring list, platinum band + polished ring + toothed edge with `bezel.teeth` / `flute_depth` / `flute_power` / `flute_phase`, crystal, Cyclops, hands from traces, crown, three-column bracelet) and the prep.

**Per photo (re-measure, never trust the 40's numbers):**
1. Scale and anchor: `measure.case_mm` (42), `case_centre_x`, `case_edge_left_x` (centre minus the toothed-edge tip radius at the pivot row: flute scoop start, check 3 clean sectors), pivot (hub screw, 6x crop), `ring_centre_px` (the dark bezel inner edge line, left / right and top / bottom), `rings` (radial profiles in a clean sector between numerals: dial flat, crystal edge, bezel inner edge, band outer, polished ring outer, tooth tips), `tip_rows_px` (lug ramps), crown box / `crown_rows`, `hub_r`.
2. Hands: the angles (the 40 reads 304.8 / 63.3 / 186.0 at about 10:09:31) and the ROIs (mask mode needs a threshold above the dial's brightest sunburst glint: 150 here; keep the ROI tight where print or an index touches the hand; the seconds hand is `shapes` along the needle). Check by overlay at 4x.
3. Date lens: `date.lens_px` (29 points on a 5x crop).
4. Bracelet: joint rows (brightness-step scans: columns 900..1020 for the polished centre, 770..840 for the brushed outer links, plus 2.4x strip crops), column lines, then recompute `strap.bracelet.pieces_mm` / `bounds_x_mm` (mm = (row - pivot row) / S; the snippet in this build's history: `top(y) = (py - y) / S`, `bot(y) = (y - py) / S`), `case.tip_top` / `tip_bottom`, `verified_mm.lug_to_lug`. If the YM42 bracelet is a different finish (titanium, brushed centre) only the photo changes.
5. Bezel: if the bezel has a different tooth count / scoop shape (YM42 has a different edge), adjust `bezel.teeth` (count the scoops on a 3x crop), `flute_phase` (0.5 = scoop at 12, 0 = ridge), `flute_depth`, `flute_power`; the bezel material (platinum band, ceramic, titanium) is only texture.
6. Emissions: dial (slate 0.325; a different colour needs its own trial, plate mean within ~1 %), steel 0.27, bezel 0.265, hands 0.335, date 0.255; `sources.md` row text and the dial / bezel description in `REFERENCE_PLAN.md`; if the photo's colours differ from the tracker's variant, say so in the report.
