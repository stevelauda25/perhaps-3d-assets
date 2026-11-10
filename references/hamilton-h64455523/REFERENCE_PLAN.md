# Reference plan: Hamilton Khaki Field King Auto H64455523 (beige day-date dial, brown leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). House method:
modelled case, bezel, crown and hands; photo maps only for the dial print and the leather strap. File name
`hamilton-h64455523`. Build code shared with H32515135 (`pipeline/steps/watch_hamilton_scuba_pioneer.py`).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, transparent background, 2000 × 2000 | `front_official_2000x2000.png` | HAVE, Hamilton's official render, primary for everything |
| 2 | 3/4 from the crown side | `three_quarter_706x900.jpg` | HAVE (retailer photo): heights by eye |
| 3 | Back | none | Not needed (flat back) |

## Decisions

| Decision | Answer |
| --- | --- |
| Case size | **40 mm** (listing) = case silhouette at 9 o'clock on the pivot row, 26.8 px/mm. Check: lug gap 20.037 mm against 20 mm |
| Origin | Hand pivot (998, 986). The render's bezel lines sit about 0.3 mm lower than the pivot (slight camera tilt); the model is round about the pivot |
| Case | One brushed body from the render's alpha outline (case, lugs and crown guards), 12 and 6 o'clock halves averaged, lug tips 24.441 mm |
| Bezel | Wide smooth polished bezel from 38.9 to 33.7 mm, black rehaut ring to the 33.0 mm dial |
| Dial | Everything printed: numerals, 24-hour ring, track, day and date windows, logo |
| Hands | Polished hour (9.9 mm) and minute (14.1 mm) hands with pale green lume and needle tips; polished seconds hand with an arrow tip |
| Crown | Fluted, 5.6 mm across, between the crown guards |
| Strap | Brown leather with white stitching from the render, 19.7 mm, house 7 mm curl; buckle outside the render |

## Phase 1 outputs

```sh
python3 -B -m pipeline.hamilton_jazz_king_trace h64455523      # -> config/watches/hamilton-h64455523-trace.json
python3 -B -m pipeline.hamilton_scuba_pioneer_dial h64455523   # -> outputs/watches/hamilton-h64455523/dial.jpg, strap.jpg (not committed)
```

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/hamilton-h64455523.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief, house method: brushed body with crown guards from the render outline, wide polished bezel, lume hands, brown leather strap with the 7 mm curl. GLB 1.58 MB |
| 1 | 2026-11-10 | Delivered to `models/watches/hamilton-h64455523.glb` |
