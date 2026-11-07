# Reference plan: OMEGA Speedmaster Calibre 321 Chronograph 39.7 mm 311.30.40.30.01.001 (steel, black dial, black tachymeter bezel, steel bracelet, chronograph)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Follower of the Omega Moonwatch template ([../omega-speedmaster-moonwatch-professional-31030425001001/baseline/BASELINE.md](../omega-speedmaster-moonwatch-professional-31030425001001/baseline/BASELINE.md)); everything is re-measured on this photo. Separate from the earlier full-model Speedmaster work (`references/omega-speedmaster-310-30-42-50-01-001/`), which is untouched.

## Target asset

Front relief GLB `models/watches/omega-31130403001001.glb` (tracker rule: lowercase brand-SKU, letters and digits only), flat back, 2.5D depth, front-matched steel bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near-upright render, transparent background (no drop shadow), 1024 x 1024 PNG | `omega-31130403001001_original.png` | HAVE, the only source (kept untouched) |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Moonwatch build, back flat |

## Measured on this photo (continuous px of the 1024 x 1024 frame)

| Item | Result |
| --- | --- |
| Alpha bbox | x 231 .. 833, y 0 .. 1022 (bracelet ends = image borders; crown to x 833.4) |
| Scale | 14.2 px/mm: case width 39.7 mm from the circular left case flank (r 281.2 .. 282.4 px -> 14.17 .. 14.23); cross-checks: lug gap 268 px (18.9 mm at 14.2), lug to lug rows 134 .. 805.5 = 47.3 mm |
| Pivot | least-squares point of the hour 303.468 / minute 47.898 / seconds 221.828 deg axes: (511.72, 461.76), residuals <= 0.05 px; hub r 21.0; bezel outer circle (513.30, 460.70) r 275.12; `ring_centre_mm` [0.111, 0.075] |
| Rings (r px about the bezel centre) | dial black to 203.5, bright inner steel ring 204.5 .. 211.5, dark gap to 218, inner chamfer 219 .. 242, black bezel top 244 .. 274.5, steel case ring to 282 (case flank circle) |
| Bezel | one black tachymeter ring (numerals 60 .. 500, dots, TACHYMETRE are photo texture); no coin ring |
| Crown | fluted barrel to x 825 (r 47.5, centre y 466.9) with a domed cap to x 833.4 (r 21.5); no guards |
| Pushers | cylinders r 31.9 / 31.6 px, axes +24.7 / -25.7 deg about their own origins (514.8, 464.8) / (512.2, 462.7), end faces 329 / 335 px |
| Lugs | straight lugs in the silhouette; lug tops y 134, bottoms y 805.5; right / left flank = circle |
| Hands (about 10:09:35) | hour baton hw 7.4 px, length 136.3, beige lume strip; minute hw 6.1 px, length 209.6 (needle tip), lume strip; chrono seconds shaft 3.5 -> 2.6 px with lume diamond (max hw 9.9 px at s 132), length 210.7, counterweight tail 52 px; sub-dial batons 5.1 px wide with a pointed tip, hubs r 9.9 px at (417.0, 462.3), (607.4, 461.8), (512.9, 557.3) |
| Bracelet | three columns outer / centre / outer, vertical joints top x 440 / 576 .. 582, bottom 442.5 / 583 .. 577.5; outer columns share joint rows, the centre column is staggered |

## Phase 1 outputs

```sh
python3 -B -m pipeline.omega_calibre321_prep   # -> 2x reference, config/watches/omega-calibre321-31130403001001-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
