# Reference plan: TUDOR Black Bay 58 Burgundy M7939A1A0RU-0001 (39 mm steel, burgundy dial and bezel insert, five-link steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). FOLLOWER of the Black Bay 58 template built for the black [M7939A1A0NU-0001](../tudor-black-bay-58-m7939a1a0nu-0001/REFERENCE_PLAN.md): same case, bracelet, crop and pose; the burgundy dial, burgundy bezel insert and silver-white hands (the black version has gold hands) come with the photo maps.

## Target asset

Front relief GLB `models/watches/tudor-m7939a1a0ru-0001.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background with drop shadow and a corner logo, 900 x 1200 | `tudor-m7939a1a0ru-0001_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Black Bay 58 / 54 builds, back flat |

## Registration against the black photo

Largest alpha component bbox identical (x 180..754, y 141..1123); silhouette differs from the black photo's by 193 px of 377k; lug tops 303 / bottoms 944, same rows. Pivot (451, 613), scale 13.8718 px/mm, rings, crown, bracelet joints and the 10:10:38 pose are taken from the template; checked by overlay (see BASELINE.md).

## Decisions

| Decision | Answer |
| --- | --- |
| Hands, bezel numerals, dial print | as in the template: hands carry the front-projected photo, print and numerals are texture only |
| Dial / steel / hands emission | re-tuned from region means on this photo |
| Comparison frame | 2048 px square, kit preset `config/presets/watch_kit_white_front_tudor_bb58.json` (2x photo pivot (902, 1226) at (1024, 1024), offset (+122, -202)) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_bb58_prep m7939a1a0ru-0001
```
