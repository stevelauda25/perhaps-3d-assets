# Reference plan: Seiko Presage Style60's SSA425J1 (black open-heart dial, 24-hour sub-dial, 4R39, three-column steel bracelet)

Written 2026-11-06 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photos and the listing supplied by Irsyad on 2026-11-06.

## Target asset

A front-facing GLB in `models/watches/seiko-ssa425j1.glb`, built like the other Seiko front reliefs: flat back, 2.5D depth, case/bezel/indices/hands/bracelet as geometry, dial print and bezel insert from one photo map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, nearly straight-on, transparent background, 2204 × 2204 | `front_2204.png` | HAVE, primary for everything |
| 2 | Slight 3/4 from the crown side, white | `three_quarter_2614.png` | HAVE: crown, lug tops, bracelet columns |
| 3 | Front, turned, white (dealer) | `dealer_front_2000x3160.png` | HAVE: full bracelet, hand colour on white |
| 4 | Back, side profile | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Listed | Measured at 40.8 mm (30.69 px/mm) |
| --- | --- | --- |
| Case diameter | **40.8 mm** (anchor) | bezel edge left of the hand pivot (1038, 1021) |
| Lug to lug | 47.0 mm | 47.25 mm (tips 23.4 mm at 12, 23.9 mm at 6) |
| Lug width | 20 mm (Style60's) | bracelet face 20.2 mm next to the lug tips |
| Thickness | 12.8 mm | heights in the spec fit it before the house depth scale |
| Bezel insert, crystal, dial flat | not listed | 20.14 / 17.79, 17.01, 14.50 mm radius |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case | Round, polished flank, thin steel lip outside the insert, polished inner ring to the crystal | #1, #2 |
| Bezel | Black insert with 60-minute numerals and bars in gold | photo map |
| Crystal | Box Hardlex: tall, flat top; its wall shows as a grey band between dial and bezel | #1, #2 |
| Lugs | Brushed tops, polished chamfer, from the case flank (y 14.25 mm) to the tips | #1 silhouette, #2 |
| Dial | Black; 24-hour sub-dial at 10 (radius 4.47 mm); open-heart aperture at 8 (radius 5.15 mm) showing the balance; minute track; lume pads inside each index | photo map |
| Indices | Applied polished batons with three ribs, 10.5–13.3 mm, 1.34 mm wide; wide triple at 12 (2.0 mm); 8 and 9 cut short by the aperture | #1 |
| Print | `SEIKO`, `PRESAGE AUTOMATIC`, `MADE IN JAPAN 4R39…` | photo map |
| Hands | Faceted sword hour and minute with cream lume and a polished tip; broad triangular tail on the hour hand; seconds needle with a paddle counterweight; small arrow hand on the 24-hour sub-dial | #1 |
| Crown | Fluted crown, 24 flutes, plain bevelled cap at 3 | #1, #2 |
| Bracelet | Three brushed columns; outer links from the lug tips, the centre column 1.5 mm nearer the case; pitch 6.6 mm; centre 0.49 of the width | #1, #2 |
| End link | Between the lugs from under the case: outer columns to the lug tips, centre 1.5 mm shorter | #1 |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | 40.8 mm case from the listing; lug to lug 47.0 mm and lug width 20 mm check it |
| Heights | Estimated for 12.8 mm with a box crystal (no side view) |
| Hand pose | The pose in #1 (about 10:09, 24-hour hand at 22 h) so the comparison render lines up |
| Open heart | Flat in the dial map (movement not modelled); the photo's seconds needle stays in the map over the movement, under the 3D needle |
| Bracelet curve | House curl: 7 mm radius from the lug tips, end_y = tip + 15.4 mm |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_ssa425_trace   # -> config/watches/seiko-ssa425j1-trace.json
python3 -B -m pipeline.seiko_ssa425_dial    # -> outputs/watches/seiko-ssa425j1/dial_photo.jpg (regenerated, not committed)
```

The map runs out to the bezel insert. Hand zones: inside the minute track the black dial gets the surrounding lighting only; the
track is rotated in 6° steps about the pivot; the sub-dial, ring included, is rotated in 45° steps about its own pivot.

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-ssa425j1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-06 | First front relief: photo-mapped dial and bezel insert, three-rib indices, sword hands with lume, three-column bracelet with the house curl |

## Known gaps and artefacts

- The photo is turned slightly: right side walls of the bracelet, lugs and case show; the build is symmetric.
- Open-heart movement and sub-dial recess are flat in the map.
- Under the hour and minute hands the dial map is plain lit black; it is hidden by the hands at the photo's pose.
- Case and crystal heights are estimates.
