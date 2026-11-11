# Reference plan: Bulova 96B251 (Lunar Pilot chronograph, 45 mm, black leather strap)

Written 2026-11-11 (Phase 0 of [WATCH_PRODUCTION_WORKFLOW.md](../../docs/3d/WATCH_PRODUCTION_WORKFLOW.md)). The supplied photo is angled; the straight front is Bulova's official render.

## References held

| # | View | File | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on render, transparent background, 1293 × 2048 | `front_official_1293x2048.png` | HAVE (Bulova official), primary for everything |
| 2 | Side | `side_official_1656x2048.png` | HAVE (Bulova official): heights |
| 3 | Back | `back_official_1226x2048.png` | HAVE, not needed for the flat-backed asset |
| 4 | 3/4 from the left | `angled_900x900.jpg` | HAVE (Irsyad) |

## Scale anchors

| Dimension | Official | Measured |
| --- | --- | --- |
| Case width | **45 mm** (anchor) | 45.05 mm from the silhouette at 26.81 px/mm (the 96B258 scale x 1.17) |
| Lug width | 20 mm | strap 19.8 mm |
| Lug to lug | not listed | 52.2 mm in the render |

## Part by part

The head (case, horns, pusher shoulders, bezel, dial rings, indices, hands, subdials, crown) is the 96B258 head: the 96B258
render matches this one at 1.17x about the pivot (normalised correlation 0.966, same hand pose), so the parts come from
[the 96B258 plan](../bulova-96b258/REFERENCE_PLAN.md) moved to this render's pivot (602, 993). New here:

| Part | True shape | Source |
| --- | --- | --- |
| Strap | 20 mm black leather with an embossed diamond pattern and edge stitching, entering the recess between the horns | #1 rows past the horn tips |
| Date | 18 | dial map |

## Decisions

| Decision | Answer |
| --- | --- |
| Scale | 45 mm (official) through the 96B258 render at 1.17x: the left flank touches this render's image edge |
| Strap | Photo map from the render's own strap rows, house curl from the horn tips |

## Phase 1 outputs

```sh
python3 -B -m pipeline.bulova_96b251_trace   # -> config/watches/bulova-96b251-trace.json
python3 -B -m pipeline.bulova_96b251_dial    # -> outputs/watches/bulova-96b251/dial_photo.jpg and strap_photo.jpg (regenerated, not committed)
```

## Versions

| Date | Round | Change |
| --- | --- | --- |
| 2026-11-11 | 1 | First build |
