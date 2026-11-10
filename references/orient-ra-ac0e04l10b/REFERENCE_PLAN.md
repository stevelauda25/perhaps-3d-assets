# Reference plan: Orient RA-AC0E04L10B (Contemporary: polished steel, navy sunburst dial, silver batons, navy croc leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). House method (modelled steel and
hands, photo map only for the dial print and the leather strap), built with the RA-AK0705R10B step (own case rings, lugs and spec).
File name `orient-ra-ac0e04l10b`: the tracker matches `Orient` plus the SKU.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, transparent background flattened onto white, 1600 × 1067, straight-on (seen a little from below) | `front_1600x1067.png` | HAVE (Orient USA, RA-AC0E04L30B), primary for everything. Watch about 650 px across: under the 2000 px target |
| 2 | Front turned a little toward the crown, 1000 × 1472 | `angled_1000x1472.jpg` | HAVE (Irsyad), check for the crown and case side |
| 3 | Back | none | Not needed (flat back) |

## Scale anchors

| Dimension | Listing | Measured in #1 at 16.2 px/mm |
| --- | --- | --- |
| Case without crown | 40.0 mm | 648 px wide (rows away from the crown): anchor |
| Strap at the lug tips | 20 mm | 328 px top / 331 px bottom = 20.25 / 20.43 mm |
| Lug to lug | 46.1 mm | 45.3 mm (21.0 above and 24.3 below the pivot: photo seen from below; the four lugs averaged) |
| Thickness | 11.9 mm, flat crystal | heights estimated before the 0.35 depth scale |

## Parts

| Part | True shape | Values / where from | Open |
| --- | --- | --- | --- |
| Case | Round, polished, wide sloped polished bezel, flat crystal | 40.0 mm; crystal opening 17.96 mm, dial edge 16.91 mm from #1 | Heights without a side photo |
| Lugs | Straight polished lugs | Outline from #1, mean of four, mirrored | |
| Crown | Fluted, 5.4 mm across, 3.3 mm long, 1 mm below the 3 o'clock axis | #1 | |
| Dial | Navy sunburst, minute track on the sloped rehaut, applied silver batons (longer at 12), date at 3, crest and ORIENT | Dial map from #1 with the hands removed; batons as raised polished steel plates | |
| Hands | Silver sword hour and minute, silver seconds with a short tail | Modelled, posed at the photo's time | |
| Strap | Navy croc leather, 20 mm | Photo map, house 7 mm curl from the lug tips; buckle left out | |

## Gaps

- The photo is small (16 px/mm): the dial print is softer than on the other Orient builds.
- No side photo: bezel and crystal heights estimated from the 11.9 mm listing.

Scale and photo set confirmed by Irsyad on 2026-11-10 (40.0 mm, Orient USA front photo).

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_ra_ac0e04l10b_trace   # -> config/watches/orient-ra-ac0e04l10b-trace.json
python3 -B -m pipeline.orient_ra_ac0e04l10b_dial    # -> outputs/watches/orient-ra-ac0e04l10b/photo.jpg (regenerated, not committed)
```

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/orient-ra-ac0e04l10b.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | House method: round 40.0 mm polished case with a wide polished bezel, flat crystal, four mirrored lugs from the photo, fluted crown, polished steel faceted hands and batons, raised ORIENT letters, dial map with the hands removed, 20 mm navy strap from the photo with the house curl |

Approved by Irsyad on 2026-11-10 (round 1), delivered as `models/watches/orient-ra-ac0e04l10b.glb` (0.8 MB).
