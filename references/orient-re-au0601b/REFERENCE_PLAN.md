# Reference plan: Orient Star RE-AU0601B (Diver 1964 2nd edition, black dial, black insert, five-link bracelet)

Written 2026-11-10 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). Front photo supplied by Irsyad on 2026-11-10.

## Target asset

A front-facing GLB in `models/watches/orient-re-au0601b.glb`, built like `orient-ra-aa0818l19b.glb`: front relief, flat back, 2.5D depth, modelled case, bezel and insert, applied markers, hands, crown and bracelet in house steel and glass; the dial print from a photo map.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on, white background, 1264 × 2000 (2× working copy 2528 × 4000) | `front_1264x2000.jpg`, `front_2x_2528x4000.png` | HAVE, primary for everything |
| 2 | 3/4 from the crown side | none | MISSING: heights estimated from the listed 14.3 mm |
| 3 | Back | none | not needed for the flat-backed front asset |

## Scale anchors

| Dimension | Listed | Measured at 41.0 mm (48.37 px/mm on the 2× copy) |
| --- | --- | --- |
| Bezel diameter | **41.0 mm** (anchor, listing) | coin edge on the flanks |
| Lug width | 20 mm | end link 19.2 mm; bracelet 19.4 mm just past the lugs |
| Lug to lug | 49.6 mm | 48.5 mm |
| Insert | not listed | 30.9-39.0 mm, centred 0.3 mm above the pivot |

## Part by part

| Part | True shape | Source |
| --- | --- | --- |
| Bezel | Steel ring with a fine coin edge (about 228 teeth); black insert with white numerals 10-50, bars, minute dots and bars 1-14, triangle with a lume pip | #1; prints traced by threshold |
| Dial | Gloss black; minute track; power reserve scale 50-25-0 at 12 | dial map |
| Markers | Applied lume dots in polished cups; bars at 6 and 9; trapezoid at 12; square at 3 beside a polished date frame | #1 |
| Hands | Hour: lollipop (lume disc in a polished ring, short tip, stem with lume); minute: sword with a lume blade; seconds: needle with a lume disc and a small counterweight disc; power reserve: tapered polished hand on its own hub | #1 |
| Crown | Large fluted crown at 3 | #1 |
| Bracelet | Five columns: brushed outer and centre, polished 2 and 4 with joints 2.7 mm further out; pitch 4.9 mm | #1 |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | 41.0 mm bezel (listing) |
| Heights | Front-relief reading of the listed 14.3 mm (no side photo) |
| Hand pose | The pose in #1 (about 10:09:37) |
| Case symmetry | The photo sits a little off-centre to the pivot; lugs use half the silhouette width, symmetric about the pivot |
| Bracelet curve | House curl: 7 mm radius from the lug tips, end_y = tip + 2.2 R |

## Phase 1 outputs

```sh
python3 -B -m pipeline.orient_re_au0601b_trace   # -> config/watches/orient-re-au0601b-trace.json
python3 -B -m pipeline.orient_re_au0601b_dial    # -> outputs/watches/orient-re-au0601b/dial_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-10 | 1 | First build |
