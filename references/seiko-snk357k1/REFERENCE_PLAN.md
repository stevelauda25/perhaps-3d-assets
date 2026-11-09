# Reference plan: Seiko 5 Automatic SNK357K1 (blue patterned dial, five-row steel bracelet)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Blue-dial version of the [SNK361K1](../seiko-snk361k1/REFERENCE_PLAN.md): same case, indices, hands, day-date and bracelet.

## Target asset

A front-facing GLB in `models/watches/seiko-snk357k1.glb`, built by the SNK361K1 step (`watch_seiko_snk361_front`): front relief, flat back, 2.5D depth; case, indices, hands, day-date frame, crown and bracelet as geometry; dial print and pattern from a map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 3236 × 6276 | `front_3236x6276.png` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | none | MISSING: heights reuse the SNK361K1 (SNK607K1) values |
| 3 | Back | none | not needed for the flat-backed front asset |

#1 is the same shoot size as the SNK361K1 photo: the case is 1385 px wide here and 1398 px there.

## Scale anchors

| Dimension | Value | Status |
| --- | --- | --- |
| Case diameter (without crown) | **38 mm** | spec sheet (Irsyad, 2026-11-09). The SNK361K1, same case, was set to 36 mm |
| Lug width | 16 mm listed | does not fit #1: the bracelet is 19.6 mm next to the case and 15.3 mm at the far end at 38 mm |
| Thickness | 11 mm listed | heights kept from the SNK361K1 spec |

## Part by part

As the SNK361K1, except:

| Part | This watch | Source |
| --- | --- | --- |
| Dial | Blue with a fine wave pattern (strongest in the upper half) | #1, map |
| Day-date | `MON 22` | #1, map |
| Hands | Posed as photographed, about 10:10:48 | #1 |
| Bracelet rows | 6.16 mm apart in this photo (SNK361K1: 5.42 mm at 36 mm) | #1 |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snk357_trace   # -> config/watches/seiko-snk357k1-trace.json
python3 -B -m pipeline.seiko_snk357_dial    # -> outputs/watches/seiko-snk357k1/dial_photo.jpg (regenerated, not committed)
```

Scale 72.91 px/mm from the 38 mm case flanks; origin = hand pivot (1591, 3134). Hands, bracelet columns, joints and crown are read from gridded crops of #1; day-date, logo, print and end link are the SNK361K1 points moved to #1 and checked on the overlay. No hand crosses the logo here, so the dial map keeps it as photographed.

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snk357k1.json --force   # build, GLB, white comparison render (overwrites outputs/jobs/seiko-snk357k1/)
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-09 | First front relief with the SNK361K1 step at 38 mm: SNK357K1 trace and blue dial map, house depth, glass, steel textures and 7 mm bracelet curl from the lug tips; 1.7 MB GLB, committed to `models/watches/seiko-snk357k1.glb` |

## Known gaps

- Only a front photo: case height, lug drop and crown length are the SNK607K1 values.
- 38 mm (spec sheet) disagrees with the SNK361K1 at 36 mm and with the listed 16 mm lug width.
- The seconds needle reads about 3 deg bent between tip and tail in #1; the tip angle is used.
