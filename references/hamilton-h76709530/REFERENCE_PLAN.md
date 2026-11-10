# Reference plan: Hamilton H76709530 (Khaki Aviation Pilot Pioneer Mechanical Bronze 43 mm, black dial, brown leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). The supplied photo is angled; the straight front is Hamilton's official render.

## Target asset

A front-facing GLB in `models/watches/hamilton-h76709530.glb`: front relief, flat back, 2.5D depth, modelled bronze case, bezel, hands, crown and lugs, glass, strap with the house curl; the dial and the strap leather from photo maps.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on render, transparent background, 2000 × 2000 | `front_official_2000x2000.png` | HAVE (Hamilton official), primary for everything |
| 2 | 3/4 from the right | `angled_2436x3764.jpg` | HAVE (Irsyad): bezel height, crown |
| 3 | Back | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Official | Measured at 43 mm (24.43 px/mm) |
| --- | --- | --- |
| Case width | **43 mm** (anchor) | bezel scallop tips, centred on the hand pivot (947, 931) |
| Bezel | not listed | glossy black insert 35.0-41.3 mm; dial with railway 33.2 mm |
| Lug width | 20 mm | lug gap 19.4 mm; strap 19.4-20.6 mm |
| Lug to lug | 52 mm | 53.2 mm in the render (used) |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Bezel | Bronze ring with about 100 fine scallops; glossy black insert, beige triangle at 12, 15 30 45, bars | #1; prints traced by threshold |
| Dial | Grained black, beige numerals, railway track, logo, Mechanical, small seconds ring, Swiss Made | dial map |
| Hands | Bronze hour hand with a lume bulb and needle tip; bronze minute baton with lume; small seconds needle with a lozenge counterweight | #1, bright components in hand-aligned crops |
| Crown | Large fluted bronze crown at 3 | #1, #2 |
| Case, lugs | Bronze, brushed flanks and lugs | #1 silhouette, render colour medians |
| Strap | Dark brown leather, cream stitched keeper loops | strap map |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Hamilton's official render (the supplied photo is angled) |
| Scale | 43 mm at the bezel scallop tips (official) |
| Bronze | Colours from the render's medians, metallic |
| Covered numeral | The hour tip covers part of the 0 of 10: it is drawn again as a stadium ring of the same size and stroke |
| Heights | Front-relief reading of the official 13 mm |

## Phase 1 outputs

```sh
python3 -B -m pipeline.hamilton_h76709530_trace   # -> config/watches/hamilton-h76709530-trace.json
python3 -B -m pipeline.hamilton_h76709530_dial    # -> outputs/watches/hamilton-h76709530/dial_photo.jpg and strap_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
