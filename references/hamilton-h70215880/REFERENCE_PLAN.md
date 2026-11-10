# Reference plan: Hamilton Khaki Field Titanium Auto H70215880 (grey dial, black PVD titanium case, khaki suede strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). House method: modelled
case, bezel, crown and hands; photo maps only for the print and the strap. File name `hamilton-h70215880`. Build code shared with the
other Hamilton builds of this session (`pipeline/steps/watch_hamilton_scuba_pioneer.py`).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, transparent background, 2000 × 2000 | `front_official_2000x2000.png` | HAVE, Hamilton's official render, primary for everything |
| 2 | 3/4 | `three_quarter_700x700.jpg` | HAVE (retailer photo): heights by eye |
| 3 | Back | none | Not needed (flat back) |

## Decisions

| Decision | Answer |
| --- | --- |
| Case size | **38 mm** (listing) = case silhouette at 9 o'clock, 24.42 px/mm. Check: strap 20.3 mm against 20 mm |
| Case | One black PVD body from the render's alpha outline (case, lugs, crown-side flank), lug tips 22.7 mm |
| Bezel | Smooth black PVD bezel 38.0 → 33.1 mm, dial 31.9 mm |
| Dial | Printed: lume numerals, 24-hour ring, minute track, logo and the speckled texture (photo map) |
| Hands | Black frames with cream lume and needle tips, hour 9.9 mm, minute 14.3 mm; black seconds hand with a lume tip |
| Strap | Khaki suede from the render, 20.2 mm, house 7 mm curl |

## Phase 1 outputs

```sh
python3 -B -m pipeline.hamilton_jazz_king_trace h70215880      # -> config/watches/hamilton-h70215880-trace.json
python3 -B -m pipeline.hamilton_scuba_pioneer_dial h70215880   # -> outputs/watches/hamilton-h70215880/ (not committed)
```

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/hamilton-h70215880.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief, house method: black PVD body, bezel and crown, black lume hands, khaki suede strap with the 7 mm curl. GLB 1.40 MB |
| 1 | 2026-11-10 | Delivered to `models/watches/hamilton-h70215880.glb` |
