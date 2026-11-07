# Reference plan: AUDEMARS PIGUET Royal Oak Selfwinding 41 15500ST (41 mm steel, white (silver) Grande Tapisserie dial, steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Follower of the Royal Oak 41 template set by the [black variant](../audemars-royal-oak-selfwinding-41-15500st-black/REFERENCE_PLAN.md) (same step, prep and geometry; catalog row 84). Catalog row 89 (SKU 15510ST, "Steel, white") has the very same photo (`standup-996`), so this build also serves it under its own name (the lead publishes the copy).

## Target asset

Front relief GLB `models/watches/audemars-15500st-white.glb` (tracker rule: lowercase brand-SKU; the SKU repeats for the white and grey watches, so the variant is appended), flat back, 2.5D depth.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright render, transparent background (soft alpha rim), 400 x 542 PNG | `audemars-15500st-white_original.png` | HAVE, what the catalog link returns (kept untouched) |
| 2 | Same asset, larger rendition (`&wid=1200&hei=1626`), 1200 x 1626 PNG, the watch is 310 x 506 px | `audemars-15500st-white_1200x1626.png` | HAVE, the working source for measuring and for the maps |
| 3 | Side / back / crown close-up | none | not available; heights are estimates (real case thickness 10.4 mm), back flat |

## Measured on this photo (continuous px of the 1200 x 1626 frame)

| Item | Result |
| --- | --- |
| Alpha bbox | x 457..764, y 577..1083 (bracelet ends at the top y 577 and the bottom y 1083) |
| Anchor | the left flat of the octagonal case (median alpha edge over rows 786..803) is 20.5 mm (half of the listed 41 mm width) from the pivot: 6.9473 px/mm (this photo is 0.9 % narrower than the black one; vertical scale unchanged within 0.2 %) |
| Pivot | (600.42, 792.45): the black pivot carried through an ECC affine fit of the two photos' steel parts (silhouette-only fit agrees to 0.15 px); the light-on-light hands cannot be thresholded, they and the hub were verified by overlay (phase correlation 0.3 px at 2x); hub radius about 7.6 px; opening circle (600.35, 790.01) r 109.2, screws mapped likewise |
| Bezel | octagon (flats left 458.0 / right 742.7 / top 650.3 / bottom 942.2, stretched by the photo tilt), thin brushed face with a polished chamfer along each flat, eight slotted screw heads (outline radius 7.5 px) on the vertex rays at 126 px from (600, 791) |
| Dial | white Grande Tapisserie plate out to r 107.4 (flat; the waffle is texture only), applied baton indices, AP logo, "SWISS MADE", date window at 3 and the minute track: all in the photo map |
| Crown | 3 o'clock, no guards: hexagonal steel cap base at x 742.3, rows 776.5..821 (circumradius 22.3 px), axis y 798.7, flat face toward the viewer |
| Bracelet | integrated, tapering from 285 px at the case to about 127 px at the top end; dark seams (rows) top [600,604) [623,628), bottom [975,982) [1010,1016) [1040,1045) [1062,1065); two polished pin-link bars at x 546..571 / 631..657 (top near the case) narrowing to 559..575 / 625..641 at the bottom end (black values through the affine, checked by overlay) |
| Hands (about 10:07:38) | hour 303.8 deg, half width 3.6 px, tip s 62.2; minute 49.9 deg, half width 4.15 px, chamfered tip s 95.2; seconds 227.3 deg, needle half width 0.7 px, tip s 100.3 (the black values in this photo's px, verified by tip overlays) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | shared `pipeline/steps/watch_audemars_royaloak41.py` (read-only): octagon bezel by rays, eight screws, flat dial lathe, hexagonal crown, integrated bracelet from `trace.bracelet` |
| Prep | shared `pipeline/audemars_royaloak41_prep.py` (read-only, variant key as argument) |
| Comparison frame | 1280 px square, camera 13.8946 px/mm (= 2 x 6.9473) centred on the pivot (2x photo pivot at (640, 640)), `config/presets/watch_kit_white_front_audemars_royaloak41_white.json` (copy of the black kit with the new scale) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.audemars_royaloak41_prep 15500st-white   # -> 2x reference, config/watches/audemars-royaloak41-15500st-white-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
