# Reference plan: Seiko 5 Sports SNZB24J1 (two-tone, white dial, steel and gold bracelet)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Same case as
[SNZB26J1](../seiko-snzb26j1/); the photo is from the same psbwatches shoot with the same framing.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, 2048 × 2048 (about 26 px/mm) | `front_psb_2048.jpg` | HAVE, primary for everything |
| 1b | Front, turned about 15° toward the crown, 2976 × 5040 | `front_turned_2976x5040.png` | HAVE (Irsyad): sharper dial; colour check, not traced |
| 2 | Side from the crown | `side_crown_mygiftstop_2000.jpg` | HAVE: bezel and case height |
| 3 | Back | `back_mygiftstop_2000.jpg` | not needed for a front relief |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | **40 mm across the knurled bezel skirt**, as SNZB26J1 (same case). Listings for SNZB24J1 say 39 mm (one 40 mm): to confirm with the owner |
| Bezel position | At zero as photographed: pip at 12, triangles at 3, 6, 9 |
| Two-tone | Steel case, bezel top and bracelet; gold crystal ring, skirt, pads, indices, hands, crown, day-date frame and bracelet stripes |
| Bezel print | Numerals and triangles traced from the photo as black geometry; pip frame and lume dot read from gridded crops |

## Parts

| Part | True shape | Source |
| --- | --- | --- |
| Case | Round under the bezel; polished lugs either side of the bracelet | #1 |
| Bezel | Flat satin steel ring with black 5-55 numerals, gold knurled skirt, raised gold pads at 12/3/6/9 (black-framed lume pip at 12, black triangles at 3, 6, 9), gold sloped ring round the crystal | #1, #2 |
| Dial | White with a radial sunburst and fine minute track; `SPORTS`, `WATER 100M RESIST`, `AUTOMATIC`, `23 JEWELS`, small print at 6: dial map | #1 |
| Indices | Faceted gold batons with a pointed outer end, wider at 6 and 9, double baton at 12, none at 3 | #1 |
| Logo | Applied gold `SEIKO` and 5 shield (fitted from the SNZ450J1 trace) | #1 |
| Day-date | `MON 22`, wide gold frame | #1 |
| Hands | Gold sword hour and minute with lume, needle seconds with a lume disc on the tail; 10:09:56 | #1 |
| Crown | Gold, fluted, at 3 | #1 |
| Bracelet | Three columns: steel outer links, steel centre links with a gold stripe either side; centre links end in a shallow chevron | #1 |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snzb24_trace   # -> config/watches/seiko-snzb24j1-trace.json
python3 -B -m pipeline.seiko_snzb24_dial    # -> outputs/watches/seiko-snzb24j1/dial_photo.jpg (regenerated, not committed)
```

Scale 26.3 px/mm; origin = middle of the crystal ring (977, 943), hub on it. Lug tip (first outer joint) 23.29 mm, row
pitch 7.22 mm, centre joints 0.9 of a row past the outer ones.

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snzb24j1.json --force   # build, GLB, white comparison render (overwrites outputs/jobs/seiko-snzb24j1/)
```

| Date | Change |
| --- | --- |
| 2026-11-09 | First front relief with the house values (2.5D depth 0.35, 7 mm curl from the lug tips, glass, steel textures); two-tone materials per part; 4.6 MB GLB, waiting for designer review |
| 2026-11-09 | Round 2 (Irsyad): bezel numerals turned to their exact 5-minute angles and centred in the band; pad triangles at 3, 6, 9 rebuilt as filled triangles centred on the pads; stray mark beside the pip removed |

## Known gaps

- Scale: 40 mm (SNZB26J1 spec sheet) against 39 mm in most SNZB24J1 listings.
- The gold hands are faint on the white dial: angles read on a yellowness map; the minute hand lies over the 2 o'clock index, its length is taken from SNZB26J1.
- The centre links' chevron ends are modelled square; heights are the SNZB26J1 values, not measured.
