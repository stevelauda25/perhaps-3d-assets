# Reference plan: Orient FAC0000CA0 (Bambino Version 3: polished steel, grey sunburst dial, silver batons, black leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). House method (modelled steel and
hands, photo map only for the dial print and the leather strap), built with the RA-AK0705R10B step (own spec and trace).
File name `orient-fac0000ca0`: the tracker matches `Orient` plus the SKU.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, white background, 2000 × 2000, straight-on | `front_2000x2000.jpg` | HAVE (WatchNation, TAC0000CA0), primary for everything |
| 2 | Side from the crown, 800 × 800 | `side_800x800.jpg` | HAVE (Ocarat): crystal dome and case profile |
| 3 | Front turned a little toward the crown | `angled_1000x1570.jpg` | HAVE (Irsyad): crown and case side |

## Scale anchors

| Dimension | Listing | Measured in #1 at 27.68 px/mm |
| --- | --- | --- |
| Case without crown | 40.5 mm | 1121 px wide (rows away from the crown): anchor |
| Strap at the lug tips | 21 mm | 20.5 / 20.4 mm (lug inner faces 21.4 mm apart) |
| Lug to lug | 46.8 mm | 45.3 mm |
| Thickness | 11.8 mm, high domed crystal | heights before the 0.35 depth scale |

## Parts

| Part | True shape | Values / where from | Open |
| --- | --- | --- | --- |
| Case | Round, polished, thin bezel, high domed crystal | 40.5 mm; crystal opening 18.21 mm, dial edge 17.13 mm from #1 | |
| Lugs | Straight polished lugs | Outline from #1, mean of four, mirrored | |
| Crown | Fluted, 4.7 mm across, 2.6 mm long, on the 3 o'clock axis | #1 | |
| Dial | Grey sunburst, printed minute track, applied silver batons, date at 3, crest, ORIENT, Water Resistant | Dial map from #1 with the hands and batons removed; batons as raised polished steel plates | Glare arc of the crystal stays in the map |
| Hands | Silver rectangular (Bauhaus) hour and minute, silver seconds with a straight tail | Modelled, posed at the photo's time | |
| Strap | Smooth black leather, 21 mm | Photo map, house 7 mm curl from the lug tips; buckle left out | |

Scale and photo set confirmed by Irsyad on 2026-11-10 (40.5 mm, retailer front photo).

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_fac0000ca0_trace   # -> config/watches/orient-fac0000ca0-trace.json
python3 -B -m pipeline.orient_fac0000ca0_dial    # -> outputs/watches/orient-fac0000ca0/photo.jpg (regenerated, not committed)
```

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/orient-fac0000ca0.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | House method: round 40.5 mm polished case, high domed crystal, four mirrored lugs from the photo, fluted crown, polished steel rectangular hands and batons, raised ORIENT letters, dial map with the hands removed, 21 mm black strap from the photo with the house curl |

Approved by Irsyad on 2026-11-10 (round 1), delivered as `models/watches/orient-fac0000ca0.glb` (0.8 MB).
