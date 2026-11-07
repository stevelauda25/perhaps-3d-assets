# Reference plan: PATEK PHILIPPE Aquanaut 5167A-001 (40 mm steel, black embossed dial, black composite rubber strap)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). First Patek Philippe asset: it sets the Aquanaut approach (structure of the [Audemars Piguet Offshore Diver build](../audemars-royal-oak-offshore-diver-15720st-green/REFERENCE_PLAN.md) with the smooth rounded-octagon Aquanaut case). The Aquanaut 5168G green and blue (catalog rows 102 and 104, 42.2 mm white gold) follow this template.

## Target asset

Front relief GLB `models/watches/patek-5167a001.glb` (tracker rule: lowercase brand-normalized SKU), flat back, 2.5D depth, flat front-matched rubber strap.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background (soft drop shadow below the strap), 1920 x 2691 RGBA PNG, the watch is 1307 x 2119 px | `patek-5167a001_original.png` | HAVE (kept untouched; working source for measuring and for the maps, native size) |
| 2 | Side / back / crown close-up | none | not available; heights are estimates (real case thickness 8.1 mm), back flat |

## Measured on this photo (continuous px of the native 1920 x 2691 frame)

| Item | Result |
| --- | --- |
| Anchor | no circle fits: the listed 40 mm case diameter = the left flank of the case (median alpha edge over rows 1330..1400, x 357.2) to the notch wall of the crown; the pivot sits at the middle, so the flank is 20 mm left of the pivot: 30.0894 px/mm |
| Pivot | the screw of the small white hub disc (959.0, 1348.0); the hour / minute centre lines (edge fits) pass through it within 0.8 px |
| Bezel | smooth, brushed rounded-octagon face with a polished outer edge: outer outline fitted as a superellipse (centre (959, 1350), half axes 601.8 x 586.5 px, exponent 2.25) from the top / bottom edge rows (763.5 / 1936.5 at x 959) and the flank, cut back to the silhouette; the rounded-square window edge is scanned on 720 rays (innermost bright run of the brushed face, 14.7 to 16.3 mm from the pivot), polished chamfer about 14 px |
| Dial | black to grey gradient dial with the embossed "Tropical" grid, applied arabic numerals and luminous square indices, minute track on a sloped flange, date window at 3, "SWISS MADE" at 6: all in the native photo map, the grid is texture only |
| Crown | one fluted crown at 3 o'clock, axis y 1364, radius 83 px, from the notch wall (x 1555) to x 1663, rounded end; flutes are texture |
| Lugs | integrated; top corners start at row 677, bottom tips end at row 2078 (lug to lug 46.5 mm); strap inner walls x 632 / 1281 (top), 630 / 1277 (bottom) |
| Strap | black composite rubber, 21.6 mm wide between the lugs, flaring to the case at the top (542 px at row 470 to 631 at row 650), tapering at the bottom (630 to 549 px at rows 2090..2510), rounded ends; embossed grid pad texture only |
| Hands (about 10:09:30) | hour 304.62 deg, steel baton (half width 25 px) with a lume inlay (half 14 px, s 78..254) and an arrow tip at s 281; minute 52.11 deg (lume s 80..386, tip s 410); seconds 179.76 deg, thin shaft half 3.5 px to s 416, counterweight tail to s 150; round hour-hand base disc (radius 38 px) and the white seconds hub (21.5 px) |

## Decisions

| Decision | Answer |
| --- | --- |
| Step | own copy `pipeline/steps/watch_patek_aquanaut40.py` of the Audemars Piguet Offshore Diver step: superellipse bezel ring (rays) with chamfer, polygon dial / crystal, one lathe crown, hands with lume, one-piece rubber strap with per-side emission |
| Prep | `pipeline/patek_aquanaut40_prep.py` (native-size maps, flank anchor, scanned window, strap inner walls, crown profile in the measure file) |
| Comparison frame | 1280 px square at half the native scale (15.0447 px/mm) centred on the pivot (the half-size photo pivot (479.5, 674.0) lands at (640, 640)), `config/presets/watch_kit_white_front_patek_aquanaut40.json` |

## Phase 1 outputs

```sh
python3 -B -m pipeline.patek_aquanaut40_prep   # -> config/watches/patek-aquanaut40-5167a001-trace.json, outputs/watches/patek-aquanaut40-5167a001/{dial_photo,steel_photo}.jpg
```
