# Reference plan: Seiko 5 Automatic SNKM87K1 (black dial, chapter ring, steel bracelet)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Build structure follows the [SUR419P1](../seiko-sur419p1/REFERENCE_PLAN.md) (faceted batons and hands, three-column bracelet).

## Target asset

A front-facing GLB in `models/watches/seiko-snkm87k1.glb`: front relief, flat back, 2.5D depth, case/indices/hands/day-date frame/crown/bracelet as geometry, dial print from a map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 1081 × 1500 | `front_1081x1500.jpg` | HAVE, primary for plan sizes and the dial map; below the 2000 px target (22 px/mm), so the dial print is softer than on the SNK builds |
| 2 | 3/4 from the crown side, 2000 × 2400 | `three_quarter_2000x2400.png` | HAVE: bracelet column split, case side |
| 3 | Back | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Value | Status |
| --- | --- | --- |
| Case diameter (without crown) | **43 mm** | listings; not yet confirmed by Irsyad |
| Lug gap (end link width) | 20.92 mm measured | listed band 21 mm: agrees |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case, lugs, crown | Round case, wide sloped polished bezel, lugs leave the case at 15 mm, tips at 24.5 / 25.4 mm; knurled crown at 3 | #1, #2; heights from SNK369K1 x1.09 (listed 12 mm thick) |
| Crystal | Flat, inside the bezel at 18.0 mm | #1 |
| Dial | Black, fine concentric pattern, flat to 13.7 mm; sloped black chapter ring to 18.0 mm with white minute ticks and 5–60 numerals | #1, map |
| Hour indices | Faceted polished batons 9.3–13.5 mm, 1.08 mm wide; double at 12 (two 0.99 mm bars); none at 3; a white lume block (1.44 × 0.59 mm) at every hour on the chapter ring edge | #1 |
| Day-date | `SUN 5`, polished frame 8.0 × 3.0 mm | #1 |
| Hands | Faceted polished dauphine hour (8.37 mm) and minute (13.10 mm) with pointed counterweights and a white lume strip down the middle; needle seconds hand (13.72 mm) with a paddle tail | #1, #2 |
| Bracelet | Three columns, brushed with polished edges; centre column half the width; centre joints 1.8 mm further from the case than the outer ones; rows 6.75 mm | #1 (6 o'clock side), #2 |
| End link | Solid between the lugs (20.9 mm), centre part 1.8 mm longer | #1 |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snkm87_trace   # -> config/watches/seiko-snkm87k1-trace.json
python3 -B -m pipeline.seiko_snkm87_dial    # -> outputs/watches/seiko-snkm87k1/dial_photo.jpg (regenerated, not committed)
```

Scale 22.23 px/mm from the left case flank at 43 mm; origin = hand pivot (500, 690). Hands read 10:08:42. The dial map fills hand pixels from the same radius a whole number of minutes (6°) round, keeping the fine pattern and taking the shade of the dial around it.

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snkm87k1.json --force   # build, GLB, white comparison render (overwrites outputs/jobs/seiko-snkm87k1/)
```

| Date | Change |
| --- | --- |
| 2026-11-09 | First front relief with the house values (2.5D depth 0.35, 7 mm curl from the lug tips, glass, steel textures) |
| 2026-11-09 | Wider dauphine blades and tails, larger crown (5.7 mm, from the front photo), white lume strip along the hour and minute hands (3/4 photo); 1.1 MB GLB, committed to `models/watches/seiko-snkm87k1.glb` |

## Known gaps

- The front photo is 1081 px wide: dial print at 22 px/mm.
- 43 mm is from listings; confirm with Irsyad.
- The front photo shows the bracelet columns off-centre (perspective); the centre column width is a compromise between #1 (0.59) and #2 (0.48).
