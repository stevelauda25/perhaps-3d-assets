# Reference plan: OMEGA Speedmaster Moonwatch Professional 42 mm 310.30.42.50.01.001 (steel, black dial, black tachymeter bezel, steel bracelet, chronograph)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). First Moonwatch: sets the Omega Moonwatch approach (Omega structure of the [Diver 300M](../omega-seamaster-diver-300m-21032422001001/REFERENCE_PLAN.md) / Seamaster 300 / Aqua Terra builds plus the chronograph parts of the Breitling Chronomat and Tudor Black Bay Chrono steps). The Silver Snoopy Award (nylon strap) and the Calibre 321 (39.7 mm) follow it. This is a separate front-relief build from the earlier full-model Speedmaster work (`references/omega-speedmaster-310-30-42-50-01-001/`, `jobs/omega-speedmaster-black-v013.json`), which is untouched.

## Target asset

Front relief GLB `models/watches/omega-31030425001001.glb` (tracker rule: lowercase brand-SKU, letters and digits only), flat back, 2.5D depth, front-matched steel bracelet.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright render, transparent background (no drop shadow), 1024 x 1024 PNG | `omega-31030425001001_original.png` | HAVE, the only source (kept untouched) |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Chronomat / Omega builds, back flat |

## Measured on this photo (continuous px of the 1024 x 1024 frame)

| Item | Result |
| --- | --- |
| Alpha bbox | x 247..811, y 1..1023 (bracelet ends = image borders; crown to x 811.6) |
| Scale | 12.7 px/mm: mean of three published dimensions read on the photo (no circle of the silhouette is on the case, the left flank is the twisted lug): case width 42 mm -> 12.63, lug to lug 47.5 mm (rows 163.7 .. 768.5) -> 12.73, bracelet 20 mm (x 386.1 .. 642.0) -> 12.79 |
| Pivot | least-squares point of the hour 304.15 / minute 48.48 / seconds 222.45 deg axes: (512.4, 451.9); hub circle (512.5, 453) r 18.2; bezel top circle (512.32, 452.05) r 250.28 (round within 0.4 percent); `ring_centre_mm` [-0.006, -0.012] |
| Rings (r px) | dial print to 192, dial flat 211, crystal edge 213, bezel_in 213.5, bezel inner chamfer to 222, black bezel top 222 .. 250.28, steel case ring beyond |
| Bezel | one black tachymeter ring (numerals 60 .. 500, dots, TACHYMETRE are photo texture); no coin ring |
| Crown | fluted barrel x 770 .. 803.5 (r 42.2, centre y 462.7), domed Omega cap to x 811.4 (r 20); guard shoulders x 785 (rows 376..420 / 504..548) in the silhouette |
| Pushers | cylinders r 29.6 / 30.8 px, axes +-23.5 deg about their own origins (512.8, 455.1) / (506.8, 466.9), end faces 301.5 / 302.5 px from the origins |
| Lugs | twisted asymmetric lugs in the silhouette; lug tops y 163.7, bottoms y 768.5 |
| Hands (about 10:09:35) | hour baton half width 6.65 px, length 123 px, lume strip; minute 5.9 -> 5.5 px, length 191 px (needle tip), lume strip; chrono seconds shaft 3 -> 1.8 px with lume diamond (max 8.8 px at s 116), length 190 px; sub-dial hands: white batons 5.2 px wide, hubs r 8.95 px at (426.1, 452.6), (600.1, 453.6), (512.8, 539.5) |
| Bracelet | five columns outer / narrow / centre / narrow / outer, vertical joints top x 459 / 476.8 / 550.4 / 568, bottom 455 / 472.3 / 548.5 / 565.8; outer and narrow columns share joint rows, the centre column is staggered |

## Phase 1 outputs

```sh
python3 -B -m pipeline.omega_moonwatch_prep   # -> 2x reference, config/watches/omega-moonwatch-31030425001001-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
