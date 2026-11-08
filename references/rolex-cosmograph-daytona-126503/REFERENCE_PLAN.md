# Reference plan: ROLEX Cosmograph Daytona 126503 (40 mm Rolesor, champagne dial, yellow gold tachymetre bezel, three sub-dials, two screw-down pushers, Oyster bracelet with gold centre links)

Written 2026-11-08 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from Catalog 2 (see `sources.md`). FOLLOWER of the Daytona 40 template (`../rolex-cosmograph-daytona-126500ln/baseline/BASELINE.md`, "Template for the next Daytona variants"): step, prep and kit preset are used read-only by key.

## Target asset

Front relief GLB `models/watches/rolex-126503.glb`, flat back, 2.5D depth, layered meshes (case slab with horns, crown guards and pusher barrels from the photo contour, gold bezel ring with chamfer and edge, crystal, dial plate, six flat hands + hub and sub-dial screws, fluted crown, two screw-down pushers, Oyster bracelet links and backing).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2857 RGBA PNG | `rolex-126503_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back | none | not available; heights follow the Daytona template, back flat |

## Measured on this photo

Same camera as the 126500LN render (check: alpha silhouette difference mean 0.014 / 255, leftmost case edge row 511, horns, bracelet ends 682 / 2513): scale 22.4625 px/mm, pivot (960, 1425), kit preset unchanged. Time is the same 10:09:55 with the chronograph running (hour 305, minute 62.5, chronograph seconds 323.8 deg; re-verified by overlay, see BASELINE.md). Dial: CHAMPAGNE sunray, applied gold baton indices, three black-ringed champagne sub-dials, red DAYTONA. Bezel: yellow gold with the black tachymetre scale (no ceramic). Crown, pushers: yellow gold. Bracelet: Oyster, brushed steel outer links, polished yellow gold centre links; joints per column checked against the 126500LN rows.

## Decisions

Step `pipeline/steps/watch_rolex_daytona40.py`, prep `pipeline/rolex_daytona40_prep.py`, kit preset `config/presets/watch_kit_white_front_rolex_daytona40.json`, all read-only. Own `config/watches/rolex-daytona40-126503{,-measure,-trace}.json` and `jobs/rolex-daytona40-126503.json`. Gold parts need no separate material (photo projection).

## Phase 1 outputs

```sh
python3 -B -m pipeline.rolex_daytona40_prep 126503   # -> config/watches/rolex-daytona40-126503-trace.json, outputs/watches/rolex-daytona40-126503/{dial_photo,steel_photo}.jpg
```
