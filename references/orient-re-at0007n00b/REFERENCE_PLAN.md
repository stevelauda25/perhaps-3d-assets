# Reference plan: Orient Star RE-AT0007N00B (polished steel, grey sunburst open-heart dial, rose-gold hands, black leather strap)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Status: round 3 for review.
Rounds 1-2 tried Pasya's photo-projected front (rejected by Irsyad: not precise). Round 3 is the house method: modelled polished
steel case, bezel, lugs and crown, modelled rose-gold hands; the photo map only for the dial print and the leather strap.
File name `orient-re-at0007n00b`: the tracker matches the first word of the title (`Orient`) plus the SKU.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, white background, 1000 × 1617, taken a little from the right | `front_1000x1617.png` (+ 2× working copy) | HAVE, primary for everything since round 2 (supplied by Irsyad). Under the 2000 px target |
| 2 | 3/4 from the crown side | `three_quarter_738x492.webp` | HAVE, heights and part shapes only |
| 3 | Back | `back_750x750.webp` | HAVE, not needed (flat back) |

## Decisions

| Decision | Answer |
| --- | --- |
| Case size | **39.3 mm** (listing) across the pivot row. Check: strap between the lugs 19.5 / 20.5 mm (slanted strap, mean 20.0) against 20 mm |
| Origin | Hand pivot (920, 1382) on the 2× copy; 42.595 px/mm |
| Photo angle | Taken a little from the right and above: the right case flank and the crown's side show, the crystal ring is an ellipse (18.08 × 17.77 mm). The model follows the photo outline so the projection lines up |
| Case | Lofted from the photo outline (per 2° about the pivot, interpolated across lugs and crown) into the crystal ellipse: flank, shoulder, wide polished bezel rising inward |
| Lugs | One slab each: the photo silhouette inside a hand-read quad (inner and tip edges against the strap), top sloping 7.0 → 5.0 mm with the distance from the pivot |
| Dial | Flat to the minute track (14.94 mm), track cone up to the crystal ring. Open heart, power reserve, indices and numerals are print in the photo |
| Hands | Rose-gold dauphine hour and minute with tails, thin seconds needle: raised plates with the photographed hands on them (the hands stay in the dial print too) |
| Crown | Fluted, 3.31 mm radius, 20.2 → 23.8 mm along the 3 o'clock axis, 1.8 mm below the pivot (photo) |
| Strap | Black croc leather from the photo (white gaps beside the slanted strap filled from the leather), house 7 mm curl from each side's lug tips (21.2 / 23.7 mm); buckle and keeper left out |

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_re_at0007n00b_trace   # -> config/watches/orient-re-at0007n00b-trace.json
python3 -B -m pipeline.orient_re_at0007n00b_dial    # -> outputs/watches/orient-re-at0007n00b/photo.jpg (regenerated, not committed)
```

## Build status

```sh
python3 -B -m pipeline.jobs run jobs/orient-re-at0007n00b.json --force
```

| Round | Date | Change |
| --- | --- | --- |
| 1 | 2026-11-10 | First front relief: photo projected on every part, round case with the wide bezel, photo lugs, raised hands, fluted crown, black leather strap with the 7 mm curl |
| 2 | 2026-11-10 | Rebuilt on the sharper 1000 × 1617 photo from Irsyad: case lofted from the photo outline into the elliptic crystal ring, lugs from the photo silhouette, hands re-picked at 10:08 |
| 3 | 2026-11-10 | House method: round 39.3 mm polished case and bezel, four mirrored lugs (outline from the straight round 1 photo), crown on the 3 o'clock axis, faceted rose-gold dauphine hands, dial map with the hands removed and straightened from the photo's crystal ellipse, 20 mm strap from the photo's flat leather |
