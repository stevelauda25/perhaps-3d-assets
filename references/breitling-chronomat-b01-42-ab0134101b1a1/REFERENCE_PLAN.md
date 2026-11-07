# Reference plan: BREITLING Chronomat B01 42 AB0134101B1A1 (42 mm steel, black dial, steel rouleaux bracelet, chronograph)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). New model within the Breitling approach ([Superocean 42 rubber](../breitling-superocean-42-a17375211b1s1/REFERENCE_PLAN.md), [Superocean Heritage 42](../breitling-superocean-heritage-42-ab2010121b1a1/REFERENCE_PLAN.md)); chronograph parts after the [Tudor Black Bay Chrono](../tudor-black-bay-chrono-m79360n-0013/REFERENCE_PLAN.md).

## Target asset

Front relief GLB `models/watches/breitling-ab0134101b1a1.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright render, transparent background (soft alpha rim, no drop shadow), 1024 x 1024 WebP | `breitling-ab0134101b1a1_original.webp` | HAVE, the only source (kept untouched) |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Superocean / Black Bay Chrono builds, back flat |

## Measured on this photo (continuous px of the 1024 x 1024 frame)

| Item | Result |
| --- | --- |
| Anchor | circle fitted to the left silhouette of the round case / bezel (rows 390..555, 570+; the 45 rider tab sticks out 2.8 px at row 480): r 227.7 px = 21 mm -> 10.8429 px/mm |
| Pivot / ring centre | hour (304.2 deg) and minute (48.8 deg) centre lines cross at (512.2, 477.5); the red seconds needle is the line x 512.0; bezel / case circle centred (511.9, 479.2), 1.7 px lower (camera tilt) -> `ring_centre_mm` [-0.028, -0.157] |
| Rings (r px about the ring centre) | dial_flat 177, crystal_edge 178.8, bezel_in 179.3, insert_out 218 (polished flange with rider tabs 15 / 30 / 45 / 60 and ticks in the photo), outer chamfer 218..227.7 |
| Hands (10:08:00, chrono at 0) | hour 304.2 deg bar with chamfered tip (110 px, half width 6.3 px), minute 48.8 deg (152.5 px, half width 6.8..7.3 px), red chronograph seconds 0 deg (152 px, needle half width 2 px, kite lume window s 117..147); three sub-dial hands (white bars) and hubs at (427.1, 479.7), (595.7, 479.3), (511.9, 564.0) |
| Crown / pushers | barrel crown x 740..797, y 448..518 (centre 483); rectangular pushers radial from (512.2, 483) at +-30 deg, end faces 272.3 px away (silhouette scan along the axis), 54 px wide; guard shoulders (x up to 767) stay in the alpha silhouette, pusher / crown rows take straight shoulder lines |
| Lugs | tops y 219, bottoms y 749.5 |
| Bracelet | rouleaux: five-segment rows (outer, polished, centre, polished, outer) alternate with full-width tube rows; top: 5-seg 213.5..246.8 (between the lugs), tube, 5-seg, tube, 5-seg, cap strip to y 101.5; bottom: 5-seg 717.5..752.5, tube, 5-seg, tube, 5-seg, tube, end strip to y 919.5; alpha ends y 102 / 920 |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | own copy `pipeline/steps/watch_breitling_chronomat42.py` (Tudor Black Bay Chrono step for hands / sub-dials / pushers, Breitling bezel and ring centre, bracelet with full-width rows) |
| Prep | `pipeline/breitling_chronomat42_prep.py` (copy of the Heritage prep, plus right-edge override lines for the pusher / crown rows) |
| Comparison frame | 2048 px square, camera 21.6857 px/mm centred on the pivot (2x photo pivot (1024.4, 955.0) at (1024, 1024)), `config/presets/watch_kit_white_front_breitling_chronomat42.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.breitling_chronomat42_prep   # -> 2x reference, config/watches/breitling-chronomat42-ab0134101b1a1-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
