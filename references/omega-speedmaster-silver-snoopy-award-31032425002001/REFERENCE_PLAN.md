# Reference plan: OMEGA Speedmaster Silver Snoopy Award 50th Anniversary 42 mm 310.32.42.50.02.001 (steel, white / silver dial with blue sub-dials and the Snoopy engraving, blue tachymeter bezel, blue nylon strap, chronograph)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`). Follower of the Omega Moonwatch template ([310.30.42.50.01.001](../omega-speedmaster-moonwatch-professional-31030425001001/baseline/BASELINE.md): same case, bezel, crown and pushers in structure; here a nylon strap and different colours). Separate front-relief build from the earlier full-model Speedmaster work (`references/omega-speedmaster-310-30-42-50-01-001/`, `jobs/omega-speedmaster-black-v013.json`), which is untouched.

## Target asset

Front relief GLB `models/watches/omega-31032425002001.glb` (tracker rule: lowercase brand-SKU, letters and digits only), flat back, 2.5D depth, front-matched nylon strap.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, upright render, transparent background (no drop shadow), 1024 x 1024 PNG | `omega-31032425002001_original.png` | HAVE, the only source (kept untouched) |
| 2 | Side / back / crown close-up | none | not available; heights copied from the Moonwatch build, back flat |

## Measured on this photo (continuous px of the 1024 x 1024 frame)

Registration against the Moonwatch template: the alpha silhouettes agree within about 3 px (xor 4.6 percent of the union), but the render has a stronger perspective: the bezel top circle is 257.26 px (Moonwatch 250.28), the pushers are 8 percent thicker, the strap 266 px between the lugs (255). So nothing of the template was reused as a number; every value below is measured again.

| Item | Result |
| --- | --- |
| Alpha bbox | x 244..813, y 1..1023 (strap ends = image borders; crown to x 814.2) |
| Scale | 12.87 px/mm: mean of case width 42 mm (12.80), lug to lug 47.5 mm (rows 158.6 .. 773.5, 12.95) and strap 20 mm (12.8) |
| Pivot | least-squares point of the hour 303.47 / minute 50.44 deg lume-strip axes (0.02 / 0.12 px): (510.86, 453.40); hub dome (512.22, 455.77) r 18.42; bezel top circle (512.76, 454.68) r 257.26; `ring_centre_mm` [0.151, -0.098] |
| Rings (r px about (512.8, 454.7)) | dial flat 204.5, crystal edge 206, bezel in 206.5, silver chamfer to 227, blue top 227 .. 257.26, steel case ring beyond |
| Bezel | one blue tachymeter ring (numerals 60 .. 500, dots, TACHYMETRE are photo texture); wide silver inner chamfer; no coin ring |
| Crown | fluted barrel x 774 .. 807.4 (r 43.15, centre y 461.45), domed cap to x 814.2; guard shoulders x 790.3 in the silhouette |
| Pushers | cylinders r 32.83 / 32.98 px, axes +24.44 / -24.85 deg about their own origins (514.53, 458.91) / (509.21, 461.65), end faces 306.9 / 310.5 px |
| Lugs | twisted asymmetric lugs in the silhouette; lug tops y 158.6, bottoms y 773.5 |
| Hands (about 10:09:35) | hour baton half width 6.0 px, length 124.3 px, white lume strip; minute 4.8 px, length 184.3 px (arrow tip), lume strip; chrono seconds hand 222.3 deg: tail 52 px, shaft 3.3 px half width, white lume diamond (s 99.9 .. 132.3), needle to 194.5 px (bent 1.3 deg against the shaft); sub-dial hands: batons 3.7 .. 4.5 px wide, hubs r 8.2 / 8.84 / 8.74 px at (424.0, 455.6), (601.75, 456.15), (512.15, 545.31) |
| Strap | blue nylon (weave, lighter stitching along both edges), one piece, 266 px wide between the lugs narrowing to about 100 px at the image borders; no keepers |

## Phase 1 outputs

```sh
python3 -B -m pipeline.omega_snoopy_prep   # -> 2x reference, config/watches/omega-snoopy-31032425002001-trace.json, outputs/watches/.../{dial_photo,steel_photo}.jpg
```
