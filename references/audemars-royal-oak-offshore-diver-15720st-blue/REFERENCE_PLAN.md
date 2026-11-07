# Reference plan: AUDEMARS PIGUET Royal Oak Offshore Diver 15720ST (42 mm steel, blue waffle dial, blue rubber strap)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 row 78 (see `sources.md`). FOLLOWER of the Offshore Diver template built for the [green variant](../audemars-royal-oak-offshore-diver-15720st-green/REFERENCE_PLAN.md) (same SKU 15720ST, catalog row 77): same step, prep and kit preset, only the per-photo values were re-measured.

## Target asset

Front relief GLB `models/watches/audemars-15720st-blue.glb` (tracker rule: lowercase brand-SKU; the SKU repeats for the green watch, so the variant is appended), flat back, 2.5D depth, flat front-matched rubber strap.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright render, transparent background (soft alpha rim), 400 x 542 PNG | `audemars-15720st-blue_original.png` | HAVE, what the catalog link returns (kept untouched) |
| 2 | Same asset, larger rendition (`&wid=1200&hei=1626`), 1200 x 1626 PNG, the watch is 346 x 507 px | `audemars-15720st-blue_1200x1626.png` | HAVE, the working source for measuring and for the maps |
| 3 | Side / back / crown close-up | none | not available; heights are the green template's (real case thickness 14.1 mm), back flat |

## Measured on this photo (continuous px of the 1200 x 1626 frame)

| Item | Result |
| --- | --- |
| Alpha bbox | x 438..783, y 577..1083 (strap ends at the top y 577 and the bottom y 1083, both with a shallow centre notch, floor y 582.7 top / 1080.5 bottom) |
| Registration to the green render | the case, bezel, screws, crowns, hub and hands of this render are the green ones translated by (+0.88, -0.74) px (ECC translation fits: x +0.76..1.0, y -0.6..-0.96 on 15 patches; hands PCA intersection +1.0 / -0.65): pivot (599.1, 795.88), opening circle centre (599.7, 794.4) r 109.5, screws and octagon the green values + (0.9, -0.72) |
| Anchor | left flat of the octagonal case (silhouette plateau 454.0 over rows 790..830; the green anchor rows 780..815 give 453.4 here only because the quantised edge steps differ) is 21 mm from the pivot: 6.9095 px/mm (green 6.9143) |
| Dial | blue Mega Tapisserie waffle dial, rose-gold applied indices with white lume, AP logo, date window at 3, "300m / 1000ft AUTOMATIC" print; the rotating ring is black with a WHITE (not cream) sector from 12 to about 15 minutes and a black triangle at 12: all in the photo map |
| Crowns | same black hexagonal nuts and rose-gold rings as the green (3 o'clock and 10 o'clock) |
| Hands (about 10:07:38) | the same hands at the same angles: hour 303.3 to 303.6, minute 48.8 to 49.0, seconds 228.7 (see the measure file note) |
| Lugs / strap | differs from the green: the steel-to-rubber boundary (saturation threshold) is at row 618 top / 988.5 bottom (green 623 / 984.3), i.e. the lugs are about 4.3 / 4.8 px longer relative to the pivot: tip rows 621.0 / 985.2 (tip_top 25.25 mm, tip_bottom 27.5 mm); the lug pins are longer (top 604, bottom 1009) |
| Strap | blue rubber, seams x 572.5 / 627.5 (top) and 572.5 / 629.2 (bottom) starting at y 599.5 top / 1021 bottom; strap ends y 577 top / 1083 bottom |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | `pipeline/steps/watch_audemars_offshorediver42.py` (shared, read-only) |
| Prep | `pipeline/audemars_offshorediver42_prep.py 15720st-blue` (shared, read-only) |
| Comparison frame | 1280 px square, camera 13.8286 px/mm centred on the pivot (2x photo pivot (1198.2, 1591.76) at (640, 640)), `config/presets/watch_kit_white_front_audemars_offshorediver42.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.audemars_offshorediver42_prep 15720st-blue   # -> 2x reference, config/watches/audemars-offshorediver42-15720st-blue-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
