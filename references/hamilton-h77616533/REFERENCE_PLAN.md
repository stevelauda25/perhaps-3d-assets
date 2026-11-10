# Reference plan: Hamilton H77616533 (Khaki Aviation X-Wind Auto Chrono 44 mm, black dial, tan leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). The supplied photo is angled; the straight front is Hamilton's official render.

## Target asset

A front-facing GLB in `models/watches/hamilton-h77616533.glb`: front relief, flat back, 2.5D depth, modelled case, bezel, hands, crown, pushers and lugs in house steel and glass, strap with the house curl; the dial and the strap leather from photo maps.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on render, transparent background, 2000 × 2000 | `front_official_2000x2000.png` | HAVE (Hamilton official), primary for everything |
| 2 | 3/4 from the left | `angled_1000x1325.jpg` | HAVE (Irsyad): bezel height, crown and pushers, rivets |
| 3 | Back | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Official | Measured at 44 mm (25.31 px/mm) |
| --- | --- | --- |
| Case width | **44 mm** (anchor) | bezel edge fitted at the gaps between lugs, lobes, crown and pushers; centred 0.2 mm from the hand pivot (999, 969) |
| Bezel | not listed | steel ring 37.1-44.2 mm with an engraved scale |
| Lug width | 22 mm | lug gap 21.2 mm; strap 20.5-21.2 mm |
| Lug to lug | 54 mm | 52.6 mm in the render (tips 25.0 / 27.6 mm: foreshortened); 54 mm used, symmetric |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Bezel | Polished steel ring, engraved black scale (10-90, 11-25, ticks) | #1; traced by threshold, black inlays |
| Inner ring, dial | Printed rotating ring (drift angles, for CROSS WIND), black dial, silver 12 and 6 subdials, black 3 subdial, applied numerals, lume dots, day-date at 9 | dial map |
| Hands | Sword hour and minute with lume and polished outline; white chrono needle with arrow; three small swords on the subdials | #1, bright components in hand-aligned crops |
| Crown, pushers | Fluted crown at 9, fluted pushers at 2 and 4 | #1, #2 |
| Case, lugs | Case with lobes at 10 and 8, long lugs | #1 silhouette |
| Strap | Tan leather, two rivets each side, white stitching | strap map |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Hamilton's official render (the supplied photo is angled) |
| Scale | 44 mm bezel width (official) |
| Lug to lug | Official 54 mm (the render's lugs are foreshortened) |
| Heights | Front-relief reading of the official 15.55 mm |
| Hand pose | The render's pose (about 10:09, chrono at 37 s) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.hamilton_h77616533_trace   # -> config/watches/hamilton-h77616533-trace.json
python3 -B -m pipeline.hamilton_h77616533_dial    # -> outputs/watches/hamilton-h77616533/dial_photo.jpg and strap_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
