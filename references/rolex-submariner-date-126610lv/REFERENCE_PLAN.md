# Reference plan: ROLEX Submariner Date 126610LV (41 mm steel, black dial, green Cerachrom bezel, date with Cyclops lens, Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). FOLLOWER of the Submariner Date 126610LN template (`../rolex-submariner-date-126610ln/baseline/BASELINE.md`).

## Target asset

Front relief GLB `models/watches/rolex-126610lv.glb` (tracker rule: lowercase brand + normalized SKU), flat back, layered meshes (case with lugs and crown guards, green ceramic bezel insert, polished rim, fluted coin-edge ring, crystal, dial plate, Cyclops lens, three hands at different heights, hub, fluted crown, Oyster bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG | `rolex-126610lv_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the template, back flat |

## Measured on this photo (native px)

| Item | Result |
| --- | --- |
| Registration | alpha identical to the 126610LN (0 px differ by > 60/255, max 10); inside the mask the dial (r < 300 px, hands, lens, print) is pixel-identical to the 126610LN's (0 % of pixels differ by > 20), the crown too; only the bezel insert differs (67 % of the annulus r 357..441 px), plus 1 % of the rehaut / coin edge pixels and 4-7 % of the bracelet pixels (green reflection / brushed grain). Pivot, scale 22.785 px/mm, rings, hands (305.5 / 63.55 / 186.3 deg), lens outline, bracelet joints therefore taken over from the 126610LN measure; overlay re-check in BASELINE |
| Dial | black Maxi dial, same layout as 126610LN (no 3 o'clock index, OYSTER PERPETUAL DATE, SUBMARINER 1000ft = 300m, date window with Cyclops) |
| Bezel | green Cerachrom insert with the white 60-minute scale and numerals, lume pearl at 12, polished green-to-white reflection sweep across the left half (as the black insert's), polished steel rim, coin edge |

## Decisions

Step `pipeline/steps/watch_rolex_submarinerdate41.py`, prep `pipeline/rolex_submarinerdate41_prep.py 126610lv`, kit preset `config/presets/watch_kit_white_front_rolex_submariner41.json`: all read-only. The tracker variant (green bezel) matches the photo.

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_submarinerdate41_prep 126610lv
```
