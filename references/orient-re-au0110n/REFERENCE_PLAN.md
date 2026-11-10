# Reference plan: Orient Star RE-AU0110N (steel, grey sunburst dial with power reserve and date, three-link steel bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 for review.
Method: the house front relief (modelled parts, house steel and glass, photo map only for the dial print). Built together
with RE-AU0108G: same case, bracelet and parts, different dial colour, so one step (`watch_orient_re_au01`) serves both and
the part sizes read on the sharper RE-AU0110N photo are shared. File name `orient-re-au0110n`: first word of the title plus the SKU.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, white background, 1251 × 2082 | `front_1251x2082.jpg` (+ 2× working copy) | HAVE, primary for everything. Under the 2000 px width target |
| 2 | 3/4 from the crown side | none | GAP: heights (bezel slope, lug slope, crown height) follow the listed 12.3 mm thickness |
| 3 | Back | none | not needed (flat back) |

## Decisions

| Part | Decision |
| --- | --- |
| Case size | **38.5 mm** (orient-watch.com) across the flanks. Check: gap between the lugs 20.0 mm on RE-AU0110N (listed 20), 19.5 mm on RE-AU0108G |
| Origin | Hand pivot; scale from the case circle fitted on the flanks (RE-AU0110N 50.0 px/mm, RE-AU0108G 49.2 px/mm on the 2× copy) |
| Case | Thin flank to 19.25 mm, wide polished bezel sloping from 19.0 mm to the crystal ring at 17.25 mm, black gasket, flat crystal |
| Lugs | Four faceted lugs from the photo silhouette, leaving the case circle at y 7.75 mm: brushed top sloping 7.2 → 5.4 mm, polished outer facet 1.9 mm wide; tip 23.3 mm (photo 22.7 / 23.8 at 12 / 6, listed lug to lug 46.9) |
| Dial | Flat to 16.2 mm, rehaut up to the crystal ring. Print, lume dots, minute track, grooved ring, date, logo and the power reserve scale are the photo map with the hands removed |
| Indices | Applied faceted batons 12.5 → 14.5 mm, 1.2 mm wide at 1 2 4 5 7 8 10 11; a grooved block of three bars at 3 (beside the date), a wide baton at 9; applied XII and VI built from strokes read on gridded crops |
| Power reserve | Raised crescent (4.95 → 6.15 mm about its centre, 105 → 255 deg) carrying its own print; dark faceted hand on its own pivot below XII, dark cap |
| Hands | Dauphine hour (9.95 mm) and minute (14.4 mm) with a narrow neck and pointed tails, polished, ridge along the middle; dark seconds needle with a counterweight; posed at the photo's time (10:08) |
| Crown | Fluted (20 flutes), 3.18 mm radius, 19.0 → 21.66 mm on the 3 o'clock axis, smooth end cap to 22.12 mm |
| Bracelet | Three columns: brushed centre link ±3.4 mm, polished rails 3.55 → 4.85 mm, brushed outer links to the edge; pitch 6.0 mm; centre joints 1.3 mm nearer the case than the outer and rail joints; dark backing; house 7 mm curl from the lug tips; clasp left out |

## Known gaps

- No side or 3/4 photo: heights are inferred (12.3 mm listed thickness, house 0.35 depth scale).
- The lug tips are cut straight; in the photo they are slightly slanted.
- The dial map near the hub (inside 2.6 mm) is filled with the dial's lighting only; the hub and hands cover most of it.

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_re_au01_trace au0110n   # -> config/watches/orient-re-au0110n-trace.json
python3 -B -m pipeline.orient_re_au01_dial au0110n    # -> outputs/watches/orient-re-au0110n/dial_photo.jpg (regenerated, not committed)
```

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/orient-re-au0110n.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief, house method |
