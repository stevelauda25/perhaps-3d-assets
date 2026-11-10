# Reference plan: Hamilton Khaki Aviation Pilot Pioneer Mechanical H76419941 (blue dial, brushed cushion case, blue NATO strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). House method: modelled
case, bezel, crown and hands; photo maps only for the print and the strap. File name `hamilton-h76419941`. Build code shared with the
other Hamilton builds of this session (`pipeline/steps/watch_hamilton_scuba_pioneer.py`).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, transparent background, 2000 × 2000 | `front_official_2000x2000.png` | HAVE, Hamilton's official render, primary for everything |
| 2 | 3/4 | `three_quarter_1000x1000.jpg` | HAVE (retailer photo): heights by eye |
| 3 | Back | none | Not needed (flat back) |

## Decisions

| Decision | Answer |
| --- | --- |
| Case size | Hamilton lists **36 x 33 mm**. The render's case is 887 × 1028 px (taller than wide), so the model is **33 mm wide** (anchor: case edge at 9 o'clock, 27.03 px/mm) and 37.6 mm tall. Check: strap 16.8 mm against the 18 mm listed lug width (7 % narrow). OPEN: confirm the scale with the owner |
| Case | One brushed cushion body from the render's alpha outline, straight case edge between the horns where the strap passes (14.5 mm from the pivot), horn tips at 18.8 mm |
| Bezel | Polished ring 28.8 → 25.8 mm sloping up to the crystal; dial 24.9 mm |
| Dial | Printed: numerals, triangle at 12, minute track, logo (photo map) |
| Hands | Polished sword hour (8.0 mm) and minute (12.4 mm) with cream lume, polished seconds needle with a short counterweight |
| Strap | Blue NATO from the render (keeper rings included), 16.8 mm, house 7 mm curl from the horn tips |

## Phase 1 outputs

```sh
python3 -B -m pipeline.hamilton_jazz_king_trace h76419941      # -> config/watches/hamilton-h76419941-trace.json
python3 -B -m pipeline.hamilton_scuba_pioneer_dial h76419941   # -> outputs/watches/hamilton-h76419941/ (not committed)
```

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/hamilton-h76419941.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief, house method: brushed cushion body from the render outline (33 mm wide), polished bezel ring, sword hands with lume, blue NATO strap with the 7 mm curl. GLB 1.58 MB |
| 1 | 2026-11-10 | Delivered to `models/watches/hamilton-h76419941.glb` |
