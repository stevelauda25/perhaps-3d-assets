# Reference plan: Seiko 5 Automatic SNK371K1 (blue dial, yellow track, steel bracelet)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Blue-dial version of the [SNK369K1](../seiko-snk369k1/REFERENCE_PLAN.md): same case, track layout, hand shapes and seven-part bracelet.

## Target asset

A front-facing GLB in `models/watches/seiko-snk371k1.glb`, built by the SNK369K1 step (`watch_seiko_snk369`): front relief, flat back, 2.5D depth; case, indices, hands, day-date frame, crown and bracelet as geometry; dial print and track from a map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 3096 × 6154 | `front_3096x6154.png` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | none | MISSING: heights reuse the SNK369K1 values |
| 3 | Back | none | not needed for the flat-backed front asset |

#1 is taken slightly from the crown side, like the SNK369K1 photo: scale and silhouette use the left side.

## Scale anchors

| Dimension | Value | Status |
| --- | --- | --- |
| Case diameter (without crown) | **37 mm** | spec sheet (Irsyad, 2026-11-09) |
| Lug gap (end link width) | 18.36 mm measured | listed lug width 18 mm: agrees within 2 % |
| Thickness | 11 mm listed | heights kept from the SNK369K1 spec |

## Part by part

As the SNK369K1, except:

| Part | This watch | Source |
| --- | --- | --- |
| Dial | Blue sunburst; yellow and grey track from 12 to 4 starting at 9.62 mm, blocks every 6 deg; minute numerals white, 60 to 20 in yellow | #1, map |
| Hour indices | Polished batons with a white lume fill, 9.6–13.3 mm, 0.98 mm wide; 1.97 mm at 12; none at 3 | #1 |
| Day-date | `WED 18`, black frame 8.6 × 3.4 mm | #1 |
| Hands | Hour: polished open arrow, lume head, dark slot between the shaft rails. Minute: polished stick, square tip, lume from 4.0 mm. Seconds: thin yellow needle, wider yellow tail. Polished hub ring, yellow cap, polished pin | #1 |
| Bracelet rows | 5.66 mm apart in this photo (SNK369K1: 6.94 mm) | #1 |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snk371_trace   # -> config/watches/seiko-snk371k1-trace.json
python3 -B -m pipeline.seiko_snk371_dial    # -> outputs/watches/seiko-snk371k1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 71.19 px/mm from the left case flank at 37 mm; origin = hand pivot (1556, 3036) |
| Hands (10:08:46) | hour 304.7°, 7.77 mm; minute 51.4°, 12.69 mm; seconds 277.8°, 12.65 mm, tail 4.84 mm |

The dial map fills hand pixels on the track (from 9.5 mm out) from one minute (6 deg) round, the outer minute ticks under the seconds needle the same way, and the plain blue dial with its own shade and grain. The 50, 45 and 10 beside the hands are kept as photographed.

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snk371k1.json --force   # build, GLB, white comparison render (overwrites outputs/jobs/seiko-snk371k1/)
```

| Date | Change |
| --- | --- |
| 2026-11-09 | First front relief with the SNK369K1 step and the house values (2.5D depth 0.35, 7 mm curl from the lug tips at 20.9 mm, glass, steel textures); 2.0 MB GLB, committed to `models/watches/seiko-snk371k1.glb` |

## Known gaps

- Only a front photo: case height, lug drop and crown length are the SNK369K1 values.
- The day-date frame reads black in #1 (SNK369K1: polished); built black.
- The outer edges of the narrow polished bracelet strip are faint in #1; read at ±364 px from the columns' centre.
