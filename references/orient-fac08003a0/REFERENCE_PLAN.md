# Reference plan: Orient FAC08003A0 (Bambino Version 4, 42 mm: polished steel, grey sunburst dial, rose gold tone batons, brown suede strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). House method (modelled steel and
hands, photo map only for the dial print and the strap), built with the RA-AK0705R10B step (own spec and trace).
File name `orient-fac08003a0`: the tracker matches `Orient` plus the SKU.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, 1077 × 1557, straight-on (a little from below) | `front_1077x1557.png` | HAVE (Orient UK, AC08003A), primary for everything. Watch about 1000 px across |
| 2 | Front turned a little toward the crown | `angled_1000x1586.jpg` | HAVE (Irsyad): crown and case side |
| 3 | Side | none | Heights as FAC0000CA0 (same family, 11.8 mm) |

## Scale anchors

| Dimension | Listing | Measured in #1 at 24.0 px/mm |
| --- | --- | --- |
| Case without crown | 42.0 mm | circle 504 px radius from rows symmetric about y 680: anchor |
| Strap at the lug tips | 22 mm | 22.1 mm top and bottom |
| Lug to lug | 49.0 mm | 48.0 mm (22.8 above and 25.2 below the pivot: seen from below; four lugs averaged) |
| Thickness | 11.8 mm, domed crystal | heights before the 0.35 depth scale |

## Parts

| Part | True shape | Values / where from | Open |
| --- | --- | --- | --- |
| Case | Round, polished, thin bezel, high domed crystal | 42.0 mm; crystal opening 18.33 mm, dial edge 16.96 mm from #1 | Heights without a side photo |
| Lugs | Straight polished lugs | Outline from #1, mean of four, mirrored | |
| Crown | Fluted, 5.4 mm across, 2.8 mm long, 0.6 mm below the 3 o'clock axis | #1 | |
| Dial | Grey sunburst, printed minute track, applied tapered rose gold batons, framed date at 3, rose gold crest, ORIENT | Dial map from #1 with the hands and batons removed; batons as raised rose gold plates (convex outlines) | |
| Hands | Rose gold dauphine hour and minute, rose gold seconds with a red end | Modelled, posed at the photo's time | |
| Strap | Brown suede on black leather, 22 mm | Photo map, house 7 mm curl from the lug tips; buckle left out | |

Scale and photo set confirmed by Irsyad on 2026-11-10 (42.0 mm, Orient UK front photo).

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_fac08003a0_trace   # -> config/watches/orient-fac08003a0-trace.json
python3 -B -m pipeline.orient_fac08003a0_dial    # -> outputs/watches/orient-fac08003a0/photo.jpg (regenerated, not committed)
```

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/orient-fac08003a0.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | House method: round 42 mm polished case, high domed crystal, four mirrored lugs from the photo, fluted crown, rose gold tone dauphine hands and tapered batons, red-tipped seconds, raised ORIENT letters, dial map with the hands and batons removed, 22 mm suede strap from the photo with the house curl |

Approved by Irsyad on 2026-11-10 (round 1), delivered as `models/watches/orient-fac08003a0.glb` (0.9 MB).
