# Reference plan: BREITLING Superocean Heritage Automatic 42 AB2010121B1A1 (42 mm steel, black dial, steel mesh bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Follower of the Breitling template ([Superocean 42 rubber](../breitling-superocean-42-a17375211b1s1/REFERENCE_PLAN.md)); different dial / hands (vintage styling) and a steel mesh bracelet.

## Target asset

Front relief GLB `models/watches/breitling-ab2010121b1a1.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright render, transparent background (soft alpha rim, no drop shadow), 1024 x 1024 WebP | `breitling-ab2010121b1a1_original.webp` | HAVE, the only source (kept untouched) |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Superocean 42 / Black Bay builds, back flat |

## Measured on this photo (continuous px of the 1024 x 1024 frame)

| Item | Result |
| --- | --- |
| Anchor | coin-edge tooth tips (silhouette radius 240.5 px, valleys 235.5) = 42 mm / 2 -> 11.4524 px/mm |
| Pivot / ring centre | hands cross at (511.2, 482.7); bezel rings centred (511.2, 485.5) (circle fit to the ceramic outer edge, rms 0.25 px), i.e. 2.8 px lower (camera tilt) -> `ring_centre_mm` [0, -0.245] |
| Rings (r px about the ring centre) | dial_flat 171, crystal_edge 180.5, bezel_in 181, insert_out 220 (dark gap 220..226), coin ring 226.9..240.5 |
| Crown | no guards; body x 748..798, y 445..523.5, fluted to x 782.5, narrower rounded cap |
| Lugs | tops y 197, bottoms y 775 |
| Bracelet | steel mesh to the alpha ends (top y 105, bottom y 918); polished end-link bar between the lugs (top y 209..250, bottom y 721..763); mesh 391..632 px wide at the lugs, narrowing to ~410..618 (top end) |
| Hands (about 10:08:35) | hour 304.2 deg arrow head (length 122 px, barbs half width 23.4), minute 47.9 deg leaf (153 px, half width 11.5), seconds 222.4 deg needle (164 px) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | own copy `pipeline/steps/watch_breitling_superoceanheritage42.py` of the Superocean 42 step with the column-driven bracelet of the Black Bay 58 step |
| Prep | `pipeline/breitling_superoceanheritage42_prep.py` (copy of the Superocean 42 prep, model names only) |
| Comparison frame | 2048 px square, camera 22.9048 px/mm centred on the pivot (2x photo pivot (1022.4, 965.4) at (1024, 1024)), `config/presets/watch_kit_white_front_breitling_superoceanheritage42.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.breitling_superoceanheritage42_prep   # -> 2x reference, config/watches/breitling-superoceanheritage42-ab2010121b1a1-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
