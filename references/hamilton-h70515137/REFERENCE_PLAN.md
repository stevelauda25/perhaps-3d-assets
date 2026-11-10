# Reference plan: Hamilton H70515137 (Khaki Field Auto 42 mm, black dial, steel bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). The supplied photo is angled; the straight front is Hamilton's official render.

## Target asset

A front-facing GLB in `models/watches/hamilton-h70515137.glb`: front relief, flat back, 2.5D depth, modelled case, hands, crown, lugs and bracelet in house steel and glass; the dial from a photo map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on render, transparent background, 2000 × 2000 | `front_official_2000x2000.png` | HAVE (Hamilton official), primary for everything |
| 2 | 3/4 from the left | `angled_1000x1484.jpg` | HAVE (Irsyad): bezel slope, bracelet |
| 3 | Back | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Official | Measured at 42 mm (23.30 px/mm) |
| --- | --- | --- |
| Case width | **42 mm** (anchor) | case edge on the alpha, centred 0.2 mm from the hand pivot (941, 929) |
| Bezel | not listed | polished slope from 37.1 mm (crystal edge) to the case edge |
| Lug width | 22 mm | lug gap 21.0 mm |
| Lug to lug | 53 mm | 51.7 mm in the render (foreshortened); 53 mm used, symmetric |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case, bezel | Polished round case, wide sloped polished bezel | #1, #2 |
| Dial | Black, grey chapter ring with minutes and 5-60, white 1-12, 13-24 inner ring, date window at 3, logo, Khaki Automatic, Swiss Made | dial map |
| Hands | Sword hour and minute with lume and needle tips; white seconds needle with a red tip and a tail disc | #1, bright components in hand-aligned crops |
| Crown | Fluted crown at 3 | #1 |
| Bracelet | Three columns: long outer links (8.5 mm), shorter centre links (6.3 mm) | #1, dark joint rows per column |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Hamilton's official render (the supplied photo is angled) |
| Scale | 42 mm case (official) |
| Lug to lug | Official 53 mm (the render's lugs are foreshortened) |
| Covered prints | 14 (minute hand) and the H of HAMILTON (hour hand) are drawn again from the same dial |
| Heights | Front-relief reading of the official 11 mm |

## Phase 1 outputs

```sh
python3 -B -m pipeline.hamilton_h70515137_trace   # -> config/watches/hamilton-h70515137-trace.json
python3 -B -m pipeline.hamilton_h70515137_dial    # -> outputs/watches/hamilton-h70515137/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
