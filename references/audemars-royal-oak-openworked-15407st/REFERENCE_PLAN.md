# Reference plan: AUDEMARS PIGUET Royal Oak Double Balance Wheel Openworked 41 15407ST (41 mm steel, skeleton dial, steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`, row 108). Built on the Royal Oak 41 template (see [the 15500ST black plan](../audemars-royal-oak-selfwinding-41-15500st-black/REFERENCE_PLAN.md) and its BASELINE.md): same camera template, octagon bezel, integrated bracelet; the dial is a skeleton (openworked) dial.

## Target asset

Front relief GLB `models/watches/audemars-15407st.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright render, transparent background (soft alpha rim), 400 x 542 PNG | `audemars-15407st_original.png` | HAVE, what the catalog link returns (kept untouched) |
| 2 | Same asset, larger rendition (`&wid=1200&hei=1626`), 1200 x 1626 PNG | `audemars-15407st_1200x1626.png` | HAVE, the working source for measuring and for the maps |
| 3 | Side / back / crown close-up | none | not available; heights are estimates (real case thickness 8.1 mm), back flat |

## Measured on this photo (continuous px of the 1200 x 1626 frame)

| Item | Result |
| --- | --- |
| Alpha bbox | x 457..766, y 578..1083 |
| Anchor | left flat of the octagonal case (median alpha edge over rows 786..803, 457.09) is 20.5 mm from the pivot: 6.9958 px/mm (black dial 7.0141) |
| Pivot | (600.5, 794.0), the polished hub (dark dot); the photographed hour / minute hand lines meet about 2 px left of it, the seconds needle passes it; hub radius about 6.3 px. Opening circle (600.4, 792.3) r 112.6 (the gold flange ring runs out to the polished chamfer), screws mean y 792.8 |
| Bezel | octagon flats left 457.1 / right 743.9 (hidden, left + 41 mm) / top 651.5 / bottom 942.7; brushed face with polished chamfers; eight ROSE-GOLD hexagonal screws (outline radius 7.5 px) on the rays at 125.3..126.9 px from the opening centre |
| Dial | openworked: rose-gold flange ring with the minute track, applied baton indices, AUDEMARS PIGUET print and SWISS MADE, skeleton movement (barrel, train, double balance wheel, bridges, rubies) with see-through cut-outs (alpha below 255 in the photo): all of it flat photo texture, cut-outs composited on white |
| Crown | 3 o'clock, no guards: hexagonal steel cap x 743.0..766.3, rows 777..820 (circumradius 21.8 px), axis y 798.5 |
| Bracelet | integrated; dark seams top [602,606) [625,629), bottom [974,982) [1008,1015) [1038,1043) [1060,1066); two polished pin-link bars (top near the case x 545..572 / 631..657.5, bottom end 560.5..576.5 / 626.5..642.5) |
| Hands | plain polished steel baton hands, no lume: hour 303.4 deg (63.0 px, full width 7.6 px), minute 46.2 deg (95.7 px, about 9 px incl. its dark facet), seconds 225.1 deg (97.4 px, needle half width 0.6 px) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | the shared `pipeline/steps/watch_audemars_royaloak41.py` (read-only, spec driven); only the spec / measure / job are new |
| Prep | `pipeline/audemars_royaloakopenworked41_prep.py` (copy of the Royal Oak 41 prep with the openworked names; the dial map is composited on white because the cut-outs are see-through) |
| Comparison frame | 1280 px square, camera 13.9916 px/mm centred on the pivot (2x photo pivot (1201.0, 1588.0) at (640, 640)), `config/presets/watch_kit_white_front_audemars_royaloakopenworked41.json` |
| Out of scope | an openwork cut-out geometry: the movement is photo texture on a flat plate |

## Phase 1 outputs

```sh
python3 -B -m pipeline.audemars_royaloakopenworked41_prep   # -> 2x reference, config/watches/audemars-royaloakopenworked41-15407st-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
