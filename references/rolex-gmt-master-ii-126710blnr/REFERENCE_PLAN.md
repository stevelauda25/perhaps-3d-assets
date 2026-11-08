# Reference plan: ROLEX GMT-Master II 126710BLNR (40 mm steel, black dial, blue and black Cerachrom 24 h bezel, date with Cyclops lens, GMT hand, Jubilee bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). NEW MODEL: the GMT-Master II 40 template, adapted from the Submariner Date 41 build (rotating coin-edge bezel, Cyclops lens, column-driven bracelet), the Tudor Black Bay GMT (the fourth hand as a free polygon) and the Tudor Black Bay 58 (five-column Jubilee-style bracelet spec). 126720VTNR (left crown), 126711CHNR, 126713GRNR and 126710BLRO follow.

## Target asset

Front relief GLB `models/watches/rolex-126710blnr.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs and crown guards, 24 h ceramic bezel insert, polished rim, 60-flute coin-edge ring, crystal, dial plate, Cyclops lens above the crystal, four hands at different heights, hub, fluted crown, Jubilee bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, the watch is 1017 x 1830 px incl. the crown | `rolex-126710blnr_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the Submariner Date template, back flat |

## Measured on this photo (continuous px of the native 1920 x 2857 frame)

| Item | Result |
| --- | --- |
| Registration | scale 23.14 px/mm (40 mm = coin-edge tip diameter: left tip envelope x 496.9, case centre x 959.7), pivot = hub screw (960.4, 1424.0) -> (960, 1424); ring centre (959.6, 1424.0); rings (px): dial 309.3, crystal / flange 351, bezel inner edge 366.4, insert outer 436.05, rim outer 442.9, tips 462.7 |
| Dial | black dial, round lume indices at 1 / 2 / 4 / 5 / 7 / 8 / 10 / 11, bar at 9, long bar at 6, triangle at 12, no index at 3 (date), ROLEX coronet, OYSTER PERPETUAL DATE, GMT-MASTER II, SUPERLATIVE CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE, minute track, rehaut ROLEX engraving |
| Bezel | 24 h scale: upper half black, lower half blue (light blue facet at the 6 o'clock side), numerals 2 / 4 / 6(9) / 8 / 10 / 12 / 14 / 16 / 18 / 20 / 22, dots, lume triangle at 12, polished rim, 60 coarse coin-edge flutes (FFT harmonic 60) |
| Date window / Cyclops | rounded lens (flat top y 1355, bottom y 1487.5, bowed sides, x 1088..1254), white window with "28" inside: texture; as the Submariner Date lens |
| Hands (about 10:09:30) | hour 305.5 deg Mercedes, minute 63.55 deg sword, seconds 186.4 deg with lume ring, GMT 152.9 deg: blue shaft (0.4 mm) with a triangular lume head whose right edge is vertical (x 1094.5), drawn over the 5 o'clock index |
| Crown / case | fluted crown x 1428..1514 (guards to x 1472), axis 0.6 mm below the pivot; lug top y 903.5 (22.5 mm), lug bottom y 1992.5 (24.6 mm) |
| Bracelet | Jubilee, five columns: outer brushed links with nested rounded tops, then inner / centre / inner polished plates; column lines x 860.8 / 926.2 / 992.5 / 1058.4 (top), 860.4 / 926 / 993.5 / 1058.8 (bottom); joints per column in `config/watches/rolex-gmtmaster40-126710blnr.json` (`strap.bracelet.note`); ends y 684.4 (top) and 2514.4 (bottom) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | `pipeline/steps/watch_rolex_gmtmaster40.py` (copy of the Submariner Date step: hands = every name in spec `hands.z`, any bracelet column layout) |
| Prep | `pipeline/rolex_gmtmaster40_prep.py <key>` (copy of the Submariner Date prep plus hand mode `polygons_px` for the GMT hand) |
| Kit preset | `config/presets/watch_kit_white_front_rolex_gmtmaster40.json` (own: 11.57 px/mm; the Submariner preset differs by 1.5 %) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_gmtmaster40_prep 126710blnr   # -> config/watches/rolex-gmtmaster40-126710blnr-trace.json, outputs/watches/rolex-gmtmaster40-126710blnr/{dial_photo,steel_photo}.jpg
```
