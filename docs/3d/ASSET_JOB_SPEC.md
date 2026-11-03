# Asset job spec

One JSON file per job in `jobs/`. Paths are project-relative. Validated by
`python3 -B -m pipeline.jobs validate` (see `validate()` in [pipeline/jobs.py](../../pipeline/jobs.py)).

| Field | Required | Meaning |
| --- | --- | --- |
| `id` | yes | Lowercase slug; unique job identity |
| `output` | yes | Must equal `outputs/jobs/<id>` |
| `input` | yes | Source `.blend`; opened read-only, never written |
| `stages` | yes | Ordered list, see below |
| `geometry_lock` | packaging | `geometry_lock.json` whose `protected` snapshot every scene stage re-verifies |
| `references` | no | Paths that must exist (design sheets, reference folders) |
| `depends_on` | no | Job ids that must succeed first (`batch` only); typically `input` is that job's scene |
| `asset_type`, `tier`, `model`, `baseline` | no | Descriptive; not interpreted |

## Scene stage

```json
{"name": "look", "step": "packaging_look", "params": { ... }}
```

Runs `pipeline/steps/<step>.py: run(params)` inside Blender on the previous scene,
then saves `<name>.blend`. Available steps:

| Step | Params | Effect |
| --- | --- | --- |
| `packaging_look` | `source_manifest` + `leather` (same keys as `config/private_edition_production.json`), and/or `studio_lights` (list of `{name, position, target, size, power}`) | Rebuild PE6 leather node trees from the 8K sources; move/resize/re-power existing reflection cards |
| `packaging_tier` | `preset` (`config/tiers/<tier>.json`), optional `exposure_ev`; roles may use `{"library": id}` | Swap slot materials per the preset's builder, apply its studio cards, hide listed objects, purge orphaned images |
| `logo_deboss` | `svg`, `width_mm`, `center_z_mm`, `front_y_mm`, `depth_mm`, `lip_radius_mm`, `outset_mm`, `wrap`, `lid_shell` (+ optional `flat_walls`, `weighted_normals`, `lip_harden`) | Re-cut the wordmark deboss from SVG outlines on the removable lid wrap only; shade deboss walls flat; drop dead fonts |
| `material_lookdev` | `material` (library id), `lighting` (`neutral`/`grazing`), optional `overrides` | Lookdev scene only: apply library material to the samples, select light set |

A new step is one module with `run(params) -> dict`. Keep it parameter-driven and
idempotent; it must not save, render or touch locked geometry.

## Render stage

```json
{"name": "hero", "render": {"camera": "CAM | production_hero", "resolution": 2048, "profile": "final",
                            "border": [0.4, 0.73, 0.3, 0.63],
                            "camera_override": {"position": [x,y,z], "target": [x,y,z], "lens_mm": 200}}}
```

`border` and `camera_override` are optional (`diagnostic` requires `border`).
`camera_override` aims an unsaved copy of the named camera; presets are never edited.
Outputs `<name>.png` (16-bit) and, for `final`, `<name>.exr` (half, ZIP).
Profiles live in [config/render_profiles.json](../../config/render_profiles.json).

## Job directory

```text
outputs/jobs/<id>/
  job.json               frozen copy of the spec as last run
  <scene-stage>.blend    one per scene stage (Spark ~20 MB; 327 MB if the input is a packed-8K scene)
  <render-stage>.png/.exr
  state/<stage>.json     status, fingerprint, seconds, rss_mb, recorded render settings, lock digest
  logs/<stage>.log       full Blender output
  events.jsonl           append-only run history (feeds `report`)
```

## Examples

- [spark-v002.json](../../jobs/spark-v002.json): canonical base → `packaging_tier` look
  (`config/tiers/spark-v002.json`) → material/branding crops → preview hero → final hero (not rendered yet).
- [icon-v014.json](../../jobs/icon-v014.json): render-only on the approved Icon scene (branding crop + final hero).
- [casio-f91w-preview.json](../../jobs/casio-f91w-preview.json): render-only watch preview.
