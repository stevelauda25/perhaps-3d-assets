# Reference plan: TUDOR Royal 36 M2836C1A0-0101 (steel, black sunburst dial, gold Roman numerals, five-row steel bracelet)

Written 2026-11-07 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Photo and SKU from catalog 2 (see `sources.md`).

## Target asset

Front relief GLB in `models/watches/tudor-m2836c1a0-0101.glb` (tracker rule: lowercase brand-SKU, the tracker auto-matches only that), flat back, 2.5D depth, curled bracelet, built like the Seiko reliefs.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, near straight-on, transparent background, 900 x 1200 | `tudor-m2836c1a0-0101_900x1200.png` | HAVE, the only source |
| 2 | Side / back / crown close-up | none | not available; heights are estimated, the back is flat |

## Scale anchors

| Dimension | Value | Source |
| --- | --- | --- |
| Case diameter | **36 mm** (anchor) | model name; measured 35.9 mm from the silhouette (14.056 px/mm) |
| Lug to lug | not listed | 40.5 mm as built (tip at 20.25 mm), not verified |
| Bracelet width | not listed | 21 mm at the case, narrowing in the photo to 16 mm at the ends (perspective plus curl) |
| Heights | not listed | estimated, house depth scale 0.35 |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Case, lugs | Integrated: the outline runs from the round case into the bracelet; brushed top | #1 silhouette |
| Bezel | 48 segments of 7.5 deg: plain polished facets (centred at 12 o'clock and every 15 deg) alternating with five-rib facets (7.5 deg + 15 k) | #1 (phase and count from the radial and FFT read) |
| Crystal | Flat sapphire, not visible apart from a thin wall | #1 |
| Dial | Black sunburst; gold applied Roman numerals, TUDOR shield, GENEVE, CHRONOMETER / OFFICIALLY CERTIFIED, SWISS MADE, gold minute track, date at 3 | photo map (2x crop, flat) |
| Hands | Gold batons with cream lume strip and a rounded tip; hour 7.6 mm, minute 12.9 mm; thin gold seconds needle 12.9 mm with a short tail | #1 |
| Crown | Fluted, 6.3 mm, 24 flutes, plain cap | #1 |
| Bracelet | Brushed rows in three columns (centre 5 mm) with two polished channels half a pitch out of step; pitch about 3.6 mm | #1 |

## Decisions

| Decision | Answer |
| --- | --- |
| Hands in the map | Left in: the 3D hands (0.1 mm wider) cover them at the photographed pose, and the minute hand keeps hiding the II numeral as in the photo. Nothing is invented. |
| Numerals | Flat in the map (not applied geometry). Raising them needs a clean numeral trace; offer if wanted. |
| Bracelet curl | House curl: 5 mm radius from the lug tips, end = tip + 11 mm |
| Pose | 10:09 as photographed; front-locked presentation |

## Phase 1 outputs

```sh
python3 -B -m pipeline.tudor_royal36_prep   # -> 2x reference, config/watches/tudor-royal36-m2836c1a0-0101-trace.json, outputs/watches/.../dial_photo.jpg
```
