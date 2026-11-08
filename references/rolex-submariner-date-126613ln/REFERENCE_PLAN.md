# Reference plan: ROLEX Submariner Date 126613LN (41 mm steel and yellow-gold Rolesor, black dial, black Cerachrom bezel with gold coin edge, date with Cyclops lens, two-tone Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). FOLLOWER of the Submariner Date 41 template built for the 126610LN (`../rolex-submariner-date-126610ln/baseline/BASELINE.md`).

## Target asset

Front relief GLB `models/watches/rolex-126613ln.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes as the 126610LN (case with lugs and crown guards, ceramic bezel insert, polished rim, fluted coin-edge ring, crystal, dial plate, Cyclops lens, three hands at different heights, hub, fluted crown, Oyster bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG | `rolex-126613ln_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the template, back flat |

## Measured on this photo (native px)

| Item | Result |
| --- | --- |
| Registration | same camera as the 126610LN: alpha masks differ by > 60/255 in 1207 px, all 1 px edge pixels (bracelet end rows 671..678 and 2524..2526, crown cap x 1516..1521); pivot (960, 1424), 22.785 px/mm; rings, hands and lens re-verified by overlay |
| Dial | black Maxi dial as the 126610LN with yellow-gold rimmed round indices / bars / triangle and a gold-rimmed Mercedes hour hand; date window and Cyclops at 3 |
| Two-tone parts | yellow-gold coin-edge bezel ring, crown, centre bracelet links (and the gold rims of dial indices and hands): all in the projected photo (`steel_photo.jpg`), no separate material, only the emissions are re-tuned |
| Bracelet | the same joint rows as the 126610LN (3x strip crops top and bottom compared: identical); the gold links are only shaded differently (deep black reflection bands in the gaps, texture only) |

## Decisions

Step, prep and kit preset reused read-only (`watch_rolex_submarinerdate41`, `rolex_submarinerdate41_prep`, `config/presets/watch_kit_white_front_rolex_submariner41.json`); own measure / spec / trace / job `rolex-submarinerdate41-126613ln`.

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_submarinerdate41_prep 126613ln
```
