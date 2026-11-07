# Reference plan: BREITLING Superocean Automatic 42 A17375211B1S1 (42 mm steel, black dial, black rubber strap)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). First Breitling asset: it sets the Breitling approach (structure of the [Black Bay 54 rubber-strap build](../tudor-black-bay-54-m79000n-0002/REFERENCE_PLAN.md), Breitling measurements).

## Target asset

Front relief GLB `models/watches/breitling-a17375211b1s1.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, flat front-matched rubber strap.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright render, transparent background (soft alpha rim, no drop shadow), 1024 x 1024 WebP | `breitling-a17375211b1s1_original.webp` | HAVE, the only source (kept untouched) |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Black Bay 54 build, back flat |

## Measured on this photo (continuous px of the 1024 x 1024 frame)

| Item | Result |
| --- | --- |
| Alpha bbox | x 280..782, y 104..919 (strap ends at top y 104, bottom y 919; crown to x 782) |
| Anchor | bezel (coin ring outer edge) circle fit to the left silhouette: centre (512.06, 473.3), r 232.15 px = 42 mm / 2 -> 11.0548 px/mm |
| Pivot | hour and minute axes cross at (512.0, 474.5) (hand height); hub pin hole seen 1.7 px lower, rings 0..1 px higher / lower (camera tilt parallax); `ring_centre_mm` [0, 0.06] |
| Rings (r px) | dial_flat 175, crystal_edge 184, bezel_in 184.5, insert_out 220, bezel_out 232.15 |
| Bezel | black-to-grey ceramic gradient (the 45 / 15 / 30 numerals and minute ticks are print in the photo) inside a steel coin-edge ring |
| Crown | box x 742..783, y 434..519 (centre 2 px below the pivot row), fluted, chamfered cap; guards belong to the case silhouette |
| Lugs | tops y 218, bottoms y 734; strap width 393..628 at the lugs (21.3 mm) |
| Strap | black rubber: textured (honeycomb) side sections, smooth centre section, seams x 469/553 (top end) to 458/565 (lug top), 457/565 (lug bottom) to 465/555 (bottom end); flares toward the lugs |
| Hands (about 10:08:35) | hour 303.0 deg bar lume (half width 10 px, length 81.5 px), minute 46.6 deg thin shaft with a 36 x 35 px lume block, tip 137.5 px, seconds 222.5 deg white shaft + red-ringed lollipop (centre 93.1 px) + thin red needle to 137.6 px |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | own copy `pipeline/steps/watch_breitling_superocean42.py` of the BB54 rubber step plus `ring_centre_mm` support |
| Prep | `pipeline/breitling_superocean42_prep.py` (copy of the Pelagos 39 prep; WebP source, bezel-circle anchor, continuous px, sub-pixel dial crop) |
| Comparison frame | 2048 px square, camera 22.1096 px/mm centred on the pivot (2x photo pivot (1024, 949) at (1024, 1024)), `config/presets/watch_kit_white_front_breitling_superocean42.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.breitling_superocean42_prep   # -> 2x reference, config/watches/breitling-superocean42-a17375211b1s1-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
