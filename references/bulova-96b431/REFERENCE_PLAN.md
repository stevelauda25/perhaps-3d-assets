# Reference plan: Bulova 96B431 (Marine Star Precisionist 43 mm, yellow wave dial, black twelve-sided bezel, rubber strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). The supplied photo is straight-on too; Bulova's official render is sharper and has a clean transparent background, so it is the working reference.

## Target asset

A front-facing GLB in `models/watches/bulova-96b431.glb`: front relief, flat back, 2.5D depth, modelled case, bezel, hands, indices, crown and lugs in house steel and glass; the dial with the bezel insert and the strap from photo maps.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on render, transparent background, 1253 × 2048 | `front_official_1253x2048.png` | HAVE (Bulova official), primary for everything |
| 2 | Side, crown side | `side_official_1733x2048.png` | HAVE (Bulova official) |
| 3 | Back | `back_official_1209x2048.png` | HAVE, not needed for the flat-backed asset |
| 4 | Dial close-up | `dial_closeup_official_2048x2048.jpg` | HAVE: hand and index finish |
| 5 | Front, retail | `front_retail_1632x2688.jpg` | HAVE (Irsyad) |

## Scale anchors

| Dimension | Official | Measured at 43 mm (26.50 px/mm) |
| --- | --- | --- |
| Case width | **43 mm** (anchor) | bezel rim flat to flat at 8, 9 and 10 o'clock |
| Lug width | 22 mm | 22.1 mm |
| Case length | 50 mm | 49.1 mm lug tip to lug tip (12 o'clock tips 23.7 mm, 6 o'clock 25.3 mm from the pivot; mean used) |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case, lugs | Brushed steel, faceted lugs, crown guards at 3 | #1 silhouette |
| Bezel | Twelve sides, flats at 12, 1, 2 ...: polished rim, black insert with numerals and markers | #1, rim and insert flats; insert print in the dial map |
| Dial | Yellow wave dial, yellow minute track, prints, date window at 3 | dial map |
| Indices | Applied steel frames with lume: ten tapered bars, a short bar at 3; applied logo at 12 | #1 lume and steel masks |
| Hands | Polished sword hour and minute hands with lume, open windows and flat tails; seconds needle with a red-framed lume triangle and a broad tail | #1, hand-aligned strips |
| Crown | Fluted steel crown between guards | #1 |
| Strap | Black rubber, wave pattern, tapers from 22 mm | strap map, taper read past the lug tips |

## Decisions

| Decision | Answer |
| --- | --- |
| Front reference | Bulova's official render |
| Scale | 43 mm case width (official) |
| Lug to lug | The render's 49.1 mm (mean of both ends) is followed; official case length 50 mm |
| Covered parts | Indices at 2 and 7 (under the hands): the mean bar shape |
| Heights | Front-relief reading of the official 12.1 mm |

## Phase 1 outputs

```sh
python3 -B -m pipeline.bulova_96b431_trace   # -> config/watches/bulova-96b431-trace.json
python3 -B -m pipeline.bulova_96b431_dial    # -> outputs/watches/bulova-96b431/dial_photo.jpg and strap.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
