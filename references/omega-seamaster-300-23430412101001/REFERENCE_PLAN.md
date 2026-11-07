# Reference plan: OMEGA Seamaster 300 41 mm 234.30.41.21.01.001 (steel, black vintage dial, black ceramic bezel with a knurled steel coin ring, steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). NEW MODEL within the Omega approach (structure of the [Omega Aqua Terra 41](../omega-seamaster-aqua-terra-150m-41-22010412103005/REFERENCE_PLAN.md) and [Diver 300M](../omega-seamaster-diver-300m-21032422001001/REFERENCE_PLAN.md) builds, Seamaster 300 measurements).

## Target asset

Front relief GLB `models/watches/omega-23430412101001.glb` (tracker rule: lowercase brand-SKU, letters and digits only), flat back, 2.5D depth, flat front-matched steel bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright render, transparent background (no drop shadow), 1024 x 1024 PNG | `omega-23430412101001_original.png` | HAVE, the only source (kept untouched) |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Aqua Terra / Diver builds, back flat |

## Measured on this photo (continuous px of the 1024 x 1024 frame)

| Item | Result |
| --- | --- |
| Alpha bbox | x 233..827, y 0..1023 (bracelet ends = image borders; crown to x 827.6) |
| Anchor | circle of the knurled coin-ring tooth tips (alpha edge on 0.5 degree rays, 228 points, rms 1.3 px = tooth height): centre (509.61, 468.37), r 275.70 px = 41 mm / 2 -> 13.449 px/mm (cross-check: bracelet between the lugs 274 px = 20.4 mm; lug width 20 mm) |
| Pivot | hour 305.19, minute 47.8, seconds 221.7 deg centre lines cross at (509.03, 470.11) (hand height; distances 0.1 / 1.2 / 1.2 px); the bezel, inner rim and tooth circles are centred 1.7 to 4 px above it (camera tilt): `ring_centre_mm` [0.028, 0.231] |
| Rings (r px) | dial_flat 210 (end of the black dial; the polished steel inner flange r 212..226.5 is carried by the dial map), crystal_edge 226.5, bezel_in 227.0 (ceramic inner edge, circle rms 0.64), insert_out = ceramic outer edge 268.4 (rms 0.5..0.7), bezel_out = coin-ring teeth 275.2 (tips 275.7) |
| Bezel | black ceramic insert (beige numerals 10 / 20 / 30 / 40 / 50, minute marks, lume pip at 12 are print in the photo) inside a steel knurled coin ring, r 268.4..275.7, teeth ~3 px high (in the silhouette) |
| Crown | x 779..827.6, y 434.5..522 (87.5 px = 6.5 mm, centre 478.25), fluted to x 816 then a rounded cap; no crown guards, no housing shoulder |
| Lugs | tops y 163, bottoms y 803.5 (the silhouette widens from the bracelet at those rows); bracelet 274 px (20.4 mm) between the lugs, tapering to 216 px at the ends |
| Bracelet | three columns: polished outer links (x 395..443 at the top) and a brushed centre link (445..580); joint lines x 445 / 579.5 at the top end -> 442.5 / 582.7 at row 170, 439.4 / 580.2 at row 810 -> 442 / 577.4 at row 1010; joints (rows): outer top 12 / 35 / 88 / 152.5, centre top 19.5 / 64.5 / 123.5, outer bottom 815.2 / 894.5 / 962 / 1010, centre bottom 762 / 845.5 / 924 / 986 |
| Hands (about 10:06:36) | hour 305.19 deg broad arrow (head barbs 26 px half width at 89.5 px, tip 137.5 px, lume triangle 93.5..128.5), minute 47.8 deg sword with a lume strip (201.5 px), seconds 221.7 deg thin shaft with a lollipop (lume disc r 8.7 px at 171 px) and a round counterweight boss at 52 px behind the pivot |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | own copy `pipeline/steps/watch_omega_seamaster300.py` of the Aqua Terra step (no code change: coin-ring bezel, solid signed hands, bracelet backing from the photo and `edge_from` are already spec driven) |
| Prep | `pipeline/omega_seamaster300_prep.py` (copy of the Diver prep: tooth-tip circle anchor, steel-map crop clamped to the image) |
| Comparison frame | 2048 px square = the frame of the 2x photo (pivot (509.03, 470.11) -> (1018.06, 940.22)), camera 26.8976 px/mm, `config/presets/watch_kit_white_front_omega_seamaster300.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.omega_seamaster300_prep   # -> 2x reference, config/watches/omega-seamaster300-23430412101001-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
