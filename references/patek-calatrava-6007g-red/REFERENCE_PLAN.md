# Reference plan: PATEK PHILIPPE Calatrava 6007G red (40 mm white gold, black / red dial, black leather strap with red stitching)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Follower of the **Calatrava 6007G template** built for the blue variant ([baseline](../patek-calatrava-6007g-blue/baseline/BASELINE.md), [plan](../patek-calatrava-6007g-blue/REFERENCE_PLAN.md)).

## Target asset

Front relief GLB `models/watches/patek-6007g-red.glb` (tracker rule: lowercase brand-SKU, variant appended because the SKU repeats), flat back, 2.5D depth, flat front-matched leather strap.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background (faint drop shadow below the strap), 1920 x 2691 PNG | `patek-6007g-red_original.png` | HAVE, the only source (untouched, worked on natively) |
| 2 | Side / back / crown close-up | none | not available; heights are the blue build's estimates, back flat |

## Registration against the blue photo (same camera)

Phase correlation of the dial region red photo vs blue photo: shift 0.003 / 0.005 px; the grey difference image shows only the colour accents (red markers, red seconds hand, red lining, red stitching) and the different leather emboss; the hour and minute hands are pixel-identical; silhouette xor 5,389 px of 2.0 million (strap ends and a few pocket rows). So every geometric value in `config/watches/patek-calatrava6007g-6007g-red-measure.json` equals the blue measure (circle centre (956.50, 1271.23) r 626.35 px = 40 mm, pivot (960.0, 1258.3), rings, hands, crown, lug rows, pocket rows); the seconds hand mask (red here) lies on the same pixels (hub x 931..988 at row 1258, pointer axis 179.3..179.5 deg).

## Decisions

| Decision | Answer |
| --- | --- |
| Step / prep | reused read-only: `pipeline/steps/watch_patek_calatrava6007g.py`, `pipeline/patek_calatrava6007g_prep.py` (variant key `6007g-red`) |
| Kit preset | reused read-only: `config/presets/watch_kit_white_front_patek_calatrava6007g.json` (same scale and pivot) |
| Comparison frame | 2048 px, 23.4881 px/mm = 0.75 x the native photo, pivot at the centre: photo pixel (x, y) at ((x - 960) * 0.75 + 1024, (y - 1258.3) * 0.75 + 1024) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.patek_calatrava6007g_prep 6007g-red   # -> config/watches/patek-calatrava6007g-6007g-red-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
