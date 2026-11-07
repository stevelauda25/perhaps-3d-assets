# Reference plan: PATEK PHILIPPE Aquanaut Chronograph 5968A-001 (42.2 mm steel, black / orange embossed dial, black rubber strap)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 row 110 (see `sources.md`). Adapted from the [5168G blue](../patek-aquanaut-5168g-blue/REFERENCE_PLAN.md) / [green](../patek-aquanaut-5168g-green/REFERENCE_PLAN.md) Aquanaut builds (itself the [5167A-001](../patek-aquanaut-5167a-001/REFERENCE_PLAN.md) template) plus the chronograph parts of the Omega Moonwatch and Audemars Piguet Royal Oak Chronograph builds.

## Target asset

Front relief GLB `models/watches/patek-5968a001.glb` (tracker rule: lowercase brand + normalized SKU), real layered geometry (case, bezel, crystal, dial plate, hands at different heights, hubs, crown, two pushers, strap), flat back, 2.5D depth.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright studio render, transparent background, 1920 x 2691 RGBA PNG, the watch is 1372 x 2171 px incl. crown and pushers | `patek-5968a001_original.png` | HAVE (untouched; measuring and map source, native size) |
| 2 | Side / back / crown close-up | none | not available; heights are the template's, back flat |

## Measured on this photo (continuous px of the native frame; details in `config/watches/patek-aquanaut5968-5968a001-measure.json`)

| Item | Result |
| --- | --- |
| Pivot / anchor | centre of the orange hub pin-hole (959.0, 1320.0); left flank of the case 323.9 px = 21.1 mm from the pivot, S = 30.09 px/mm |
| Bezel | superellipse centre y 1323, half axes 635 x 618 px, exponent 2.25, cut back to the silhouette; window scanned on 720 rays |
| Dial | graduated black / grey embossed globe-grid dial, orange minute track, applied numerals and indices, date window at 3, one sub-dial at 6 (rounded, off-centre, own pivot at (958.6, 1532.0)); all native photo map |
| Hands | hour 303.26 deg, minute 52.74 deg (steel frames with pale lume inlays); central orange chronograph hand 0.30 deg with a long pointed tail; orange sub-dial hand 137.87 deg with a counterweight arrow |
| Crown / pushers | crown rows 1251..1449, notch wall x 1586; pushers rows 866..1092 (2 o'clock) and 1594..1830 (4 o'clock), outlines from the alpha silhouette |
| Strap | black composite rubber with an embossed pad; straight inner walls (top 626 -> 622 / 1291 -> 1297.5, bottom 616 -> 619.5 / 1293 -> 1286.5) |

## Phase 1 outputs

```sh
python3 -B -m pipeline.patek_aquanaut5968_prep 5968a001   # -> config/watches/patek-aquanaut5968-5968a001-trace.json, outputs/watches/patek-aquanaut5968-5968a001/{dial_photo,steel_photo}.jpg
```
