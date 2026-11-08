# Reference plan: ROLEX GMT-Master II 126713GRNR (40 mm steel and yellow gold Rolesor, black dial, grey and black Cerachrom 24 h bezel, gold coin edge, date with Cyclops lens, gold GMT hand, Jubilee bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from the Rolex image host row in `rolex_map.json` (see `sources.md`). FOLLOWER of the GMT-Master II 40 template (126710BLNR, `../rolex-gmt-master-ii-126710blnr/baseline/BASELINE.md`): step, prep and kit preset are reused read-only by key; only the per-photo measure / spec / job JSON is new.

## Target asset

Front relief GLB `models/watches/rolex-126713grnr.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs and crown guards, ceramic 24 h insert, polished gold rim, 60-flute gold coin-edge ring, crystal, dial plate, Cyclops lens, four hands at different heights, hub, fluted gold crown, Jubilee links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, watch 1018 x 1831 px incl. the crown | `rolex-126713grnr_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the template, back flat |

## What is per photo (versus 126710BLNR)

| Item | Result |
| --- | --- |
| Registration | same camera: alpha silhouette differs from the 126710BLNR photo in 81 px above 60/255 (crown right edge); pivot (960, 1424), scale 23.14 px/mm, rings, lens, crown rows kept (overlay-checked) |
| Dial | black dial, same layout as 126710BLNR; hour / minute / seconds hands gold with white lume, indices white-lume with gold-coloured frames |
| Bezel | 24 h scale: upper half black, lower half grey (Cerachrom), gold numerals / dots / triangle, gold polished rim, gold coin edge |
| GMT hand | gold shaft (same axis 152.9 deg, 9 px) with gold-framed lume triangle head (same vertices within 1 px) |
| Bracelet | Jubilee, five columns, outer and inner brushed / polished steel, centre links gold; joints per column checked against 126710BLNR by 4x strips |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_gmtmaster40_prep 126713grnr   # -> config/watches/rolex-gmtmaster40-126713grnr-trace.json, outputs/watches/rolex-gmtmaster40-126713grnr/{dial_photo,steel_photo}.jpg
```
