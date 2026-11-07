# Reference plan: AUDEMARS PIGUET Royal Oak Chronograph 41 26240ST (41 mm steel, white Grande Tapisserie dial, steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Second Audemars Piguet model: it sets the Royal Oak Chronograph approach (octagon-bezel structure of the [Offshore Diver build](../audemars-royal-oak-offshore-diver-15720st-green/REFERENCE_PLAN.md) with the chronograph parts and bracelet columns of the [Moonwatch](../omega-speedmaster-moonwatch-professional-31030425001001/baseline/BASELINE.md) build). The green variant (catalog row 93, same SKU) follows this template.

## Target asset

Front relief GLB `models/watches/audemars-26240st-white.glb` (tracker rule: lowercase brand-SKU; the SKU repeats for the green watch, so the variant is appended), flat back, 2.5D depth, flat bracelet links.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright render, transparent background, 400 x 542 PNG | `audemars-26240st-white_original.png` | HAVE, what the catalog link returns (kept untouched) |
| 2 | Same asset, larger rendition (`&wid=1200&hei=1626`), 1200 x 1626 PNG, the watch is 318 x 507 px | `audemars-26240st-white_1200x1626.png` | HAVE, the working source for measuring and for the maps |
| 3 | Side / back / crown close-up | none | not available; heights are estimates (real case thickness about 11 mm), back flat |

## Measured on this photo (continuous px of the 1200 x 1626 frame; 6.9268 px/mm)

| Item | Result |
| --- | --- |
| Alpha bbox | x 456..773, y 577..1083 (bracelet ends at the top y 577.6 and the bottom y 1083; crown to x 773) |
| Anchor | 41 mm = distance between the outer edges of the polished left / right bezel flats (457.5 / 741.5 px; top / bottom flats 651.5 / 936.0 give the same 284 px) |
| Pivot | hub centre (599.4, 792.9) from a rotational-symmetry search of the hub; opening circle centre (599.9, 792.3) r 110.4, screws centred (600.0, 792.1), octagon centre (599.5, 793.75) |
| Bezel | regular octagon, polished chamfer band all round (about 8 px wide), eight slotted hexagonal screws (outline circumradius 7.5 px) on the vertex rays at 125.3 px; no rotating ring |
| Dial | white Grande Tapisserie plate out to r 96, chapter ring (minute track) to the bezel; three sub-dials (3 / 9 / 6 positions: 12-hour counter right, 30-minute counter left, running seconds bottom, their hands stay photo), date window at 4, applied batons: all photo map |
| Crown / pushers | crown hexagonal barrel R 22 px x 743..768 plus cap to 773 on the axis y 798; pushers at 63 / 117 degrees: hexagonal nut R 18.2 px plus a cylindrical cap r 10.5 px (caps sit 3.4 px off the nut axes) |
| Hands | hour 304.0 deg (60.5 px, half width 3.0, centre line 2.0 px off the pivot axis), minute 50.3 deg (95.6 px, half width 2.7 / 3.05), chrono seconds needle: tail only visible, 99.4 px at 227.3 deg |
| Bracelet | full-width links, tapering from 27 mm at the lugs; dark joint gaps top y 602..606 / 623..627, bottom 978..984, 1008..1014, 1038..1044, 1064..1068; polished pins across the gaps (photo texture); lug tops y 626.7, bottoms 978.2 |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | own copy `pipeline/steps/watch_audemars_royaloakchrono41.py` of the Offshore Diver step: hand offset, off-axis crown caps, chain-of-links bracelet with steel_photo backing |
| Prep | `pipeline/audemars_royaloakchrono41_prep.py` (anchor on the bezel width, hand offsets, crown cap shifts, three crown_replace lines) |
| Comparison frame | 1280 px square, camera 13.8536 px/mm centred on the pivot (2x photo pivot (1198.8, 1585.8) at (640, 640)), `config/presets/watch_kit_white_front_audemars_royaloakchrono41.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.audemars_royaloakchrono41_prep   # -> 2x reference, config/watches/audemars-royaloakchrono41-26240st-white-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
