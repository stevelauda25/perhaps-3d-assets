# Reference plan: AUDEMARS PIGUET Royal Oak Offshore Diver 15720ST (42 mm steel, green waffle dial, green rubber strap)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). First Audemars Piguet asset: it sets the Offshore Diver approach (structure of the [Breitling Superocean 42 rubber build](../breitling-superocean-42-a17375211b1s1/REFERENCE_PLAN.md) with the screwed-bezel approach of the Cartier Santos Large). The blue variant (catalog row 78, same SKU) follows this template.

## Target asset

Front relief GLB `models/watches/audemars-15720st-green.glb` (tracker rule: lowercase brand-SKU; the SKU repeats for the blue watch, so the variant is appended), flat back, 2.5D depth, flat front-matched rubber strap.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright render, transparent background (soft alpha rim), 400 x 542 PNG | `audemars-15720st-green_original.png` | HAVE, what the catalog link returns (kept untouched) |
| 2 | Same asset, larger rendition (`&wid=1200&hei=1626`), 1200 x 1626 PNG, the watch is 344 x 506 px | `audemars-15720st-green_1200x1626.png` | HAVE, the working source for measuring and for the maps |
| 3 | Side / back / crown close-up | none | not available; heights are estimates (real case thickness 14.1 mm), back flat |

## Measured on this photo (continuous px of the 1200 x 1626 frame)

| Item | Result |
| --- | --- |
| Alpha bbox | x 438..781, y 578..1083 (strap ends at the top y 578 and the bottom y 1083, both with a shallow centre notch; crowns to x 438 and 781) |
| Anchor | no circle fits: the left flat of the octagonal case (median alpha edge over rows 780..815) is 21 mm (half of the listed 42 mm width) from the pivot, 6.914 px/mm |
| Pivot | hour and minute centre lines cross at (597.6, 796.5), hub circle fit (598.4, 796.6): pivot (598.2, 796.6) at hand height; everything higher sits 1.5..2.6 px higher (camera tilt): opening circle centre (598.8, 795.1) r 109.5, screws centred (599.0, 794.0) |
| Bezel | regular octagon (flats left 452.0 / right 745.0 / top 650.3 / bottom 946.0), eight hexagonal slotted screws (circumradius 10.6 px) on the vertex rays at 134.7 px, polished chamfer down to the round opening; rotating black ring (inner edge r 88..95, outer 109.5) with a cream sector between about 0 and 15 minutes and the 50 / 40 / 30 / 20 numerals (print) |
| Dial | green Mega Tapisserie waffle dial, rose-gold applied indices with white lume, AP logo, date window at 3, "300m / 1000ft AUTOMATIC" print: all in the photo map, the waffle is texture only |
| Crowns | 3 o'clock: black hexagonal nut (circumradius 28 px, flat face toward the viewer) x 745..775 plus rose-gold ring to x 781.5, axis y 803; 10 o'clock (rotating bezel): same part on the axis 300 deg, outer ring centre (446.5, 702.5); the guard of the 3 o'clock crown is part of the silhouette (notch wall x 745 for rows 775..832) |
| Lugs | integrated; tops y 626, bottoms y 981; strap width 188 px at the lugs (27 mm), tapering to 175 / 156 px at the ends |
| Strap | green rubber, side sections and a centre section between seams x 571.5 / 626.5..627.5 (visible only near the ends), shallow notch at both ends (centre floor y 584 top, 1081 bottom) |
| Hands (about 10:07:38) | hour 303.4 deg, rose-gold bar half width 8 px, tip s 58, white inlay; minute 49.1 deg, bar half width 5.5 px, tip s 90, white inlay; seconds 228.7 deg, thin needle, lollipop centre s 50.3 (r 6.4), tip s 90 |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | own copy `pipeline/steps/watch_audemars_offshorediver42.py` of the Breitling Superocean rubber step: octagon bezel ring (rays) with chamfer, eight screws, generic hexagonal crowns |
| Prep | `pipeline/audemars_offshorediver42_prep.py` (copy of the Breitling prep: 1200 x 1626 PNG source, flat anchor, octagon / opening / crowns in the measure file, crown rows replaced by lines) |
| Comparison frame | 1280 px square, camera 13.8286 px/mm centred on the pivot (2x photo pivot (1196.4, 1593.2) at (640, 640)), `config/presets/watch_kit_white_front_audemars_offshorediver42.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.audemars_offshorediver42_prep   # -> 2x reference, config/watches/audemars-offshorediver42-15720st-green-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
