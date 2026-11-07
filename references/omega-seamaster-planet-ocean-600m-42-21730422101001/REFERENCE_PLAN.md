# Reference plan: OMEGA Seamaster Planet Ocean 600M 42 mm 217.30.42.21.01.001 (steel, black dial, black ceramic bezel with serrated steel coin ring, steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). FOLLOWER / ADAPT of the Omega Diver 300M bracelet build [210.30.42.20.03.001](../omega-seamaster-diver-300m-21030422003001/REFERENCE_PLAN.md): the step is reused, the prep is a renamed copy, everything else is re-measured on this photo.

## Target asset

Front relief GLB `models/watches/omega-21730422101001.glb` (tracker rule: lowercase brand-SKU, letters and digits only), flat back, 2.5D depth, flat front-matched steel bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright render, transparent background (no drop shadow), 1024 x 1024 PNG | `omega-21730422101001_original.png` | HAVE, the only source (kept untouched) |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Diver template, back flat |

## Measured on this photo (continuous px of the 1024 x 1024 frame)

| Item | Result |
| --- | --- |
| Relation to the Diver photos | same render family and hand pose (10:09:36), but NOT the same frame: the case is a Planet Ocean (angular lugs, serrated steel coin ring outside the ceramic, no helium valve, larger crown with guards), so the Diver registration (pivot, scale 12.8957 / 12.951) was re-derived |
| Scale | the left silhouette at the case middle is the coin ring (x 239 at row 460): its radius about 272 px = 21 mm (the 42 mm case diameter); cross-check: the bracelet between the lugs is 271 px = 21 mm. 12.95 px/mm is used (the Diver rubber photo's value) |
| Pivot | (512.1, 462.25): the three hand axes, each hand symmetric about its axis within 0.3 px (minute / seconds nearly collinear, the hour hand fixes the position); the hub pin hole is 1.1 px lower |
| Bezel | ceramic ring r 203.4 .. 253.4 px (circle fits, outer centre (511.73, 460.96), inner (512.2, 458.9): one `ring_centre_mm`), steel flange r 193 .. 203.4, serrated coin ring r 253.4 .. 272 |
| Hands | hour 304.2 deg (arrow tip 110.8 px), minute 47.2 deg (arrow tip 166.4 px), seconds 221.8 deg (lozenge at 100..137 px, ends 171.5 px); all solid, traced as signed outlines |
| Crown | x 783..831 px, rows 422..514 (7.1 mm tall), wide flutes; crown guards (right silhouette 796..801 px above and below) belong to the case silhouette |
| Bracelet | three columns (brushed outer, polished centre, brushed outer); lug width 271 px; top outer joints at rows 150 / 96 / 44, centre 137.8 / 119.5 / 71.5 / 29.5, bottom outer 797 / 856 / 919 / 969 / 1006, centre 810 / 884 / 941 / 994.5; column boundary x 447.2 and 577.3 (the right one tapers to 570.6 at the bottom end) |
| Dial | black, silver-grey print, applied lume indices and arabic 12 / 3 / 6 / 9, date-less; photo map |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | `pipeline/steps/watch_omega_diver300m.py` read-only (bracelet kind, column driven, coin ring branch of the bezel, signed hand outlines) |
| Prep | `pipeline/omega_planetocean42_prep.py 21730422101001` (copy of the Diver prep with this model's names and notes) |
| Comparison frame | 2048 px square = the frame of the 2x photo (pivot (512.1, 462.25) -> (1024.2, 924.5)), camera 25.9 px/mm, `config/presets/watch_kit_white_front_omega_planetocean42.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.omega_planetocean42_prep 21730422101001   # -> 2x reference, config/watches/omega-planetocean42-21730422101001-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
