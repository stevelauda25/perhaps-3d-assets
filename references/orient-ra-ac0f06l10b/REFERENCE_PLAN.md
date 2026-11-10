# Reference plan: Orient RA-AC0F06L10B (Contemporary automatic, blue sunburst dial, blue croc leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Irsyad supplied
the 3/4 photo; the straight front photo comes from a retailer listing of the same reference (see `sources.md`).
House method: modelled case, bezel, lugs, crown, indices, date frame and hands in house steel and glass; photo maps only for
the dial print and the leather strap.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 2000 × 2000 | `front_2000x2000.jpg` | HAVE, primary for everything (soft fine detail) |
| 2 | 3/4 from the crown side, 1000 × 1538 | `three_quarter_1000x1538.jpg` | HAVE: bezel slope and strap thickness, read by eye |
| 3 | Back | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Official | Measured at 41.6 mm (29.81 px/mm) |
| --- | --- | --- |
| Case width | **41.6 mm** (anchor) | 9-3 row, case edge to the crown root |
| Lug to lug | 48.3 mm | 48.31 mm |
| Strap | 22 mm | 21.7-22.4 mm just past the lug tips |
| Crystal ring | not listed | 37.9 mm (inner edge of the polished bezel) |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Round, polished, wide polished bezel sloping up to the crystal | #1, #2 |
| Lugs | Four polished lugs, straight inner edges, curved outer edges | #1 silhouette |
| Dial | Blue sunburst, printed minute track, crown emblem, ORIENT Automatic, Water Resistant, movement print | dial map |
| Indices | Applied faceted tapered batons at 1-11 (3 shortened by the date), a pair at 12; polished date frame at 3 | #1 |
| Hands | Faceted hour and minute with a narrow neck and a shoulder; thin polished seconds with a short wide tail | #1 |
| Crown | Fluted, smooth end cap, at 3 | #1 |
| Strap | Blue croc-print leather, blue stitching, 22 mm | strap map |

## Decisions

| Decision | Answer |
| --- | --- |
| Front photo | Retailer's straight front of the same watch; Irsyad's photo is 3/4 only |
| Scale | Official 41.6 mm case; lug to lug and strap agree |
| Centre | The photo is taken a little from below; the model is symmetric about the index ring centre |
| Heights | Front-relief reading of the official 11.7 mm |
| Hand pose | The pose in #1 so the comparison render lines up |
| Strap curve | House curl: 7 mm radius from the lug tips, end = tip + 2.2 R |

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_ra_ac0f06l10b_trace   # -> config/watches/orient-ra-ac0f06l10b-trace.json
python3 -B -m pipeline.orient_ra_ac0f06l10b_dial    # -> outputs/watches/orient-ra-ac0f06l10b/dial_photo.jpg, strap_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
| 2026-11-10 | 1 | Approved and delivered to `models/watches/orient-ra-ac0f06l10b.glb` |
