# Reference plan: Zeppelin 100 Jahre Chronograph Z8680M4 (steel, green dial, Milanese mesh bracelet)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 delivered 2026-11-09 (`models/watches/zeppelin-z8680m4.glb`).

Same case and dial layout as [Z7680MB2](../zeppelin-z7680mb2/REFERENCE_PLAN.md); the step is a copy of its step with a mesh bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front taken from the left (about 3/4), 3430 × 5390 | `front_3430x5390.png` | HAVE, only photo; straightened on the dial plane |
| 2 | Straight front, back | none | Case sizes from the Z7680MB2 straight photo (same case) |
| 3 | Spec sheet | `spec_sheet.png` | HAVE |

`pipeline/zeppelin_z8680m4_rectify.py` maps six lume dots, the hand pivot and the three sub-dial hubs to their Z7680MB2
positions with a homography (75 px/mm; median residual 0.12 mm, max 0.28 mm at the pivot).

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **42 mm** (listing; same case as Z7680MB2). The listing's 11 mm thickness differs from Z7680MB2's 13 mm; heights kept from Z7680MB2 |
| Case, lugs, crown, pushers | From the Z7680MB2 trace: this photo is taken from the side, so its case outline is skewed |
| Origin | Hand pivot in the straightened photo (1781, 2893) |
| Hands | Steel lollipop hour and minute hands with lume leaf and disc, white chronograph needle with a long tail, white sub-dial hands: lozenge with a tail disc at 9, needle with a tail disc at 3, two alarm hands at 6 (the short one with a counterweight); posed at the photo's time |
| Dial | Green; print, scales, sub-dials, lume dots, date and airship logo stay in the dial map; hands and hubs removed by a normalised blur fill |
| Bracelet | As photographed: solid brushed end piece between the lugs (polished edges) to the lug tips, then Milanese mesh 21.1 mm wide with the house 7 mm curl. Mesh map: a 3.68 mm band of the 6 o'clock mesh (two pattern repeats), tiled along the bracelet; the 12 o'clock side uses the same map turned round |
| Branch, file | `zeppelin` branch; `models/watches/zeppelin-z8680m4.glb` |

## Known gaps

- The left part of the telemeter ring (7-11 o'clock) shows the bezel's inner wall seen from the side, so it reads grey there.
- The hand zones in the dial map are smooth (no sunray); the 3D hands cover them from the front.
- The mesh is a flat strip with a photo map; no real weave relief.

## Phase 1 outputs

```sh
python3 -B -m pipeline.zeppelin_z8680m4_rectify   # -> outputs/watches/zeppelin-z8680m4/front_rectified.png (regenerated, not committed)
python3 -B -m pipeline.zeppelin_z8680m4_trace     # -> config/watches/zeppelin-z8680m4-trace.json
python3 -B -m pipeline.zeppelin_z8680m4_dial      # -> outputs/watches/zeppelin-z8680m4/dial_photo.jpg, mesh_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 75 px/mm (straightened photo) |
| Hands | hour 305.3°, 11.64 mm; minute 62.5°, 15.66 mm; chronograph 359.4°, 16.24 mm |
| Mesh | 20.4 mm wide in the photo (bracelet 21.1 mm used); pattern repeat 1.84 mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/zeppelin-z8680m4.json --force
```

| Date | Change |
| --- | --- |
| 2026-11-09 | Round 1: first build. Delivered as `models/watches/zeppelin-z8680m4.glb` (2.04 MB) |
