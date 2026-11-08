# Reference plan: ROLEX GMT-Master II 126711CHNR (40 mm steel and Everose gold Rolesor, black dial, brown and black Cerachrom 24 h bezel with Everose coin edge, date with Cyclops lens, Everose GMT hand, Oyster bracelet)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from the Rolex image host row in `rolex_map.json` (see `sources.md`). FOLLOWER of the GMT-Master II 40 template (126710BLNR, `../rolex-gmt-master-ii-126710blnr/baseline/BASELINE.md`) and of the two-tone 126713GRNR and the Oyster 126710BLRO: step, prep and kit preset are reused read-only by key; only the per-photo measure / spec / job JSON is new.

## Target asset

Front relief GLB `models/watches/rolex-126711chnr.glb` (tracker rule: lowercase brand + normalized SKU), flat back, 2.5D depth, layered meshes (case with lugs and crown guards, ceramic 24 h insert, polished Everose rim, 60-flute Everose coin-edge ring, crystal, dial plate, Cyclops lens, four hands at different heights, hub, fluted Everose crown, Oyster links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG, watch 1017 x 1832 px incl. the crown | `rolex-126711chnr_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights follow the template, back flat |

## What is per photo (versus the siblings)

| Item | Result |
| --- | --- |
| Registration | same camera: alpha silhouette differs from the 126710BLRO photo in 330 px above 60/255 (edge noise and bracelet colour edges); pivot (960, 1424), scale 23.14 px/mm, rings, lens, crown rows kept (overlay-checked) |
| Dial | black dial, same layout; hour / minute / seconds hands Everose with white lume, indices white-lume with Everose frames, GMT-MASTER II print Everose |
| Bezel | 24 h scale: upper half black, lower half brown (Cerachrom), Everose numerals / dots / triangle, Everose polished rim and coin edge |
| GMT hand | Everose shaft (same axis 152.9 deg) with Everose-framed lume triangle head; polygons as 126713GRNR (overlay-checked) |
| Bracelet | Oyster, three columns: brushed steel outer links, polished Everose centre link; joint rows identical to 126710BLRO (profile cross-correlation, shift 0 px) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_gmtmaster40_prep 126711chnr   # -> config/watches/rolex-gmtmaster40-126711chnr-trace.json, outputs/watches/rolex-gmtmaster40-126711chnr/{dial_photo,steel_photo}.jpg
```
