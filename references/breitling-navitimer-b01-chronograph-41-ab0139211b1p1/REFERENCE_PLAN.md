# Reference plan: BREITLING Navitimer B01 Chronograph 41 AB0139211B1P1 (41 mm steel, black dial, silver sub-dials, black leather strap)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Third Breitling asset: Superocean 42 structure ([baseline](../breitling-superocean-42-a17375211b1s1/baseline/BASELINE.md)) plus the chronograph parts of the [Black Bay Chrono](../tudor-black-bay-chrono-m79360n-0013/baseline/BASELINE.md) (pushers, sub-dial needles and hubs).

## Target asset

Front relief GLB `models/watches/breitling-ab0139211b1p1.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched leather strap.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright render, transparent background (soft alpha rim, no drop shadow), 1024 x 1024 WebP | `breitling-ab0139211b1p1_original.webp` | HAVE, the only source (kept untouched) |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Superocean 42 build, back flat |

## Measured on this photo (continuous px of the 1024 x 1024 frame; details in `config/watches/breitling-navitimer41-ab0139211b1p1-measure.json`)

| Item | Result |
| --- | --- |
| Anchor | circle fit to the coin-edge tooth tips on the left silhouette: centre (512.12, 470.74), r 222.95 px = 41 mm / 2 -> 10.8756 px/mm; 56 teeth, tips 223.0 / valleys 218.9 px |
| Pivot | hub disc centre and hour / minute centre-line crossing (513.07, 469.75); rings about (512.12, 470.74) (`ring_centre_mm` [-0.087, -0.091]) |
| Rings (r px about the ring centre) | dial_flat 172.0, crystal_edge / bezel_in 173.4, insert_out 210.0 (end of the white slide-rule ring), bezel_out 222.95 (tips) |
| Bezel | fixed steel bezel, two slide-rule scales (print only in the projected photo), coin edge |
| Crown / pushers | crown box x 731..765.5, y 433..509 (7.0 mm), 16 flutes, no guards; pushers radial at +-30 deg, end faces 23.59 mm from (513.07, 470.6), cap diameter 4.0 mm |
| Lugs / strap | lug tops y 220, bottoms y 721; strap 392..632 at the lugs (22 mm), rounded ends at y 103 / 920 |
| Hands (about 10:08:35) | hour 303.93 deg (bar, 8.97 mm), minute 47.91 deg (12.97 mm), red chrono seconds 0 deg (13.6 mm, tail 4.0 mm), three sub-dial needles with ball hubs |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | own copy `pipeline/steps/watch_breitling_navitimer41.py` of the Superocean 42 step (coin-edge teeth, pushers, sub-dial polygons / discs, hand offset, leather strap kind) |
| Prep | `pipeline/breitling_navitimer41_prep.py` (copy of the Superocean 42 prep; several mirror-row ranges about the bezel circle centre) |
| Comparison frame | 2048 px square, camera 21.7512 px/mm centred on the pivot (2x photo pivot (1026.14, 939.5) at (1024, 1024)), `config/presets/watch_kit_white_front_breitling_navitimer41.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.breitling_navitimer41_prep   # -> 2x reference, config/watches/breitling-navitimer41-ab0139211b1p1-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
