# Reference plan: Hamilton Jazzmaster Performer Auto H36205130 (black dial, black bezel insert, steel bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). House method: modelled
case, bezel, crown and hands; photo maps only for the print and the strap. File name `hamilton-h36205130`. Build code shared with the
other Hamilton builds of this session (`pipeline/steps/watch_hamilton_scuba_pioneer.py`).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, transparent background, 2000 × 2000 | `front_official_2000x2000.png` | HAVE, Hamilton's official render, primary for everything |
| 2 | 3/4 | `three_quarter_793x1000.jpg` | HAVE (retailer photo): heights by eye |
| 3 | Back | none | Not needed (flat back) |

## Decisions

| Decision | Answer |
| --- | --- |
| Case size | **38 mm** (listing) = case silhouette at 9 o'clock, 23.26 px/mm. Check: bracelet 19.2 mm at the case against 20 mm lug width |
| Case | One brushed body from the render's alpha outline (case, lugs, crown-side flank), lug tips 21.6 mm |
| Bezel | Polished outer rim (38.0 → 36.9 mm), black insert 36.9 → 32.3 mm photo-mapped, polished inner ring to 31.1 mm, printed silver rehaut track to the 29.4 mm dial |
| Indices | Applied polished batons traced (mean of 11 hours), double baton at 12 traced on its own |
| Hands | Polished tapered batons with lume strips, hour 9.7 mm, minute 15.0 mm; polished seconds needle with a lozenge |
| Bracelet | Three brushed columns (centre 9.1 mm, outer 5.0 mm each), outer joints from 20.9 mm, centre half a row nearer the case, 9 mm pitch, house 7 mm curl |

## Phase 1 outputs

```sh
python3 -B -m pipeline.hamilton_jazz_king_trace h36205130      # -> config/watches/hamilton-h36205130-trace.json
python3 -B -m pipeline.hamilton_scuba_pioneer_dial h36205130   # -> outputs/watches/hamilton-h36205130/ (not committed)
```

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/hamilton-h36205130.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief, house method: brushed body from the render outline, polished rims with the photo's black insert, applied batons (double at 12), three-column bracelet with the 7 mm curl. GLB 1.65 MB |
| 1 | 2026-11-10 | Delivered to `models/watches/hamilton-h36205130.glb` |
