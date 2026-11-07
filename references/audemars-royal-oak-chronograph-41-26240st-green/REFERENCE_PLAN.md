# Reference plan: AUDEMARS PIGUET Royal Oak Chronograph 41 26240ST (41 mm steel, green Grande Tapisserie dial, steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2, row 93 (see `sources.md`). Follower of the white variant, which set the Royal Oak Chronograph template: the step, prep and kit preset are reused unchanged; only the measure / spec / job JSON are new. Template origin: the approach (octagon-bezel structure of the [Offshore Diver build](../audemars-royal-oak-offshore-diver-15720st-green/REFERENCE_PLAN.md) with the chronograph parts and bracelet columns of the [Moonwatch](../omega-speedmaster-moonwatch-professional-31030425001001/baseline/BASELINE.md) build). This is the green variant (catalog row 93, same SKU 26240ST as the white row 91).

## Target asset

Front relief GLB `models/watches/audemars-26240st-green.glb` (tracker rule: lowercase brand-SKU; the SKU repeats for the white watch, so the variant is appended), flat back, 2.5D depth, flat bracelet links.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright render, transparent background, 400 x 542 PNG | `audemars-26240st-green_original.png` | HAVE, what the catalog link returns (kept untouched) |
| 2 | Same asset, larger rendition (`&wid=1200&hei=1626`), 1200 x 1626 PNG, the watch is 317 x 506 px | `audemars-26240st-green_1200x1626.png` | HAVE, the working source for measuring and for the maps |
| 3 | Side / back / crown close-up | none | not available; heights are estimates (real case thickness about 11 mm), back flat |

## Measured on this photo (continuous px of the 1200 x 1626 frame; 6.9268 px/mm, shared with the white photo)

Registration against the white photo (same camera template): silhouette identical within 0.2 px (left side 0.3 px wider), octagon flats within 0.15 px (left 457.5, right 741.4, top 651.5, bottom 936.15), bracelet joint rows within 0.3 px, crown and pushers identical. Dial-side content is shifted by (-0.22, +0.21) px (screw heads, hub symmetry search), and the bezel opening is larger than the white one.

| Item | Result |
| --- | --- |
| Alpha bbox | x 456..772, y 578..1083 |
| Anchor | 41 mm = outer edges of the polished left / right bezel flats (457.5 / 741.5 px, kept from the white photo, right edge measured 741.4: scale stays 6.9268) |
| Pivot | (599.2, 793.1) = white pivot + the measured shift (-0.2, +0.2); checked by overlay (hub and hands coincide with the render) |
| Opening circle | centre (599.53, 792.30), r 112.38 (rising edge shadow line -> polished chamfer, rms 0.22 px, 348 of 360 scans); the same code gives (599.89, 792.28, 110.46) on the white photo |
| Screws | white positions + (-0.22, +0.21), outline radius 7.5 px |
| Dial | green Grande Tapisserie plate, chapter ring, three darker green sub-dials (all photo map), date window at 4, applied steel batons; hands photographed in the map |
| Hands | same shape and angles as the white photo: hour 304.0 deg, minute 50.3 deg, chrono-seconds tail 227.3 deg (checked on the overlay) |
| Bracelet / crown / pushers | as the white photo (same joint rows, same silhouette) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | shared Royal Oak Chronograph step `pipeline/steps/watch_audemars_royaloakchrono41.py` (read-only): hand offset, off-axis crown caps, chain-of-links bracelet with steel_photo backing |
| Prep | shared `pipeline/audemars_royaloakchrono41_prep.py` with the variant key (anchor on the bezel width, hand offsets, crown cap shifts, three crown_replace lines) |
| Comparison frame | 1280 px square, camera 13.8536 px/mm centred on the pivot (2x photo pivot (1198.4, 1586.2) at (640, 640)), `config/presets/watch_kit_white_front_audemars_royaloakchrono41.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.audemars_royaloakchrono41_prep 26240st-green   # -> 2x reference, config/watches/audemars-royaloakchrono41-26240st-green-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
