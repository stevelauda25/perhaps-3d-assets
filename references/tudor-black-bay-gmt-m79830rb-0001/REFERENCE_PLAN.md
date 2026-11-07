# Reference plan: TUDOR Black Bay GMT M79830RB-0001 (41 mm steel, black dial, blue/red GMT bezel, steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Same recipe as the Royal, Ranger and Black Bay 54 builds ([Black Bay 54 -0001](../tudor-black-bay-54-m79000n-0001/REFERENCE_PLAN.md)); the Black Bay GMT is a different model (41 mm case, 24 h two-colour bezel with polished flange, date window, red GMT hand with arrow head, straight diagonal lug flanks, crown on a neck), so this build sets the **Black Bay GMT template**.

## Target asset

Front relief GLB `models/watches/tudor-m79830rb-0001.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background with drop shadow, 900 x 1200 | `tudor-m79830rb-0001_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Black Bay 54 build, back flat |

## Measured on this photo (px of the 900 x 1200 frame, pivot = hub hole)

| Item | Result |
| --- | --- |
| Alpha bbox | x 171..775 (775 = crown), y 125..1121; the bracelet runs 485 px (35.8 mm) above and 511 px (37.7 mm) below the pivot |
| Pivot, scale | (450, 610); bezel left edge x 172 on the pivot row gives 13.561 px/mm (41 mm anchor, 278 px = 20.5 mm); the black dial's enclosing circle is centred at (449.5, 610.7), so the photo is centred on the pivot within 1 px |
| Rings (r from pivot, diagonals 115 / 135 / 160 / 200 / 225) | dial_flat 191 (minute track 188..190), black rehaut 192..202, polished steel flange 203..222 (grey, in the dial map out to 206, steel map beyond), dark gap 223..225, insert 226..270 (blue above, red below the 3 / 9 o'clock line; numerals 22 20 18 16 14 12 10 8 6 4 2, pearl dots, white triangle at 12 are in the photo), coin-edge steel ring 271..278 = bezel_out |
| Hands (about 10:09:xx) | hour 9.25 mm at 304.0 deg (stem half width 0.6 mm, snowflake diamond widest 2.1 mm at 6.75 mm, end bar from 8.2 mm, white lume nearly over the whole hand); minute 13.75 mm at 63.8 deg (half width 0.52 mm, long taper tip); seconds 13.7 mm at 185.7 deg (needle 0.15 mm half width, 8 px wide tail stub 4.5 mm behind the hub, rhombus lume 2.3 mm wide at 9.0 mm); GMT hand red at 152.3 deg, shaft 0.4 mm wide, arrow head 4.0 x 2.7 mm (red frame, white lume) with a short stem ending at 14.3 mm; hub radius 1.47 mm |
| Crown | fluted part x 736..777, y 561..668 (radius 3.95 mm, centre 0.33 mm below the pivot row), about 80 fine flutes, rounded outer edge; neck x 722..736, 84 px high; no crown guards |
| Case | straight diagonal lug flanks from the bezel (y 545) to the lug corners; case top edge y 282 (24.2 mm), bottom edge y 943 (24.55 mm); rounded lug corners |
| Bracelet | three brushed columns with rivet ears at the sides: outer columns top joint y 162, bottom 1063.5; centre column top joints 297 / 241 / 234 (0.5 mm dark band 234..241), bottom 927 / 989 / 995 / 1101 / 1106; vertical joint lines x 381 / 515 (top), 380 / 514 (bottom); width 276 px (20.4 mm) |
| Dial | black glossy, white minute track, round lume dots 1 / 2 / 4 / 5 / 7 / 8 / 10 / 11 (index circles), bar indices 3 / 6 (date side) and 9, triangle 12, TUDOR shield, GENEVE, GMT, CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE; date window 573..625 x 592..628 at 3 o'clock showing 28; all flat in the photo map |

## Decisions

| Decision | Answer |
| --- | --- |
| Hands | left in the map; 3D hands carry the front-projected photo (`hands_photo`) with outlines measured from the photo (profile lists, GMT arrow head as a polygon, in the spec) |
| Bezel colours, numerals, dial print, date | flat in the photo (projected / dial map), not applied geometry |
| Strap | steel bracelet, `strap.kind = bracelet` |
| Pose | 10:09 as photographed; front-locked presentation |
| Comparison frame | 2048 px square, camera 27.122 px/mm centred on the pivot (2x photo pivot (900, 1220) at (1024, 1024), offset (+124, -196)) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_bbgmt_prep m79830rb-0001   # -> 2x reference, config/watches/tudor-bbgmt-m79830rb-0001-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
