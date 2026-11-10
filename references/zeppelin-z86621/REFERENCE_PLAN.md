# Reference plan: Zeppelin New Captain's Line Z86621 (steel, white dial, 24 h and small seconds sub-dials, brown leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 delivered 2026-11-10 (`models/watches/zeppelin-z86621.glb`).

Own construction; scripts follow [Z96645](../zeppelin-z96645/REFERENCE_PLAN.md) (one off-axis photo, straightened first).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, slightly off axis, 2000 × 3208 | `front_2000x3208.png` | HAVE, only photo; straightened |
| 2 | Back, 3/4 | none | Not available (Irsyad); not needed for the flat-backed front asset |
| 3 | Spec sheet | `spec_sheet.png` | HAVE |

`pipeline/zeppelin_z86621_rectify.py` maps the inner ends of 10 black hour bars (3 and 9 are cut by glare) to one circle
with a homography (median residual 1.81 px, max 2.8 px). The photo was only about 1 % off round.

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **43 mm** (spec sheet). Check: the strap reads 21.0-21.3 mm (listing 22 mm; a 22 mm strap would mean a 44.4 mm case) |
| Movement | Listing says "chronograph"; the photo shows a 24 h sub-dial at 9 and small seconds at 4-5, no pushers: built from the photo |
| Origin | Dial centre (hour-bar centre); the raised centre hub is seen 0.13 mm off it, the model puts it on the centre |
| Case, lugs, crown | Round polished case with a thin polished bezel (19.8-20.9 mm), plain polished lugs from the left and bottom right silhouette (the top right lug sits behind the strap), ends cut square; large fluted crown with a domed end |
| Hands | Faceted dark steel dauphine hour and minute hands: waist at the hub, widest point and tip measured from the photo (narrower side, so print touching an edge does not widen them); grey collet and cap with a polished ring; black sub-dial needles on black hubs with steel pins |
| Dial | White; print, sub-dial rings, gold 24 h batons, logo and rehaut stay in the dial map; hands and hubs removed (smooth blur fill) |
| Strap | Brown leather, 21.3 mm; map straightened from the photo's 12 o'clock strap, used on both sides |

## Known gaps

- The hand zones in the dial map are smooth (no dial grain); the 3D hands cover them from the front.
- Crystal glare at 3 and 9 o'clock on the minute track stays in the dial map.
- The strap map covers 22.8-36.2 mm from the centre; past that the curled end repeats the last row. The embossed Zeppelin logo on the 6 o'clock strap and the keeper loop are not reproduced.
- The lug's inner flat top and outer rounded flank are one slab with a wide edge radius.

## Phase 1 outputs

```sh
python3 -B -m pipeline.zeppelin_z86621_rectify   # -> outputs/watches/zeppelin-z86621/front_rectified.png (regenerated, not committed)
python3 -B -m pipeline.zeppelin_z86621_trace     # -> config/watches/zeppelin-z86621-trace.json
python3 -B -m pipeline.zeppelin_z86621_dial      # -> outputs/watches/zeppelin-z86621/dial_photo.jpg, strap_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 39.9446 px/mm from the 43 mm case (left and right edge circles) |
| Rings | hour bars (inner end) 17.57 mm, dial edge 19.48 mm, bezel inner 19.78 mm |
| Lugs | outer edge 15.47 mm, strap edge 10.64 mm, tips 24.36 mm |
| Hands | hour 305.5°, 12.23 mm; minute 57.2°, 16.04 mm; 24 h 332.8°, 4.68 mm; seconds 147.9°, 4.53 mm |
| Sub-dials | 24 h at (-6.41, 0.28) mm; small seconds at (3.73, -4.63) mm |
| Crown | radius 3.15 mm, flutes 20.8-24.3 mm, dome to 25.5 mm |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/zeppelin-z86621.json --force
```

| Date | Change |
| --- | --- |
| 2026-11-10 | Round 1: first build. Delivered as `models/watches/zeppelin-z86621.glb` (0.95 MB) |
