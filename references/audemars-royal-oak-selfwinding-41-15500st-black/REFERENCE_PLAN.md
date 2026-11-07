# Reference plan: AUDEMARS PIGUET Royal Oak Selfwinding 41 15500ST (41 mm steel, black Grande Tapisserie dial, steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Second Audemars Piguet model: it sets the Royal Oak 41 approach (structure of the [Offshore Diver build](../audemars-royal-oak-offshore-diver-15720st-green/REFERENCE_PLAN.md), with an integrated steel bracelet). The white (catalog row 84) and grey (row 85) variants follow this template; catalog row 88 (SKU 15510ST, "Steel, black") has the very same photo (`standup-1060`), so this build also serves it under its own name.

## Target asset

Front relief GLB `models/watches/audemars-15500st-black.glb` (tracker rule: lowercase brand-SKU; the SKU repeats for the white and grey watches, so the variant is appended), flat back, 2.5D depth.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright render, transparent background (soft alpha rim), 400 x 542 PNG | `audemars-15500st-black_original.png` | HAVE, what the catalog link returns (kept untouched) |
| 2 | Same asset, larger rendition (`&wid=1200&hei=1626`), 1200 x 1626 PNG, the watch is 310 x 506 px | `audemars-15500st-black_1200x1626.png` | HAVE, the working source for measuring and for the maps |
| 3 | Side / back / crown close-up | none | not available; heights are estimates (real case thickness 10.4 mm), back flat |

## Measured on this photo (continuous px of the 1200 x 1626 frame)

| Item | Result |
| --- | --- |
| Alpha bbox | x 456..765.8, y 578..1083 (bracelet ends at the top y 578 and the bottom y 1083, crown to x 765.8) |
| Anchor | the left flat of the octagonal case (median alpha edge over rows 786..803) is 20.5 mm (half of the listed 41 mm width) from the pivot: 7.0141 px/mm |
| Pivot | (600.0, 792.5): the seconds needle passes it to 0.1 px, the hour hand to 0.2 px, the minute hand (incl. its dark facet) to 0.1 px; hub radius about 7.6 px; everything higher sits 1.5..2.5 px higher (camera tilt): opening circle (599.8, 790.0) r 109.8, screws mean y 791 |
| Bezel | octagon (flats left 456.2 / right 743.4 / top 650.0 / bottom 942.5, stretched by the photo tilt), thin brushed face with a polished chamfer along each flat, eight slotted screw heads (outline radius 7.5 px) on the vertex rays at 126 px from (600, 791) |
| Dial | black Grande Tapisserie plate out to r 108 (flat; the waffle is texture only), applied baton indices, AP logo, "SWISS MADE", date window at 3 and the minute track: all in the photo map |
| Crown | 3 o'clock, no guards: hexagonal steel cap x 743.0..765.8, rows 776.5..821 (circumradius 22.3 px), axis y 798.7, flat face toward the viewer |
| Bracelet | integrated, tapering from 285 px at the case to about 127 px at the top end; dark seams (rows) top [600,604) [623,628), bottom [975,982) [1010,1016) [1040,1045) [1063,1066); two polished pin-link bars at x 545..570 / 631..657 (top near the case) narrowing to 557..573 / 626..642 at the bottom end |
| Hands (about 10:07:38) | hour 303.8 deg, half width 3.6 px, tip s 62.5; minute 49.9 deg, half width 4.15 px, chamfered tip s 95.7; seconds 227.3 deg, needle half width 0.7 px, tip s 100.8 |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | own copy `pipeline/steps/watch_audemars_royaloak41.py` of the Offshore Diver step: octagon bezel by rays, eight screws, flat dial lathe, generic hexagonal crown, integrated bracelet from `trace.bracelet` (links between measured seams in three columns plus two continuous pin-link bars) |
| Prep | `pipeline/audemars_royaloak41_prep.py` (copy of the Offshore Diver prep with the bracelet seams / bars, one crown) |
| Comparison frame | 1280 px square, camera 14.0282 px/mm centred on the pivot (2x photo pivot (1200.0, 1585.0) at (640, 640)), `config/presets/watch_kit_white_front_audemars_royaloak41.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.audemars_royaloak41_prep   # -> 2x reference, config/watches/audemars-royaloak41-15500st-black-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
