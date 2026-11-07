# Reference plan: PATEK PHILIPPE Calatrava Weekly Calendar 5212A (40 mm steel, cream dial, brown leather strap)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Follower of the **Calatrava 6007G template** ([blue baseline](../patek-calatrava-6007g-blue/baseline/BASELINE.md)), with a new prep copy and spec because the camera, bezel, crown, hands and strap all differ.

## Target asset

Front relief GLB `models/watches/patek-5212a.glb` (tracker rule: lowercase brand-SKU), flat back, 2.5D depth, layered parts (case, stepped bezel, crystal, dial plate, applied indices, hands at different heights, crown, leather strap), front-locked.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background (faint drop shadow below the strap), 1920 x 2691 PNG | `patek-5212a_original.png` | HAVE, the only source (untouched, worked on natively) |
| 2 | Side / back / crown close-up | none | not available; heights are the 6007G build's estimates, back flat |

## Registration

The 5212A photo does NOT share the 6007G camera: the case circle is centre (957.85, 1378.20) r 630.46 px (31.523 px/mm) against (956.50, 1271.23) r 626.35 (31.3175 px/mm), the pivot (hub cap centre) is (958.3, 1368.7); so the measure file is new and the kit preset is a copy with 23.6423 px/mm (0.75 x the native photo). Camera tilt: the bezel / dial circles sit 3 to 6 px above the case circle centre (ring centre (958.5, 1375.5)).

## Decisions

| Decision | Answer |
| --- | --- |
| Step | reused read-only: `pipeline/steps/watch_patek_calatrava6007g.py` (spec driven, no code change: the stepped bezel is a `bezel.profile_rz_mm`, all hands, red tips and indices are `hands.polygons`) |
| Prep | copy `pipeline/patek_calatrava5212a_prep.py` (names, folder) and `pipeline/patek_calatrava5212a_polys.py` (hand / index polygons from the photo into the spec) |
| Kit preset | `config/presets/watch_kit_white_front_patek_calatrava5212a.json` (own scale, pivot at the frame centre) |
| Comparison frame | 2048 px, 23.6423 px/mm = 0.75 x the native photo: photo pixel (x, y) at ((x - 958.3) * 0.75 + 1024, (y - 1368.7) * 0.75 + 1024) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.patek_calatrava5212a_prep 5212a    # -> config/watches/patek-calatrava5212a-5212a-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
python3 -B -m pipeline.patek_calatrava5212a_polys 5212a   # -> hands.polygons in config/watches/patek-calatrava5212a-5212a.json
```
