# Reference plan: Orient RA-AC0Q17Y (Mako 40, copper fume dial, steel bezel, steel bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Front photo supplied by Irsyad on 2026-11-10.

## Target asset

A front-facing GLB in `models/watches/orient-ra-ac0q17y.glb`, built like `orient-ra-ac0q16n.glb` (same case, bezel, hands and bracelet): front relief, flat back, 2.5D depth, modelled case, bezel, indices, hands, crown and bracelet in house steel and glass; the dial print from a photo map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 1241 × 2048 (2× working copy 2482 × 4096) | `front_1241x2048.jpg`, `front_2x_2482x4096.png` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | none | MISSING: heights as RA-AC0Q16N (listed 12.8 mm) |
| 3 | Back | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Listed | Measured at 39.9 mm (49.98 px/mm on the 2× copy) |
| --- | --- | --- |
| Bezel diameter | **39.9 mm** (anchor, listing) | circle on the flanks, centred 0.3 mm below the hand pivot (1146, 1948) |
| Lug width | 20 mm | end link 19.9 mm; bracelet 19.65 mm just past the lugs |
| Lug to lug | 46.5 mm | 45.5 mm (tips 21.9 mm top, 23.6 mm bottom: the top end leans away) |
| Bezel rings | not listed | inner lip 29.5 mm, brushed top 30.3-36.9 mm, slotted rim to 39.9 mm |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Bezel | As RA-AC0Q16N: polished inner lip, brushed top with black-filled engravings, 72-slot coin-edge rim. Rotated a few degrees in this photo | #1; engravings traced by threshold, shadow arcs on the inner step filtered out |
| Dial | Grained (sandy) copper fume, dark at the edge; minute track; lume squares at 3 and 9 | dial map |
| Indices, date | As RA-AC0Q16N | #1 |
| Hands | As RA-AC0Q16N; seconds lume triangle has its wide end toward the pivot | #1 |
| Crown, lugs, bracelet | As RA-AC0Q16N; bracelet pitch 5.74 mm, centre joints 1.47 mm nearer the case | #1 |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | 39.9 mm bezel (listing) |
| Hand pose | The pose in #1 (about 10:07:45) |
| Dial filler | Isotropic sand grain under the hand zones (the dial has no sunburst) |
| Bracelet curve | House curl: 7 mm radius from the lug tips, end_y = tip + 2.2 R |

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_ra_ac0q17y_trace   # -> config/watches/orient-ra-ac0q17y-trace.json
python3 -B -m pipeline.orient_ra_ac0q17y_dial    # -> outputs/watches/orient-ra-ac0q17y/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
