# Reference plan: Orient RA-WJ0004Y Mako Solar (steel, beige bezel, brown sunburst dial, steel bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). House method: modelled steel,
bezel, indices and hands; photo map for the dial print and the bezel insert print.
File name `orient-ra-wj0004y`: the tracker matches `Orient` plus the SKU.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, white background, 1855 × 3183, straight-on | `front_1855x3183.jpg` | HAVE, primary for everything. Under the 2000 px target on the short side |
| 2 | 3/4 from the crown side | none | MISSING: heights estimated (thickness not listed) |
| 3 | Back | none | Not needed (flat back) |

## Scale anchors

| Dimension | Listing | Measured in #1 at 37.79 px/mm |
| --- | --- | --- |
| Case without crown | 39.9 mm (Orient USA, most retailers) | 1508 px across the pivot row (left flank mirrored about the bezel centre): anchor |
| Bracelet at the lugs | 20 mm | 756 px = 20.0 mm |
| Bezel | not listed | 1442 px = 38.2 mm (circle fit, centre 2.6 px from the pivot) |
| Lug to lug | not listed | 23.1 + 23.4 = 46.5 mm |
| Thickness | not listed | estimate about 12 mm |

watch.co.uk lists 42.8 mm / 22 mm: at 22 mm the case would be 43.9 mm and the bezel 42.0 mm, so that listing does not fit the photo.

## Parts

| Part | True shape | Values / where from | Open |
| --- | --- | --- | --- |
| Case | Diver case, brushed lug tops with polished bevels, notch at 9 | Outline from #1 | Heights |
| Bezel | Beige aluminium insert with white print and triangle, steel coin edge visible outside it | 38.2 mm; insert print from the photo map | |
| Crown | Fluted, at 3 | #1 | |
| Dial | Brown sunburst, applied lume bars with steel frames, applied 12, 6 and 9, framed date at 3, logo and print | Dial map from #1 with the hands removed; bars and numerals raised | |
| Hands | Steel sword hour and minute with lume, thin seconds with orange tip and a dark counterweight | Modelled, posed at the photo's time | |
| Bracelet | Three columns, brushed, row pitch and column split from #1 | House curl from the lug tips | |

## Gaps

- No 3/4 or side photo, and no listed thickness: case, bezel and bracelet heights are estimates.

Scale and photo set confirmed by Irsyad on 2026-11-10 (39.9 mm, front photo only).

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_ra_wj0004y_trace   # -> config/watches/orient-ra-wj0004y-trace.json
python3 -B -m pipeline.orient_ra_wj0004y_dial    # -> outputs/watches/orient-ra-wj0004y/photo.jpg (regenerated, not committed)
```

Bracelet from the photo: three columns (centre 0.49 of the width), pitch 6.5 mm, outer and centre joints almost level (0.4 mm apart).

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/orient-ra-wj0004y.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | House method: brushed case plate from the photo silhouette, polished bezel ring with the photo insert, applied frames with lume for the bars and the 12, 6 and 9, raised ORIENT letters, sword hands with lume, dark seconds with an orange tip, fluted crown, three-column bracelet with the house curl |

Approved by Irsyad on 2026-11-10 (round 1), delivered as `models/watches/orient-ra-wj0004y.glb` (2.2 MB).
