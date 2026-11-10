# Reference plan: Orient RA-AK0705R10B (polished steel, burgundy sunburst dial, day and 24-hour sub-dials, brown croc leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). House method (modelled steel and
hands, photo map only for the dial print and the leather strap), as Orient Star RE-AT0007N00B round 3.
File name `orient-ra-ak0705r10b`: the tracker matches `Orient` plus the SKU.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, white background, 1569 × 2380, close to straight-on | `front_1569x2380.jpg` | HAVE, primary for everything. Under the 2000 px target on the short side |
| 2 | 3/4 from the crown side | none | MISSING: heights from the 12.6 mm listing and the front photo's rings |
| 3 | Back | none | Not needed (flat back) |

## Scale anchors

| Dimension | Listing | Measured in #1 at 33.58 px/mm |
| --- | --- | --- |
| Case without crown | 40.5 mm | 1360 px (circle fit on the case outline, 0.4 px mean residual): anchor |
| Strap at the lug tips | 21 mm | 697 px top / 702 px bottom = 20.8 / 20.9 mm |
| Lug to lug | 46.5 mm | 22.6 + 23.6 = 46.2 mm (pivot 0.38 mm above the case centre) |
| Thickness | 12.6 mm | heights before the 0.35 depth scale |

## Parts

| Part | True shape | Values / where from | Open |
| --- | --- | --- | --- |
| Case | Round, polished, thin flank, wide polished bezel stepping up to a high domed crystal | 40.5 mm; ring radii from #1 in Phase 1 | Bezel and dome heights without a 3/4 photo |
| Lugs | Straight polished lugs, outer side slanted toward the tip | Outline from #1, mirrored | |
| Crown | Fluted, about 6.2 mm across, 3 mm long, a little below the 3 o'clock axis | #1 | |
| Dial | Burgundy sunburst, minute track with numerals, applied Roman numerals and bars (black with a gold edge), day sub-dial at 10, 24-hour sub-dial at 5, framed date at 3, applied logo | Dial map from #1 with the hands removed; applied numerals and bars as raised dark plates traced from the photo | |
| Hands | Black dauphine hour and minute with a gold edge, gold seconds needle with a counterweight, gold sub-dial hands | Modelled, posed at the photo's time | |
| Crystal | Domed | House glass | |
| Strap | Brown croc leather, 21 mm, stitched | Photo map, house 7 mm curl from the lug tips; buckle left out | |

## Gaps

- No 3/4 or side photo: bezel step and dome heights are estimated from the listing thickness.
- The photo is about 1570 px wide: dial print is sharp enough for the numerals and sub-dial text; the small `MOV'T JAPAN` print is soft.

Scale and photo set confirmed by Irsyad on 2026-11-10 (40.5 mm, front photo only).

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_ra_ak0705r10b_trace   # -> config/watches/orient-ra-ak0705r10b-trace.json
python3 -B -m pipeline.orient_ra_ak0705r10b_dial    # -> outputs/watches/orient-ra-ak0705r10b/photo.jpg (regenerated, not committed)
```

The listing gives gold-tone hands and indices: they look black in the photo because they reflect the dark studio. Modelled as polished gold.

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/orient-ra-ak0705r10b.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | House method: round 40.5 mm polished case and bezel, polished rehaut, boxed domed crystal, four mirrored lugs from the photo, fluted crown, faceted gold hands (main and sub-dial), gold applied numerals and bars, raised ORIENT letters, dial map with the hands removed, 21 mm strap from the photo with the house curl |
| 2 | 2026-11-10 | Hour, minute and sub-dial hands, the hub, Roman numerals and bars black (Irsyad, as the photo); seconds hand stays gold |

Approved by Irsyad on 2026-11-10 (round 2), delivered as `models/watches/orient-ra-ak0705r10b.glb` (1.6 MB).
