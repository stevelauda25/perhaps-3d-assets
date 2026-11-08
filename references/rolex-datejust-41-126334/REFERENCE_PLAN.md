# Reference plan: ROLEX Datejust 41 126334 (41 mm steel, white-gold fluted bezel, mint green dial, Cyclops date, Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). NEW MODEL: this is the Datejust 41 template (126331 Everose Rolesor / Jubilee slate Roman and 126333 Rolesor yellow / Jubilee slate follow it).

## Target asset

Front relief GLB `models/watches/rolex-126334.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs, polished flange, chamfer and 74 real flutes of the white-gold bezel, crystal, dial plate, Cyclops lens, three hands at different heights, hub, fluted crown, Oyster bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 969 x 1855 px incl. the crown | `rolex-126334_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the Rolex Submariner 41 / Tudor templates, back flat |

## Measured on this photo (continuous px of the native 1920 x 2857 frame)

| Item | Result |
| --- | --- |
| Anchor | the widest part of the head at the pivot row is the 41 mm case flank: left edge x 504.6, case centre x 960.0 -> 910.8 px, 22.215 px/mm; cross-checks: bracelet at the lugs 466 px = 20.98 mm, lug to lug rows 905..1980 = 48.4 mm, crown diameter 6.3 mm |
| Pivot | hub screw (960, 1424); dial / rehaut circle centred (959.7, 1426.9), bezel circle (959.9, 1423.1) |
| Rings (radius, px / mm) | dial edge 341.5 (15.37), rehaut / flange line 354.9 (15.98), flange outer 379.5 (17.08), flute zig-zag inner 386.7..390.7 (17.41..17.59), outer 442.1..445.7 (19.90..20.06), case flank 455.4 (20.5) |
| Bezel | polished flange, grey chamfer, 74 flutes = 148 flat facets of 2.432 deg (bright / dark pairs), alternate boundaries reach further in and out (zig-zag), the flank of the case shows as a grey band outside the flutes |
| Dial | mint green sunburst: applied baton indices (12, 6 double bars; 3 replaced by the date window), ROLEX coronet, ROLEX / OYSTER PERPETUAL / DATEJUST, SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE, minute track with 5-minute numerals engraved on the rehaut |
| Cyclops | barrel-shaped lens about 7.6 x 5.9 mm over the date window (centre 1192.5, 1421.5), bright rim, the date numeral 28 magnified |
| Hands (about 10:09:30) | hour 305.5 deg (tip 8.7 mm, broad baton with black facet), minute 63.55 deg (13.5 mm), seconds 186.3 deg (14.3 mm needle, counterweight tail 4.7 mm); outlines traced by the prep |
| Crown | fluted, no guards: axis y 1435.5, radius 69.5 px (3.1 mm), x 1409..1474 |
| Bracelet | Oyster, three columns (outer / centre / outer), column lines x 859.5 / 1059; outer joints top 752.5, bottom 2182 / 2369 / 2488; centre top 867 / 726, bottom 2030 / 2240 / 2406 / 2503; ends y 672 / 2527 |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | new `pipeline/steps/watch_rolex_datejust41.py` (copy of the Submariner 41 step: flute facets instead of the coin edge / insert, Cyclops lens, mirrored crown rows, spec-driven columns so a Jubilee only needs another column list) |
| Prep | new `pipeline/rolex_datejust41_prep.py` (native working size, texture cap 2048, scale from the case flank, traced hand outlines with a colour test for the coloured dial, lens outline) |
| Comparison frame | 1280 px square at half the native scale (11.1073 px/mm) centred on the pivot, `config/presets/watch_kit_white_front_rolex_datejust41.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_datejust41_prep 126334   # -> config/watches/rolex-datejust41-126334-trace.json, outputs/watches/rolex-datejust41-126334/{dial_photo,steel_photo}.jpg
```
