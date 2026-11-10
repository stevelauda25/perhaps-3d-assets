# Reference plan: Orient RA-AC0P03L10B (Bambino 42 mm version 4, blue-grey sunburst dial, brown suede strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Irsyad supplied
the 3/4 photo; the straight front photo comes from a retailer listing of the same reference (see `sources.md`).
House method: modelled case, bezel, lugs, crown, indices, date frame and hands in house steel and glass; photo maps only for
the dial print and the suede strap. Built with the `watch_orient_ra_ac0f06l10b` step (same construction as RA-AC0F06L10B).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 2000 × 2000 | `front_2000x2000.jpg` | HAVE, primary for everything |
| 2 | Dial close-up, 1200 × 1200 | `dial_closeup_1200x1200.png` | HAVE: shapes by eye |
| 3 | Angled, 1200 × 1200 | `angled_1200x1200.jpg` | HAVE: dome and lug curve by eye |
| 4 | 3/4 from the crown side | `three_quarter_2342x3158.jpg` | HAVE |

## Scale anchors

| Dimension | Official | Measured at 42 mm (27.90 px/mm) |
| --- | --- | --- |
| Case width | **42.0 mm** (anchor) | 9-3 row, case edge to the crown root |
| Lug to lug | 49.0 mm | 47.3 mm (the lugs curve down: foreshortened; official value used) |
| Strap | 22 mm | 21.1-22.7 mm past the lug tips |
| Crystal ring | not listed | 37.8 mm |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Round, polished, thin bezel, high domed crystal | #1, #3 |
| Lugs | Long polished lugs curving down, straight inner edges | #1 silhouette |
| Dial | Blue-grey sunburst, printed minute track, crown emblem, ORIENT Automatic, Water Resistant, movement print | dial map |
| Indices | Applied lance batons at 1-11 (3 shortened by the date), coffin-shaped double baton at 12; polished date frame | #1, #2 |
| Hands | Polished dauphine hour and minute, thin seconds with a short tail | #1, fitted axes |
| Crown | Fluted, at 3 | #1 |
| Strap | Brown suede with grey lining and light stitching, 22 mm | strap map |

## Decisions

| Decision | Answer |
| --- | --- |
| Front photo | Retailer's straight front of the same watch; Irsyad's photo is 3/4 only |
| Scale | Official 42 mm case, official 49 mm lug to lug |
| Centre | The photo is taken a little from below: hand axes meet 0.43 mm above the index ring centre; the hub and hand shadows show about 1 mm lower and are masked there |
| Crystal | Domed in the real watch; flat disc at the dome's mean height |
| Heights | Front-relief reading of the official 12 mm |
| Strap curve | House curl: 7 mm radius from the lug tips, end = tip + 2.2 R |

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_ra_ac0p03l10b_trace   # -> config/watches/orient-ra-ac0p03l10b-trace.json
python3 -B -m pipeline.orient_ra_ac0p03l10b_dial    # -> outputs/watches/orient-ra-ac0p03l10b/dial_photo.jpg, strap_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
| 2026-11-10 | 1 | Approved and delivered to `models/watches/orient-ra-ac0p03l10b.glb` |
