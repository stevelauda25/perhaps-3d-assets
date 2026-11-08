# Reference plan: ROLEX Oyster Perpetual 41 134300 (41 mm steel, pistachio dial, Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). FOLLOWER: reuses the Oyster Perpetual 41 template (step, prep, kit preset, geometry).

## Target asset

Front relief GLB `models/watches/rolex-134300-pistachio.glb` (tracker rule: lowercase brand + normalized SKU + variant), flat back, 2.5D depth, layered meshes (case with lugs, domed polished bezel, crystal, dial plate, three hands at different heights, hub, fluted crown, Oyster bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 965 x 1853 px incl. the crown | `rolex-134300-pistachio_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the Tudor Black Bay 58 template (case thickness about 8 mm real), back flat |

## Measured on this photo (continuous px of the native 1920 x 2857 frame)

| Item | Result |
| --- | --- |
| Anchor | the listed 41 mm case = 2 x (case centre x 959 - left flank x 512) = 894 px, 21.805 px/mm (the right flank is hidden by the crown; the centre is the mean of left / right flanks at rows 1300, 1340, 1570); lug to lug 1052 px = 48.2 mm |
| Pivot | hub screw centre (961, 1424); hub disc radius 21 px; the dial / bezel circle is centred (959.4, 1429), a few px left of and below the hub (camera view from slightly right / above) |
| Rings (radius from the ring centre) | pistachio dial 348 px (15.96 mm), bright crystal / rehaut edge 391, bezel inner edge 394 (a thin black gap line to 402), bezel outer edge 442 px (20.27 mm) |
| Bezel | smooth domed polished bezel (no insert, no numerals, no coin edge): one lathe with a dome profile |
| Dial | flat pistachio dial, ROLEX coronet at 12, applied round-ended baton indices (double bars at 3 and 9 and 6, single at the others), minute track of short bars with a dot every 5, two text lines at 6, SWISS MADE: all in the native photo map |
| Hands (about 10:09:30) | hour 305.53 deg (round-ended baton, flat tip 9.65 mm, tail 2.95 mm, half width 0.77 -> 0.58), minute 63.55 deg (tip 14.85 mm, tail 2.85, half width 0.70 -> 0.52, crosses the 2 o'clock index), seconds 186.3 deg (needle to 15.1 mm, counterweight tail 4.05 mm, half width 0.42 -> 0.12) |
| Crown | fluted, axis y 1435 (0.5 mm below the pivot), radius 78 px (3.58 mm), base x 1399, flutes to 1455, cap to 1477 |
| Bracelet | Oyster, three columns: outer brushed links (top joints y 759.5, 923; bottom 1987, 2171, 2363, 2500) and a wider centre link (top 727, 868.5; bottom 2025.5, 2236, 2410, 2507); ends y 673 / 2526; the bracelet tapers (21.6 mm at the lugs to 16.5 mm at the end) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | new `pipeline/steps/watch_rolex_oysterperpetual41.py` (copy of the Black Bay 58 step: domed bezel lathe from a spec profile, no insert, three-column bracelet, no lume geometry) |
| Prep | new `pipeline/rolex_oysterperpetual41_prep.py` (native working size, texture cap 2048, scale from the mirrored case flank) |
| Comparison frame | 1280 px square at half the native scale (10.9024 px/mm) centred on the pivot (half-size photo pivot (480.5, 712.0) at (640, 640)), `config/presets/watch_kit_white_front_rolex_oysterperpetual41.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_oysterperpetual41_prep 134300-pistachio   # -> config/watches/rolex-oysterperpetual41-134300-pistachio-trace.json, outputs/watches/rolex-oysterperpetual41-134300-pistachio/{dial_photo,steel_photo}.jpg
```
