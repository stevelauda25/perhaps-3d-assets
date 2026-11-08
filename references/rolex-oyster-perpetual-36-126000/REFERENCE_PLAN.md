# Reference plan: ROLEX Oyster Perpetual 36 126000 (36 mm steel, lavender dial, Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). ADAPT of the Oyster Perpetual 41 template (`../rolex-oyster-perpetual-41-134300-green/baseline/BASELINE.md`): same step (read-only), new 36 mm measurements.

## Target asset

Front relief GLB `models/watches/rolex-126000.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs, domed polished bezel, crystal, dial plate, three hands at different heights, hub, fluted crown, Oyster bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 876 x 1741 px incl. the crown | `rolex-126000_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the 41 template (back flat) |

## Measured on this photo (continuous px of the native 1920 x 2857 frame)

| Item | Result |
| --- | --- |
| Anchor | the listed 36 mm case = 2 x (case centre x 959.5 - left flank x 549) = 821 px, 22.806 px/mm (the right flank is hidden by the crown); lug to lug 982 px = 43.1 mm; the same camera as the 41 renders, the watch is scaled up 4.6 % (fewer mm, same frame) |
| Pivot | hub screw centre (960, 1424); hub disc radius about 19 px; the dial / bezel circle is centred (959.6, 1428.3), a few px below the hub |
| Rings (radius from the ring centre) | lavender dial 314 px (13.77 mm), crystal / rehaut edge 351 (rehaut with ROLEX text 314..351), bezel inner edge 354.5, bezel outer edge 401.5 px (17.6 mm) |
| Bezel | smooth domed polished bezel (no insert, no numerals): one lathe with the 41's dome profile |
| Dial | flat lavender dial, coronet at 12, applied baton indices (double bars at 3, 9 and 6, single at 1, 2, 4, 5, 7, 8, 10, 11), black square markers at the odd hours, minute track, ROLEX / OYSTER PERPETUAL, SUPERLATIVE CHRONOMETER / OFFICIALLY CERTIFIED, SWISS MADE: all in the native photo map |
| Hands (about 10:09:30) | hour 305.2 deg (flat tip 7.95 mm, tail 2.6), minute 63.2 deg (tip 12.3, tail 2.6, ends at the 2 o'clock index), seconds 186.0 deg (needle to 13.4 mm, counterweight tail 4.2) |
| Crown | fluted, axis y 1435 (0.5 mm below the pivot), radius 68 px (2.98 mm), neck x 1360, flutes to 1407, cap to 1424 |
| Bracelet | Oyster, three columns: outer brushed links (top joint y 811.5; bottom 2108.5, 2292, 2414.5) and a wider centre link (top 770.5, 931; bottom 1957, 2166.5, 2335, 2435.5); ends y 729 / 2469; column lines x 860.5 / 1058.5 |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | `pipeline/steps/watch_rolex_oysterperpetual41.py` reused read-only (spec driven; the 36 mm case fits through the measure / spec values) |
| Prep | new `pipeline/rolex_oysterperpetual36_prep.py` (name-bound copy of the 41 prep; native size, texture cap 2048) |
| Comparison frame | 1280 px square at half the native scale (11.4028 px/mm) centred on the pivot, `config/presets/watch_kit_white_front_rolex_oysterperpetual36.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_oysterperpetual36_prep 126000   # -> config/watches/rolex-oysterperpetual36-126000-trace.json, outputs/watches/rolex-oysterperpetual36-126000/{dial_photo,steel_photo}.jpg
```
