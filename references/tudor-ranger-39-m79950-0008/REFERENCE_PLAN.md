# Reference plan: TUDOR Ranger M79950-0008 (39 mm steel, beige dial with black Arabic numerals, steel three-column bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Built from the **Ranger 39 template** of [M79950-0001](../tudor-ranger-39-m79950-0001/REFERENCE_PLAN.md): same case, bezel, crown, bracelet, camera and pose; different dial and hands.

## Target asset

Front relief GLB `models/watches/tudor-m79950-0008.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background with drop shadow, 900 x 1200 | `tudor-m79950-0008_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Royal / -0001 builds, back flat |

## Measured on this photo (px of the 900 x 1200 frame, pivot = hub hole)

| Item | Result |
| --- | --- |
| Frame | same crop as -0001: alpha bbox x 182..764, y 154..1119, only 110 px of the alpha silhouette differ; pivot (451, 615), 13.795 px/mm, rings, crown box, bracelet joints and case rows reused |
| Dial | beige (cream) matte, black Arabic numerals 12 / 3 / 6 / 9, black baton indices (no lume), black minute track, small raised dots in the dial edge, TUDOR shield, GENEVE, RANGER, SWISS MADE; no date window |
| Hands (10:09:xx) | hour: spear head with cream lume and black outline, tip (346, 543); minute: sword with cream lume strip and black tip section, tip (628, 532); seconds: black needle, small cream lume block, red tip, tip (308, 750), tail end (499, 575); black hub (radius 20 px) |

## Decisions

Same as -0001: hands carry the front-projected photo (`hands_photo`), dial is the 2x photo map (numerals, indices, print stay in the map), bracelet flat, pose 10:09 as photographed, comparison frame 2048 px square at 27.59 px/mm centred on the pivot (2x photo pivot (902, 1230) at (1024, 1024)). Per-dial changes: dial map, dial emission, hand tips and lume fractions.

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_ranger39_prep m79950-0008   # -> 2x reference, config/watches/tudor-ranger39-m79950-0008-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
