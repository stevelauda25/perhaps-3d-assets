# Perhaps 3D troubleshooting

Use this guide with the [SOP](PRODUCTION_WORKFLOW.md) and
[verified v010 settings](BASELINE_V010.md). Inspect before rerendering. Changes and
new output generation require a task that authorizes them; v010 stays immutable.

| Symptom | Likely cause / inspect first | Safe next action for an authorized production task |
| --- | --- | --- |
| Box looks like clay or a flat matte object | Unsuitable grain morphology, roughness too uniform, broad reflection cards; inspect actual source normal and the two leather node trees in the saved scene | Follow the SOP's clay decision tree: source → scale → normal/height → roughness → studio. Do not raise samples or global brightness as the first fix |
| Grain too small / disappears in hero | Excessive coordinate repetition, small physical repeat, filtering or denoising; compare config `tile_mm` with node `Physical source repeat` and unchanged metric UV density | Change one shared coordinate factor in a new version only. In v010 32mm/UV × 1/0.08 = 400mm repeat. Do not restore 96mm from Leather037 history |
| Grain oversized or too deeply pebbled | Repeat too large, strong normal or duplicate height bump; distinguish physical size from relief amplitude | Inspect mapping and normal separately. Do not fix scale using bump strength; retain aligned maps |
| Thin cracks / polygon network instead of rounded grain | Source morphology, not just frequency; Leather037 remains angular when enlarged | Inspect original maps at native resolution and qualification record. Do not reintroduce a rejected source for convenience or create a dominant Voronoi/noise pattern |
| Top/front/side have different grain sizes | Generated/object coordinates, object scale, per-face mapping or stretched UVs; inspect `PE metric wrap`, map vector links and unit object scales | Preserve UVs and use one shared mapping factor. Historical planar density audit covers 47 sampled edges, not every possible seam. Check continuity without modifying canonical vertices |
| Top seems smooth while side is textured | Grazing angle, specular/roughness response, filtering or source orientation can alter visibility without changing density | Confirm density first; then inspect card geometry and reflections. Do not use a different texture scale on the top |
| Reveal looks like a black gap | Metal receives no useful reflection; wrong selected material; inspect collar slot 2 and `PE | Dark graphite brushed inlay.001` | Verify metallic response and the Low inlay reflection card before changing band dimensions. Preserve original collar/reveal geometry |
| Reveal looks silver or chrome | Bright source reflection, base reflectance/roughness or metal parameter drift | Compare final graphite parameters and card settings to baseline. Do not compensate by painting reflections into a map or changing geometry |
| Wordmark invisible / looks like hairline outlines | Thin provisional Didot, grazing illumination, shallow/flat compression response | Inspect appearance-wrap deboss, pressed material and lighting. An official vector is not established; document that limitation. Do not increase contrast, size or position casually |
| Wordmark too visible / floating / glowing | Separate text surface, overly contrasting pigment/coat, bad depth or artificial highlights | Compare pressed-leather material and actual recessed wrap geometry; avoid emissive branding or an added floating text object |
| Corner seams, sharp transitions or bevel segmentation | Appearance-wrap normals/UV seam, evaluated bevel limits or locked construction | Inspect visible wraps and modifiers separately from hidden canonical shells. Never unhide duplicate shells or change canonical bevels to disguise the problem. Record structural limits |
| Stitching looks dashed/decorative | Excessive contrast, gaps, float or incorrect thread response | Inspect the existing stitching curve and finishing report. Keep changes isolated and restrained; no blanket embellishment |
| Slow render / Metal memory pressure | Full 8K maps, multiple Blender processes, whole-frame diagnostics or first-use overhead | Use bounded final-density borders; close unnecessary render processes when authorized; keep source fidelity. Review `events.jsonl` and Metal availability. Do not repeatedly run CPU/GPU benchmarks or downsample the master reflexively |
| `Requested Metal backend unavailable` | Device unavailable/unsupported, wrong executable, or non-macOS host | Run `pipeline check`. General CLI supports CPU/auto; the v010 production runner does not. A production device-port change requires explicit implementation scope |
| Missing texture path after moving project | Absolute image path from original Mac, external source absent, image not packed | Inspect packed-file status first. v010's four 8K maps are packed. Preserve original source manifest/checksums for rebuilding; do not overwrite source files or use silent low-res replacements |
| Source checksum mismatch | Wrong/corrupt file or intentional change to a source under the same name | Stop the stage; compare local manifest hash and byte count. Recover exact original data through an authorized recovery task. Do not edit expected hashes just to pass |
| Stage reports existing log/scene | Overwrite protection or a previous partial stage | Preserve evidence, inspect status/log, and use a new attempt directory. Removing a log is not a safe resume mechanism |
| v010 command rejects `--device`, `--output` or legacy config | Wrong CLI/schema; full production config required | Use `pipeline.production --help` and the baseline replay instructions. Do not pass split material/studio snapshots or old `lookdev_config.json` into the v010 runner |
| `pipeline render/export` fails on v010 | Foundational CLI requires `effective_config.json` and uses technical cameras/product selection | Do not add a fake effective config to v010. Use the correct renderer; plan GLB delivery separately |
| GLB differs from Cycles master | Unsupported node math, missing baking, different reflection environment, incorrect object selection or real-time tone mapping | Retain the master and create a separate baked delivery scene. Validate actual glTF materials and selected wraps in the future target viewer. Export success alone is insufficient |

## Safe inspection commands

Run from the project root. These entry points were executed in the documentation
audit and do not render/save scenes:

```sh
rtk proxy python3 -B -m pipeline check
rtk proxy python3 -B -m pipeline --help
rtk proxy python3 -B -m pipeline.production --help
```

For parameter questions, read the existing
[final full config](../../outputs/packaging/private-edition-v010/config_final.json),
[material snapshot](../../outputs/packaging/private-edition-v010/material_config.json),
[studio snapshot](../../outputs/packaging/private-edition-v010/studio_config.json),
[events](../../outputs/packaging/private-edition-v010/events.jsonl) and
[validation](../../outputs/packaging/private-edition-v010/validation.json).
`pipeline.production verify` writes files; it is not a read-only audit command.

Do not import historical Casio scripts, execute builders for inspection, run browser
QA or initiate a render/adjust loop. Report concrete remaining issues and let the
designer select the next visual change.
