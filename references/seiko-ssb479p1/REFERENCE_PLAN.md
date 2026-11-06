# Reference plan: Seiko SSB479P1 (quartz chronograph, black dial, cream subdials, steel bracelet)

Written 2026-11-06 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: delivered (round 1, 2026-11-06).

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, white background, 3165 × 4640 | `front_3165x4640.jpg` | HAVE, primary for everything; turned slightly (left flank shows 0.35 mm more) |
| 2 | Back | none | GAP: not needed for a front relief |
| 3 | 3/4 or side | none | GAP: heights estimated for the listed 12.6 mm |

## Decisions

| Decision | Answer |
| --- | --- |
| Case size | **38.7 mm** case width on the centre row (listing). Checks: bracelet 19.57 mm just past the lug tips vs 20 mm listed; lug to lug 45.25 mm traced |
| Origin | Case and dial centre. The photo's hand pivot sits 0.17 mm left of it; hands are placed on the origin |
| Bezel | Thin polished steel edge, black tachymeter insert from the photo map (its centre sits 0.27 mm right of the dial centre in the photo; mapped from its own centre) |
| Dial | Photo map: dial, three cream subdials with their hands, date at 4:30, print, the grey crystal wall as a sloped cone |
| Bracelet | Five columns with the house curl; joints and column split from the photo |

## Parts

| Part | True shape |
| --- | --- |
| Case | Round, polished, lugs with brushed tops and polished edges |
| Crown and pushers | Fluted crown at 3; cylindrical pushers at 2 (60.3°) and 4 (119.7°), stem plus wider cap |
| Indices | Applied polished batons with a cream lume tip; wide at 12; short at 3, 6, 9 beside the subdials |
| Hands | Silver swords with cream lume (hour, minute), long silver chronograph needle with a tapered counterweight |
| Bracelet | Brushed outer and centre links sharing joints from the lug tips; polished narrow links between, joints 1.67 mm nearer the case; pitch 4.30 mm |

## Phase 1 outputs

```sh
python3 -B -m pipeline.seiko_ssb479_trace   # -> config/watches/seiko-ssb479p1-trace.json
python3 -B -m pipeline.seiko_ssb479_dial    # -> outputs/watches/seiko-ssb479p1/dial_photo.jpg (regenerated, not committed)
```

| Item | Value |
| --- | --- |
| Scale | 52.532 px/mm from the 38.7 mm case width; origin (1536, 2330) |
| Rings | insert 18.96–16.89, dial edge 14.85, minute track 14.18 mm |
| Lugs | leave the case at 12.0 mm, tips 22.63 mm |
| Hands (10:08:30 chrono) | hour 307.8°, minute 50.3°, chronograph 180° |

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/seiko-ssb479p1.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-06 | First front relief: round case with tachymeter bezel from the photo, crown and two pushers, applied batons with cream lume, sword hands and chronograph needle, five-column bracelet with the 7 mm house curl |
