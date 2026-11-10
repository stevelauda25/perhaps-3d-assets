# Reference plan: Orient RA-AC0Q16N (grey fume diver, steel bezel, steel bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Front photo supplied by Irsyad on 2026-11-10.

## Target asset

A front-facing GLB in `models/watches/orient-ra-ac0q16n.glb`, built like `seiko-sur419p1.glb`: front relief, flat back, 2.5D depth, modelled case, bezel, indices, hands, crown and bracelet in house steel and glass; the dial print from a photo map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 1228 × 2048 (2× working copy 2456 × 4096) | `front_1228x2048.jpg`, `front_2x_2456x4096.png` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | none | MISSING: heights estimated from the listed 12.8 mm |
| 3 | Back | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Listed | Measured at 39.9 mm (49.95 px/mm on the 2× copy) |
| --- | --- | --- |
| Bezel diameter | **39.9 mm** (anchor, listing) | circle on the flanks, centred 0.15 mm below the hand pivot (1150, 1975) |
| Lug width | 20 mm | end link 19.4 mm; bracelet 19.5-20.0 mm just past the lugs |
| Lug to lug | 46.5 mm | 45.75 mm (tips 22.6 mm top, 23.1 mm bottom) |
| Bezel rings | not listed | inner lip 29.4 mm, brushed top 30.2-37.0 mm, slotted rim to 39.9 mm |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Bezel | Steel: polished inner lip, brushed flat top with black-filled engravings (triangle with dot at 12, dots 1-14, bars, 10-50 as outline numerals), coin-edge rim with about 72 slots, a few larger grip recesses | #1; engravings traced by threshold |
| Case, lugs | Round case under the bezel; broad lugs with a brushed top and polished chamfer | #1 silhouette |
| Dial | Grey fume sunburst (dark at the edge), minute track with lume squares at 3 and 9 | dial map |
| Indices | Applied polished frames with lume: triangle at 12, bars at 6 and 9, trapezoids at the other hours; polished date frame at 3 | #1 |
| Logo, print | Crown emblem, ORIENT, Automatic, Water Resistant 20 bar, movement print at 6 | dial map |
| Hands | Hour: arrow with a black stem and lume head; minute: sword with a black stem and lume blade; seconds: needle, orange-framed lume triangle, black counterweight | #1 |
| Crown | Fluted crown with a smooth collar at 3, no guards | #1 |
| Bracelet | Three columns, brushed; centre joints 1.15 mm nearer the case; pitch 5.3 mm | #1 |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | 39.9 mm bezel (listing) |
| Bezel engravings | Traced outlines built as black inlays on the brushed top (geometry, not a photo map) |
| Heights | Front-relief reading of the listed 12.8 mm (no side photo) |
| Hand pose | The pose in #1 so the comparison render lines up |
| Bracelet curve | House curl: 7 mm radius from the lug tips, end_y = tip + 2.2 R |

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_ra_ac0q16n_trace   # -> config/watches/orient-ra-ac0q16n-trace.json
python3 -B -m pipeline.orient_ra_ac0q16n_dial    # -> outputs/watches/orient-ra-ac0q16n/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
