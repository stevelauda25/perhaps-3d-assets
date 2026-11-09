# Reference plan: Seiko 5 SNKK65K1 (steel, silver dial, day-date)

Written 2026-11-09 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 1 built 2026-11-09, waiting for the designer.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 3198 × 3198 | `front_3198.png` | HAVE, primary for everything (upscaled: dark halos round every part) |
| 1b | Front, turned toward the crown, 2000 × 3502 | `front_turned_2000x3502.png` | Cross-check only |
| 2 | 3/4 from the crown side | none | MISSING: heights taken from SNKL41K1 |
| 3 | Back | none | MISSING: not needed for the flat-backed front asset |

## Decisions

| Decision | Answer |
| --- | --- |
| Case diameter | **38 mm** (spec sheet from Irsyad, 2026-11-09). Cross-check: bracelet 17.87 mm at the first row vs 18 mm listed lug width |
| Construction | Own step (`watch_seiko_snkk65`, copied from the SNKL47K1 step): the case differs from SNKL41K1 (Irsyad: similar, with differences) |
| Silhouette | Left half mirrored: the right side has the crown and the clasp |
| SEIKO, 5 shield, index pips, green gasket, SUN 5 | Kept in the dial map |
| Bracelet curl | Starts at the end of the end-link tongue (23.5 mm), not at the shoulder tops (21.0 mm), so the end link stays straight |

## Differences from SNKL41K1

| Part | SNKL41K1 | SNKK65K1 |
| --- | --- | --- |
| Lugs | Slim lugs from the case | Square shoulder blocks either side of the end link |
| End link | Straight, ends at the lug tips | Centre and mid pieces run 2.5 mm past the lug tips as a tongue |
| Dial | White, black square at 3 | Silver sunburst, green crystal gasket, no square |
| Hands | Dauphine with lume strip, seconds with counterweight bar | Swords with a lume insert, round collar on the hour hand, seconds needle with a long tapered tail |
| Indices | Single batons, pip at the inner end | Single batons, pip at the outer end; 12 is a double-width tapered block |
| Day-date | Thin frame | Wide polished frame (0.45 mm wall) |
| Bracelet | Centre, strips, outer half a row off | Polished centre and brushed mid pieces in step, brushed outer links; joints 2.5 mm apart |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_snkk65_trace   # -> config/watches/seiko-snkk65k1-trace.json
python3 -B -m pipeline.seiko_snkk65_dial    # -> outputs/watches/seiko-snkk65k1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 44.2105 px/mm from the 38 mm case (left flank, concentric with the crystal ring); origin = hand pivot (1600, 1512) |
| Crystal ring | 15.833 mm (outer edge of the green gasket); minute track ends at 14.93 mm |
| Lug tips | 21.0 mm (shoulder tops); end-link tongue to 23.5 mm |
| Indices | 9.50–12.94 mm, 0.837 mm wide; 12: 1.696 mm |
| Hands | hour 305.2°, 8.08 mm; minute 50.09°, 11.71 mm; seconds 253.91°, 12.24 mm, tail 6.61 mm |
| Bracelet | pitch 6.68 mm; centre 0.19 and mid pieces to 0.57 of the half width |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-snkk65k1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-09 | First front relief: all steel, shoulder lugs, end-link tongue, sword hands with lume, wide day-date frame, three-column bracelet with the 7 mm curl |
| 2 | 2026-11-09 | Day-date frame matched to the photo outline: moved up 0.3 mm, rounded corners (0.72 mm), thinner wall (0.36 mm) |
