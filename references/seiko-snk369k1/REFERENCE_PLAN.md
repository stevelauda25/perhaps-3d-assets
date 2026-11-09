# Reference plan: Seiko 5 Automatic SNK369K1 (white dial, red track, steel bracelet)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Same SNK case family as the [SNK381K1](../seiko-snk381k1/REFERENCE_PLAN.md); heights are taken from that build.

## Target asset

A front-facing GLB in `models/watches/seiko-snk369k1.glb`, built like `seiko-snk361k1.glb`: front relief, flat back, 2.5D depth, case/bezel/indices/hands/day-date frame/crown/bracelet as geometry, dial print from a map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 2000 × 3708 | `front_2000x3708.png` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | none | MISSING: no listing has one; heights reuse the SNK607K1/SNK381K1 values |
| 3 | Back | none | not needed for the flat-backed front asset |

#1 is taken slightly from the crown side: the right case flank and the right bracelet edge also show their side faces. Scale and silhouette use the left side.

## Scale anchors

| Dimension | Value | Status |
| --- | --- | --- |
| Case diameter (without crown) | **37 mm** | listings; not yet confirmed by Irsyad (SNK361K1 was set to 36 mm) |
| Lug gap (end link width) | 18.18 mm measured | listed band 18 mm: agrees within 1 % |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case, lugs, crown | SNK case: wide sloped polished bezel, brushed lug tops, knurled crown at 4 o'clock (112°); lugs leave the case at 8.5 mm, tips at 21.1 mm | #1; heights from SNK381K1 |
| Crystal | Flat, inside a dark gasket ring at 14.4–15.3 mm | #1 |
| Dial | White; edge 13.8 mm, rehaut to 14.4 mm | #1 |
| Print | Minute numerals 5–60 (red 60–20, black 25–55), minute ticks, red and grey track from 12 to 4, `SEIKO`, 5 shield, `AUTOMATIC 21 JEWELS`: all in the dial map | #1 |
| Hour indices | Applied polished batons with a pale lume fill, 9.6–13.3 mm, 1.15 mm wide; 2.1 mm wide at 12; none at 3 | #1 |
| Day-date | `MON 22`, polished frame 8.4 × 2.7 mm | #1 |
| Hands | Hour: black open arrow, lume head, white between the shaft rails. Minute: black stick with a square tip and a lume window. Seconds: thin red needle, wide red tail. Polished hub ring, red cap, polished pin | #1 |
| Bracelet | Seven parts per row: brushed outer links, narrow polished strip, polished mid links half a row offset, brushed centre link; rows 6.9 mm apart | #1 |
| End link | Solid, same columns, between the lugs (18.2 mm) from the case to the lug tips | #1 |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snk369_trace   # -> config/watches/seiko-snk369k1-trace.json
python3 -B -m pipeline.seiko_snk369_dial    # -> outputs/watches/seiko-snk369k1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 43.46 px/mm from the left case flank at 37 mm; origin = hand pivot (991, 1819) |
| Hands (10:08:10) | hour 304.2°, 7.90 mm; minute 45.6°, 12.69 mm; seconds 57.8°, 13.13 mm, tail 4.79 mm |

Hands, indices, day-date, crown and bracelet columns are read from gridded crops (`MANUAL_PX`, ±5 px ≈ ±0.1 mm). The dial map fills hand pixels on the track from the same spot one hour round (track blocks and indices repeat every 30°), the white dial with its own shade and grain, and redraws the `1` of the red `10`, which lies under the seconds hand.

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snk369k1.json --force   # build, GLB, white comparison render (overwrites outputs/jobs/seiko-snk369k1/)
```

| Date | Change |
| --- | --- |
| 2026-11-09 | First front relief with the house values (2.5D depth 0.35, 7 mm curl from the lug tips, glass, steel textures); 1.4 MB GLB, committed to `models/watches/seiko-snk369k1.glb` |

## Known gaps

- Only a front photo: case height, lug drop and crown length are the SNK607K1/SNK381K1 values.
- 37 mm is from listings; confirm with Irsyad.
- The seconds hand tip is lost against the red track; its length is read where the track begins.
