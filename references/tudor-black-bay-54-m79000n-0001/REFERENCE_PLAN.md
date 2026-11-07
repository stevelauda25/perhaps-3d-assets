# Reference plan: TUDOR Black Bay 54 M79000N-0001 (37 mm steel, black dial, steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Same recipe as the Royal and Ranger builds ([Ranger 39 -0001](../tudor-ranger-39-m79950-0001/REFERENCE_PLAN.md)); the Black Bay 54 is a different model (dive bezel with insert, snowflake hands, no crown guards, riveted three-column bracelet), so this build also sets the **Black Bay 54 template** for the rubber-strap M79000N-0002.

## Target asset

Front relief GLB `models/watches/tudor-m79000n-0001.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background with drop shadow, 900 x 1200 | `tudor-m79000n-0001_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Royal and Ranger builds, back flat |

## Measured on this photo (px of the 900 x 1200 frame, pivot = hub hole)

| Item | Result |
| --- | --- |
| Alpha bbox | x 192..740 (740 = crown), y 215..1119; the bracelet runs 438 px (31.4 mm) above and 467 px (33.5 mm) below the pivot |
| Pivot, scale | (451, 653); coin-edge bezel left edge x 193 on the pivot row gives 13.946 px/mm (37 mm anchor, 258 px = 18.5 mm). The photo's right bezel edge is at about 703, i.e. the case is about 3 px off-centre on the pivot; the crown hides that side, the silhouette's crown rows take the mirrored left edge |
| Rings (r from pivot, diagonals 225 / 315) | dial_flat 195 (printed dial and minute track), rehaut ring 196..206 (grey, in the dial map), bezel_in 207, black insert 207..249 (numerals 10 / 20 / 30 / 40 / 50, bar markers, triangle with a pearl at 12: all in the photo), dark line 250, steel coin-edge ring 251..258 = bezel_out |
| Bezel | rotating, black aluminium insert inside a steel coin-edge ring, polished inner chamfer |
| Hands (about 10:09:xx) | hour 8.36 mm at 302.5 deg (stem half width 0.52 mm, snowflake diamond widest 3.9 mm at 5.9 mm, flat end, lume strip plus diamond); minute 12.26 mm at 61.5 deg (half width 0.5 mm, lume strip, pointed tip); seconds 12.34 mm at 186.0 deg (needle 0.07 mm, counterweight disc 0.41 mm radius at 4.7 mm behind the hub, lume disc 0.5 mm at 7.0 mm); gold, hub radius 18.5 px (1.33 mm) |
| Crown | x 703..741, y 610..693 (radius 2.98 mm, centre 0.11 mm above the pivot row), fluted, narrower end ring from x 733; no crown guards |
| Case | the lugs rise above the round bezel: lug tops y 344 (22.1 mm), lug bottoms y 957.5 (21.8 mm) |
| Bracelet | three brushed columns with rivet ears at the sides: outer columns top y 243 (end piece 215..243), bottom lug end 957.5 / 1083.5; centre column top joints 373, 311, 219, bottom 931, 1006, 1100.5; vertical joint lines x 389 / 510 (top), 390 -> 393.5 / 510 -> 508.5 (bottom end) |
| Dial | black glossy, gold minute track, round lume dots 1 / 2 / 4 / 5 / 7 / 8 / 10 / 11, bar indices 3 and 9, triangle 12, bar 6, TUDOR shield, GENEVE, 200m=660ft, CHRONOMETER OFFICIALLY CERTIFIED, SWISS MADE; no date window; all flat in the photo map |

## Decisions

| Decision | Answer |
| --- | --- |
| Hands | left in the map; 3D hands carry the front-projected photo (`hands_photo`) with outlines and lume polygons measured from the photo (profile and lume lists in the spec) |
| Bezel numerals, markers, dial print | flat in the photo (projected / dial map), not applied geometry |
| Strap | `strap.kind` in the spec: `bracelet` (built) or `rubber` (placeholder for -0002) |
| Pose | 10:09 as photographed; front-locked presentation |
| Comparison frame | 2048 px square, camera 27.89 px/mm centred on the pivot (2x photo pivot (902, 1306) at (1024, 1024), offset (+122, -282)) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_bb54_prep m79000n-0001   # -> 2x reference, config/watches/tudor-bb54-m79000n-0001-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
