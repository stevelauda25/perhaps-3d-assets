# Reference plan: ROLEX GMT-Master II 126710BLRO (40 mm steel, black dial, blue and red Cerachrom 24 h bezel "Pepsi", date with Cyclops lens, GMT hand, Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). FOLLOWER of the GMT-Master II 40 template built for the 126710BLNR (`../rolex-gmt-master-ii-126710blnr/baseline/BASELINE.md`): step, prep and kit preset are reused read-only by key.

## Target asset

Front relief GLB `models/watches/rolex-126710blro.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs and crown guards, 24 h ceramic bezel insert, polished rim, 60-flute coin-edge ring, crystal, dial plate, Cyclops lens above the crystal, four hands at different heights, hub, fluted crown, Oyster bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 1017 x 1832 px incl. the crown | `rolex-126710blro_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the template, back flat |

## Measured on this photo (continuous px of the native 1920 x 2857 frame)

| Item | Result |
| --- | --- |
| Registration | identical to the 126710BLNR photo: left tip x 497 / right (crown) 1512 at the pivot row, lug rows 906 / 1989 at x 700, crown rows 1376..1497 at x 1500; alpha mask difference > 60/255 only on the bracelet columns (Jubilee vs Oyster) and 367 px elsewhere in the head (edge noise); scale 23.14 px/mm, pivot (960, 1424) |
| Dial | black dial, same layout as the 126710BLNR (round lume indices, bar at 9, long bar at 6, triangle at 12, GMT-MASTER II, SUPERLATIVE CHRONOMETER, date window with Cyclops at 3); the difference image of the two photos inside r < 330 px shows only the GMT hand |
| Bezel | 24 h scale: upper half blue, lower half red, a lighter (faceted) wedge at the 10 o'clock end of the blue half and at the 8 / 6 o'clock end of the red half, numerals, dots, lume triangle at 12; ring radii identical to the 126710BLNR |
| Hands (about 10:09:30) | hour 305.5 deg, minute 63.55 deg, seconds 186.4 deg: pixel-identical to the 126710BLNR photo. GMT hand: RED shaft (principal axis 152.907 deg, 0.4 mm, passes 1.16 px from the hub screw centre; the 126710BLNR blue shaft: 152.909 deg, 1.20 px) with the same triangular lume head (overlay of the existing polygons on 8x crops of both photos: vertices follow the head within 0.5 px) |
| Crown / case | identical to the 126710BLNR |
| Bracelet | OYSTER, three columns: outer brushed links (nested rounded ends: top step y 759.5; bottom steps 2181 / 2367 / 2483) and a wide polished centre link (top joints 880 / 735.5; bottom 2004 / 2222 / 2392 / 2505); column lines x 860.5 / 1058.5 (top), 859.5 / 1059.5 (bottom); ends y 683 (centre), 685 (outer), 2514 |

## Decisions

| Decision | Answer |
| --- | --- |
| Step / prep / kit preset | `pipeline/steps/watch_rolex_gmtmaster40.py`, `pipeline/rolex_gmtmaster40_prep.py <key>`, `config/watches/../presets/watch_kit_white_front_rolex_gmtmaster40.json`, all read-only |
| Own files | `config/watches/rolex-gmtmaster40-126710blro{,-measure,-trace}.json`, `jobs/rolex-gmtmaster40-126710blro.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_gmtmaster40_prep 126710blro   # -> config/watches/rolex-gmtmaster40-126710blro-trace.json, outputs/watches/rolex-gmtmaster40-126710blro/{dial_photo,steel_photo}.jpg
```
