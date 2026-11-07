# Reference plan: PATEK PHILIPPE Calatrava 6007G blue (40 mm white gold, black / blue dial, black leather strap with blue stitching)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). First Patek Philippe asset and the **Calatrava 6007G template** (the red variant, row 81, follows it): Navitimer structure ([baseline](../breitling-navitimer-b01-chronograph-41-ab0139211b1p1/baseline/BASELINE.md)) minus chronograph parts, with a smooth polished bezel and a free-polygon seconds hand.

## Target asset

Front relief GLB `models/watches/patek-6007g-blue.glb` (tracker rule: lowercase brand-SKU, variant appended because the SKU repeats), flat back, 2.5D depth, flat front-matched leather strap.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background (faint drop shadow below the strap), 1920 x 2691 PNG | `patek-6007g-blue_original.png` | HAVE, the only source (kept untouched, worked on natively) |
| 2 | Side / back / crown close-up | none | not available; heights are estimates (no side view), back flat |

## Measured on this photo (continuous native px; details in `config/watches/patek-calatrava6007g-6007g-blue-measure.json`)

| Item | Result |
| --- | --- |
| Anchor | circle through the case silhouette (crown rows excluded): centre (956.50, 1271.23), r 626.35 px = 40 mm / 2 -> 31.3175 px/mm |
| Pivot | hub disc centre of the blue seconds hand (960.0, 1258.3); bezel / crystal / dial circles about (956.9, 1256.9) (`ring_centre_mm` [-0.099, 0.045]) |
| Rings (r px about the ring centre) | dial_flat 487, crystal_edge / bezel_in 494.7, bezel_out 608 (polished domed bezel, no teeth) |
| Crown | box x 1577..1657, y 1189.5..1377 (5.99 mm), about 20 flutes, rounded cap, no guards; no pushers |
| Lugs / strap | lug tops y 547.5, bottoms y 2052; strap 21.5 mm at the lugs, rounded ends at y 309 / 2557 narrowing to 18.8 / 17.5 mm; blue lining visible between lug and bezel, transparent pockets rows 670..750 / 1830..1917 |
| Hands (about 10:09) | hour 305.45 deg (dark baton with lume strip, 9.08 mm, flat tip), minute 53.40 deg (13.56 mm, flat tip), both with a 3.4 mm square tail; blue seconds hand 179.47 deg (pointer 15.4 mm, tail 4.8 mm, hub disc r 0.91 mm) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | own copy `pipeline/steps/watch_patek_calatrava6007g.py` of the Navitimer step (native-size maps, `bezel.profile_rz_mm`, `hands.hub`, optional pushers) |
| Prep | `pipeline/patek_calatrava6007g_prep.py` (native 1920 x 2691 maps, per-row pocket detection) |
| Comparison frame | 2048 px square, camera 23.4881 px/mm = 0.75 x the native photo, centred on the pivot (photo pixel (x, y) at ((x - 960) * 0.75 + 1024, (y - 1258.3) * 0.75 + 1024)), `config/presets/watch_kit_white_front_patek_calatrava6007g.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.patek_calatrava6007g_prep 6007g-blue   # -> config/watches/patek-calatrava6007g-6007g-blue-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
