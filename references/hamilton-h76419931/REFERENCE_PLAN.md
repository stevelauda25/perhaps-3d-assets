# Reference plan: Hamilton H76419931 (Khaki Aviation Pilot Pioneer Mechanical 36 x 33 mm, black dial, grey NATO strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). The supplied photo is 367 px wide; the working front is Hamilton's official render.

## Target asset

A front-facing GLB in `models/watches/hamilton-h76419931.glb`: front relief, flat back, 2.5D depth, modelled cushion case, hands and crown in house steel and glass, NATO strap with the house curl; the dial and the strap weave from photo maps.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on render, transparent background, 1200 × 1200 | `front_official_1200x1200.png` | HAVE (Hamilton official), primary for everything |
| 2 | Front, retailer, 367 × 720 | `front_retail_367x720.jpg` | HAVE (Irsyad): check only, too small to trace |
| 3 | 3/4, back | none | MISSING: heights estimated from the official 9.95 mm |

## Scale anchors

| Dimension | Official | Measured at 33 mm (16.12 px/mm) |
| --- | --- | --- |
| Case width | **33 mm** (anchor, "36 x 33 mm") | cushion at its widest row, crown excluded |
| Case length | 36 mm | 37.3 mm in the render (kept): 18.2 mm above, 19.2 mm below the pivot |
| Lug width | 18 mm | NATO strap 16.7 mm in the render |
| Dial | not listed | printed dial 26.3 mm, polished ring to 28.2 mm |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Brushed cushion, polished edge, polished ring round the crystal | #1 alpha outline per row |
| Dial | Black grained; printed white 1-12, beige triangle, bars at 3 6 9, dots; white chapter ring; Hamilton, Mechanical, Swiss Made | dial map |
| Hands | Lance hour and needle minute with beige lume; polished seconds needle | #1, hand-aligned crops |
| Crown | Small fluted crown at 3 | #1 |
| Strap | Grey NATO running under the case | strap map |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Hamilton's official render (the supplied photo is 367 px wide) |
| Scale | 33 mm case width (official); the render's length is kept |
| Covered numeral | The hour tip covers the right half of the 0 of 10: mirrored from the left half |
| Heights | Front-relief reading of the official 9.95 mm |

## Phase 1 outputs

```sh
python3 -B -m pipeline.hamilton_h76419931_trace   # -> config/watches/hamilton-h76419931-trace.json
python3 -B -m pipeline.hamilton_h76419931_dial    # -> outputs/watches/hamilton-h76419931/dial_photo.jpg and strap_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
