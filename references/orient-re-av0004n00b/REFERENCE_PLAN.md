# Reference plan: Orient Star RE-AV0004N00B (Contemporary Modern Skeleton, grey open-heart dial, rose-gold hands, steel bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Irsyad supplied
the 3/4 photo; the straight front and angled renders are Orient's official images (see `sources.md`). House method: modelled
case, bezel, lugs, crown, indices, XII, hands and bracelet in house materials; photo map for the dial.
Shared scripts with its sibling: `pipeline/orient_re_av00_trace.py`, `pipeline/orient_re_av00_dial.py`, step `watch_orient_re_av00`.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 2000 × 2000 | `front_2000x2000.webp` | HAVE, primary for everything |
| 2 | Low angled render, 2000 × 2000 | `angled_2000x2000.webp` | HAVE: heights read by eye |
| 3 | 3/4 from the crown side | `three_quarter_1000x1474.jpg` | HAVE |

## Scale anchors

| Dimension | Official | Measured at 41 mm |
| --- | --- | --- |
| Case width | **41 mm** (anchor) | 9-3 row, case edge to the crown root |
| Lug to lug | 49 mm | 48.95 mm |
| Lug width | not on the official sheet (20 or 21 mm at retailers) | 21.2 mm (lug gap, end link row) |
| Crystal ring | not listed | 37.9 mm (inner edge of the polished bezel) |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Round, polished, wide concave polished bezel sloping up to the crystal | #1, #2 |
| Lugs | Brushed tops with polished edges, flowing out of the case to rounded tips | #1 silhouette |
| Dial | Open heart at 9, power reserve at 12, small seconds at 6, skeleton window at 2, chapter ring with minute numerals, logo | dial map |
| Indices | Applied faceted wedges at 1-8, 10, 11 (8 and 10 shortened), applied XII | #1 |
| Hands | Hour and minute: metal frame with lume inlay and long counterweight tails | #1, rotated strips |
| Crown | Large fluted crown with a smooth cap, at 3 | #1 |
| Bracelet | five-piece bracelet: brushed outer links, polished narrow links, brushed centre link; narrow and centre joints 2.4 mm nearer the case; pitch 6.6 mm | #1 bottom side |

## Decisions

| Decision | Answer |
| --- | --- |
| Front photo | Orient's official render; Irsyad's photo is 3/4 only |
| Scale | Official 41 mm case; official 49 mm lug to lug agrees |
| Dial layout | Same dial and hand pose as the sibling render; read once in mm and checked on both overlays |
| Hand removal | Inpainting (dial not rotationally even); the modelled hands cover the zones |
| Heights | Front-relief reading of about 12 mm and the angled render |
| Bracelet curve | House curl: 7 mm radius from the lug tips, end = tip + 2.2 R |

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_re_av00_trace re-av0004n00b   # -> config/watches/orient-re-av0004n00b-trace.json
python3 -B -m pipeline.orient_re_av00_dial re-av0004n00b    # -> outputs/watches/orient-re-av0004n00b/ (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
| 2026-11-10 | 1 | Approved and delivered to `models/watches/orient-re-av0004n00b.glb` |
