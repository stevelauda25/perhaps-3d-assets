# Reference plan: Orient RA-AK0704N10B (Bambino Version 8: polished steel, grey dial, day and 24-hour sub-dials, grey croc leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). House method (modelled steel and
hands, photo map only for the dial print and the leather strap). Same case as RA-AK0705R10B: that build's step, case, lugs and crown.
File name `orient-ra-ak0704n10b`: the tracker matches `Orient` plus the SKU.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, white background, 2000 × 2000, straight-on (seen a little from below) | `front_2000x2000.jpg` | HAVE (retailer, RA-AK0704N30B), primary for the dial, hands, numerals and strap |
| 2 | Front turned a little toward the crown, 726 × 1248 | `angled_726x1248.jpg` | HAVE (Irsyad), check for the crown and case side |
| 3 | Back | none | Not needed (flat back) |

## Scale anchors

| Dimension | Listing | Measured in #1 at 30.67 px/mm |
| --- | --- | --- |
| Case without crown | 40.5 mm (as RA-AK0705R10B) | 1242 px wide (rows away from the crown): anchor |
| Strap at the lug tips | 21 mm | 627 px top / 633 px bottom = 20.45 / 20.64 mm |
| Lug to lug | 46.5 mm | 46.6 mm, but 20.9 above and 25.7 below the pivot: photo seen from below, lugs taken from RA-AK0705R10B |
| Thickness | 12.6 mm | heights as RA-AK0705R10B |

## Parts

| Part | True shape | Values / where from | Open |
| --- | --- | --- | --- |
| Case, lugs, crown, crystal | Same as RA-AK0705R10B | That build's spec values and lug trace | |
| Dial | Grey, minute track with numerals, applied silver Roman numerals and bars, day sub-dial at 10, 24-hour sub-dial at 5, framed date at 3, applied logo | Dial map from #1 with the hands removed; numerals and bars as raised polished steel plates (top-hat outline: the dial is lit unevenly) | |
| Hands | Silver dauphine hour and minute, silver seconds needle with a counterweight, silver sub-dial hands | Modelled, posed at the photo's time | |
| Strap | Grey croc leather, 21 mm, stitched | Photo map, house 7 mm curl from the lug tips; buckle left out | |

## Gaps

- No 3/4 or side photo: heights as RA-AK0705R10B (same case).
- The dial rings are centred on the pivot; the case outline is 3 % shorter than wide (camera a little low). The model uses the round case.

Scale and photo set confirmed by Irsyad on 2026-11-10 (40.5 mm, retailer front photo).

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_ra_ak0704n10b_trace   # -> config/watches/orient-ra-ak0704n10b-trace.json
python3 -B -m pipeline.orient_ra_ak0704n10b_dial    # -> outputs/watches/orient-ra-ak0704n10b/photo.jpg (regenerated, not committed)
```

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/orient-ra-ak0704n10b.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | House method on the RA-AK0705R10B case: polished steel faceted hands (main and sub-dial), applied numerals and bars, raised ORIENT letters, dial map with the hands removed, 21 mm grey strap from the photo with the house curl |

Approved by Irsyad on 2026-11-10 (round 1), delivered as `models/watches/orient-ra-ak0704n10b.glb` (1.4 MB).
