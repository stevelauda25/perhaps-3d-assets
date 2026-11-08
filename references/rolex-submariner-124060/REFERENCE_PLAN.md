# Reference plan: ROLEX Submariner 124060 (41 mm steel, black dial, black Cerachrom bezel, Oyster bracelet, no date)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). NEW MODEL: this is the Submariner 41 template (the Submariner Date 126610LN / 126610LV / 126613LB / 126613LN and the Sea-Dweller 126600 / Deepsea 136660 follow it).

## Target asset

Front relief GLB `models/watches/rolex-124060.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs and crown guards, ceramic bezel insert, polished rim, fluted coin-edge ring, crystal, dial plate, three hands at different heights, hub, fluted crown, Oyster bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 1028 x 1855 px incl. the crown | `rolex-124060_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the Tudor Black Bay 58 / Omega diver templates, back flat |

## Measured on this photo (continuous px of the native 1920 x 2857 frame)

| Item | Result |
| --- | --- |
| Anchor | the widest part of the head is the coin-edge bezel: tip envelope left x 492.6, centre x 959.7 -> 41 mm = 934.2 px, 22.785 px/mm; cross-checks: lug to lug rows 900..1988 = 47.8 mm, bracelet at the lugs 20.6 mm, crown 7.0 mm |
| Pivot | hub screw centre (960.3, 1424.4) -> (960, 1424); dial / bezel circles centred (959.7, 1423.7) |
| Rings (radius from the ring centre) | dial edge 309 px (13.56 mm), flange / crystal edge 353.7 (15.52), insert inner 357 (15.67), insert outer 441.2 (19.36), polished rim outer 449.3 (19.72), flute tips 467.1 (20.5) |
| Bezel | black ceramic insert (60-minute scale, numerals 10 / 20 / 30 / 40 / 50, lume pearl at 12, all baked with the ceramic's white reflection in the photo), 120-flute coin edge, flutes about 4 px deep |
| Dial | black Maxi dial: Mercedes-ring hour hand, round indices at 1 / 2 / 4 / 5 / 7 / 8 (lume discs), bars at 3 / 9, long bar at 6, triangle at 12, ROLEX coronet, OYSTER PERPETUAL, SUBMARINER 1000ft = 300m, SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE, minute track, rehaut with the ROLEX engraving |
| Hands (about 10:09:30) | hour 305.5 deg Mercedes (tip 8.1 mm), minute 63.55 deg (12.7 mm), seconds 186.3 deg (13.5 mm, tail dot at 4.5 mm, lume ring at 7.5 mm); outlines traced by the prep |
| Crown | fluted with guards: axis y 1436, radius 80 px (3.5 mm), flutes x 1426..1498, cap to 1520; guard edge x 1466 |
| Bracelet | Oyster, three columns (outer / centre / outer), column lines x 859 / 1061; outer joints top 756.7, bottom 2181 / 2366 / 2485; centre top 864 / 721, bottom 2028 / 2240 / 2409 / 2502; ends y 675 / 2525; the bracelet tapers from 20.6 mm at the lugs |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | new `pipeline/steps/watch_rolex_submariner41.py` (copy of the Oyster Perpetual 41 step: ceramic insert + rim + fluted coin ring instead of the domed bezel, traced hand outlines, spec-driven three-column Oyster bracelet) |
| Prep | new `pipeline/rolex_submariner41_prep.py` (native working size, texture cap 2048, scale from the bezel tips, traced hand outlines) |
| Comparison frame | 1280 px square at half the native scale (11.3927 px/mm) centred on the pivot (half-size photo pivot (480, 712) at (640, 640)), `config/presets/watch_kit_white_front_rolex_submariner41.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_submariner41_prep 124060   # -> config/watches/rolex-submariner41-124060-trace.json, outputs/watches/rolex-submariner41-124060/{dial_photo,steel_photo}.jpg
```
