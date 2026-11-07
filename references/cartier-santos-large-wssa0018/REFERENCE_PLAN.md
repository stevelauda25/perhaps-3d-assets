# Reference plan: CARTIER Santos de Cartier Large WSSA0018 (39.8 mm steel, silver dial, steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Same projected-photo recipe as the Cartier [Tank Must XL](../cartier-tank-must-xl-wsta0053/REFERENCE_PLAN.md) (mask from the JPEG, steel map, dial map, 3D hands over the photographed ones), with the bezel / flank rings of the Tudor Black Bay steps instead of brancards and bars. It is the template for the Santos Large WSSA0071 (blue) and WSSA0062 (green).

## Target asset

Front relief GLB `models/watches/cartier-wssa0018.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, light background with soft shadow gradient, 750 x 750 JPEG without alpha | `cartier-wssa0018_original.jpg` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights are estimates (real case thickness about 9 mm), back flat |

## Measured on this photo (px of the 750 x 750 frame, pivot = hub centre (375.0, 364.7), hub radius 9.5 px)

| Item | Result |
| --- | --- |
| Silhouette | derived mask (see `sources.md`): bbox x 222..560 (560 = crown cabochon), y 73..671 |
| Scale | case width 39.8 mm = 304 px between the case flanks (rows 272..301) gives 7.638 px/mm; the horn-to-horn height (rows 173.5 .. 553.5) then reads 49.75 mm against the listed 47.5 mm lug-to-lug (4 percent more than the Catalog ratio; recorded in the trace, not asserted) |
| Case | square case with four horns (brushed end-link housings) that continue into the bracelet end links; polished bezel face (outline traced: x 242..508, y 221.5..513.5, S-curved notch at each corner) carrying eight screws (radius 6.3 px); bezel opening x 268..483, y 257..471 (corner radius 24); dial surface x 272..479, y 261..467; crown guards at x 543.5 |
| Dial | silver, Roman numerals (XII, I, X, XI, II, ... VI with the open IIII and VI forms), railroad minute track square, CARTIER, AUTOMATIC, SWISS MADE, date window at 6; all flat in the photo map |
| Hands (about 10:08) | blue steel sword hands: hour 8.58 mm at 305 deg (0.6 to 0.9 mm wide), minute 12.17 mm at 55 deg (about 0.6 mm), seconds 12.23 mm at 184 deg (0.3 mm) with a 4.63 mm counterweight tail; blue hub radius 1.24 mm |
| Crown | angular steel part x 521..549 (half height 24.5 px = 3.2 mm, axis y 364.5) plus a blue sapphire cabochon to x 559.8 |
| Bracelet | one column of links, each with two screws; joints (rows) top 214.5 / 175.5 / 136 / 102.5 / 82 / end 72.5, bottom 515.5 / 551.5 / 591.5 / 627.5 / 655 / end 671.5; the first link on each side is the end link between the horns (x 291..459) |

## Decisions

| Decision | Answer |
| --- | --- |
| Silhouette | mask derived from the JPEG (no alpha), recorded in `sources.md` and the trace |
| Hands | left in the dial map; 3D hands carry the front-projected photo (`hands_photo`) with outlines measured from the photo (spec `hands.profile`) |
| Numerals, minute track, date window, print, screw slots | flat in the maps, not applied geometry; the bezel screw heads are shallow domes |
| Crown | lathe from the measured profile with the sapphire dome; facets and blue come from the projected photo |
| Pose | 10:08 as photographed; front-locked presentation |
| Comparison frame | 1600 px square, camera 15.276 px/mm centred on the pivot (the pivot of the 2x photo, (750.5, 729.9), at (799.5, 799.5): translation (+49.0, +69.6)) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.cartier_santoslarge_prep wssa0018   # -> 2x reference, mask, config/watches/cartier-santoslarge-wssa0018-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
