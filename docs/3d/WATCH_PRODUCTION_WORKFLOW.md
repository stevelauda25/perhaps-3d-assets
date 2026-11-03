# Watch asset production workflow (reference-first)

Status: **method proven on the Omega Speedmaster Moonwatch Professional 310.30.42.50.01.001 (Hesalite, black dial)**, latest
version `v014`. Nothing here is approved: approval is manual and the designer's alone. Technical measurements below are inputs
and aids, never a visual or photorealism score.

Use this for any new watch (or other small hard-surface product with printed faces). Box work keeps using
[OPTIMIZED_PRODUCTION_WORKFLOW.md](OPTIMIZED_PRODUCTION_WORKFLOW.md); the job runner, render profiles and stage fingerprints are shared.

## 1. What the method is (and is not)

The asset is **not sculpted or CAD-modelled and not a downloaded model**. A Python build step creates the meshes from
**measurements traced off clean product photos**: lathes (case, bezel, crystal, pusher/crown barrels), lofted rings (fluted crown),
planar prisms and SubD slabs (lugs, shoulders, links), traced vector shapes (dial print, hands). Every number lives in a spec JSON
so a correction is a one-line config change and an incremental re-run, not a remodel.

```text
reference dossier (Phase 0) -> trace to JSON (Phase 1) -> spec JSON + build step (Phase 2)
  -> same-pixel comparison job, white kit (Phase 3) -> presentation job, dark kit (Phase 4) -> designer review
```

Why this is fast: lightweight scene (about 4 MB build, 5 MB with kit), no textures except two small steel maps, previews 10-15 s,
comparison renders about 25 s, reruns skip unchanged stages.

## 2. Phase 0: study the references BEFORE any modelling (the step that saves the most iterations)

Most wasted iterations in the Speedmaster work came from modelling first and discovering the reference problem afterwards
(wrong scale anchor, distracting references, a glare traced as print, shapes guessed that a macro crop would have shown).
Do all of this first and write the result into `references/<product>/REFERENCE_PLAN.md` + `sources.md`.

### 2.1 Required reference set

| # | View | Must be | Used for |
| --- | --- | --- | --- |
| 1 | **Front, straight-on, white or transparent background, >= 2000 px** | official render or catalogue cut-out, bracelet straight | everything planform: silhouette, dial, print, hands, bezel, lugs, bracelet columns |
| 2 | Back, straight-on | same standard | caseback ring, lug undersides, engraving |
| 3 | 3/4 view(s), clean white | studio photo/render, preferably >= 1500 px | heights (crown, pusher, lug slope) via camera registration |
| 4 | Macros: crown, pushers, dial, bracelet link, clasp | native resolution (not web thumbnails) | shapes that are invisible at 1:1 (see 2.3) |
| 5 | Side profile and lug-end view | orthographic if at all possible | case height profile, lug twist. Rarely public: if missing, say so and ask the owner for photos (REFERENCE_PLAN.md "Ways to close the gap") |

Reject: lifestyle/wrist shots, dark-background galleries, anything with props or tables, thumbnails upscaled. The designer will
reject a build matched to a distracted reference; ask for or find clean ones first. Record each source, size and what it is used for.

### 2.2 Scale anchor: two independent verified dimensions

Take the manufacturer's numbers (diameter, thickness, lug-to-lug, lug width) and anchor pixels to millimetres with **two different
measured features**, never one. For the Speedmaster: lug tip = half of 47.5 mm and bracelet width at the lugs = 20 mm gave
23.7709 px/mm. Anchoring on the black bezel insert alone was **2.2 % small** because the stated 42 mm is the outer steel ring.
`pipeline/watch_trace.py` does the two-pass anchor and the build step **asserts** the verified numbers, so a wrong anchor fails loudly.

### 2.3 Macro study checklist (do this with 4x crops, region by region)

Crop and upscale the best reference (`PIL` crop + `LANCZOS` x4) and write down, per region, what the real part is:

* **Crown**: flat flutes or round? how many? profile along the axis (collar, chamfered ends, shoulder radius), end emblem size and relief.
* **Pushers**: plain cylinder or flanged? face-edge fillet, neck, tilt angle (from the silhouette), length.
* **Case flank and shoulders**: continuous polished mass or separate guards? where does the edge peak (read it from the traced
  silhouette between crown and pushers instead of guessing).
* **Lugs**: sloping brushed top, polished outer chamfer (dark in studio shots), root where the lug meets the case.
* **Bracelet**: columns and widths, row pitch, which columns share joints, staggered rows, link end shape, taper, end links reaching the case.
* **Dial**: print list (logo, script, numerals, ticks), sub-dial recess step, texture/grain, applied indices and lume frames, hands (outline, lume inlay, hub).
* **Bezel**: black band vs steel ring radii, numerals/dots, radius of the numeral baseline.
* **Reference artefacts**: crystal glare crescents, perspective asymmetry (the Omega render is about 4 % bigger at the bottom, right lugs
  about 0.5 mm wider), reflections that a tracer would mistake for print. Mark them so they are not copied.

### 2.4 Output of Phase 0 (gate before Phase 1)

A short table in `REFERENCE_PLAN.md`: per part -> true shape, measured values or "measure in Phase 1", source image, open question.
Anything not visible in any reference is listed as a **known gap** and shown to the designer, not invented silently.

## 3. Phase 1: measure and trace (host-side, numpy + OpenCV, no Blender)

```sh
python3 -B -m pipeline.watch_trace            # silhouette per y, index bars, hubs, link edges -> config/watches/speedmaster-trace.json
python3 -B -m pipeline.watch_print            # dial/sub-dial/track/bezel print as vector outlines -> speedmaster-print.json
python3 -B -m pipeline.watch_hands            # hands + lume inlays, hand-local -> speedmaster-hands.json
python3 -B -m pipeline.ref_register config/watches/ref_landmarks/bobs_3q.json   # camera pose of a 3/4 photo from the 12 lume bars (planar PnP)
```

Tracing rules learned the hard way:

* Thresholds are in **true mm**, not pixels.
* Print = everything bright that is not lume or a hand. A crystal glare crescent passes that test: `watch_print.py` caps the area of
  track blobs, and a leftover sliver (track shape 13) was removed by hand from `speedmaster-print.json` (the file's `source` says so;
  **regenerating the file means deleting it again**).
* Hands overlapping print leave a gap in the print (the 3D hands cover it).
* Traced polylines are pixel-jittery: simplify (`rdp` in the build step) before offsetting, or mitre inset produces spikes.
* Height (z) cannot come from the front view. Register a 3/4 photo (`ref_register`, 1.8 px reprojection achieved) and fit z by same-camera
  silhouettes (`pipeline/ref_overlay.py`), or measure from a side view if you have one.

## 4. Phase 2: spec + build step

* Spec: `config/watches/<product>-vNN.json`. One version file at a time; bump the version when keys change shape, keep only the latest.
  Keys (Speedmaster v11): `verified_mm`, `case` (flank, lug, guard), `bezel`, `crystal`, `dial`, `hands`, `crown`, `pushers`, `bracelet.columns`,
  `faceted`, `materials`, `trace`/`print`/`hands.traced` file references.
* Build step: `pipeline/steps/watch_speedmaster_v3.py` (reuse for a similar watch; its helpers `Geo`, `rot`, `rect` live in
  `pipeline/steps/watch_speedmaster.py`; SubD/faceted slabs in `pipeline/subd.py`). Input scene: `assets/watches/baseline/casio_studio_base.blend`
  (built by `pipeline/watch_base.py`).
* Materials are **library roles** (`library_roles` in the job): `steel_brushed`, `steel_polished`, `steel_links` (grain along the
  bracelet), `bezel_black`, `dial_black`, `print_white`, `lume`, `hesalite`, plus plain roles in the spec (`hand_white`, `steel_gap`).
  Presets in `config/material_library/`; steel uses two small CC0 maps (Metal009 brushed, Metal012 polished).
* Job fingerprints include the spec, the trace/print/hands files named in it and the loaded pipeline modules, so edits re-run only what changed.

### 4.1 Build order (front planform first, then depth)

1. Silhouette-driven planform: case lathe, lugs (per side, from the traced outline), shoulders, bezel + steel ring, crystal.
2. Dial: base, sub-dial recesses, indices (frames + lume), traced print, traced hands, hubs.
3. Crown, pushers (measured centres/tilt), case shoulders.
4. Bracelet: columns, per-row links, joints, taper, backing plate.
5. Only then: back, clasp, 3/4 cross-checks.

### 4.2 Shape rules that held up

* Link = rounded rectangle in the y-z profile (corner radius about 0.9 x half thickness), flat brushed top, polished chamfer via bevel
  material slot, dark backing plate (`steel_gap`) so gaps read as shadow lines.
* Crown = star polygon rings lofted along the axis with flat shading (each flute catches its own reflection), ends scaled down for the chamfer,
  small domed emblem disc; do not use one smooth cylinder.
* Pusher = plain polished lathe with a 0.6 mm face fillet and a narrower neck; no decorative flange.
* Shoulders = one polished faceted slab whose outline comes from the traced edge, up to the case-top height, so it reads as one piece with the case.
* Never use a silhouette edge that includes a neighbouring part (the right edge beside the pushers is the pusher, not the lug).

## 5. Phase 3: same-pixel comparison (the loop, kept short)

Job `jobs/omega-speedmaster-black-v013.json`: `build` -> `kit` (`watch_kit_white_front.json`, orthographic front camera at the reference scale) ->
`cmp-front` (render profile `comparison`: full resolution, 96 spp, about 25 s).

```sh
python3 -B -m pipeline.jobs run jobs/omega-speedmaster-black-v013.json
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup --disable-autoexec --python pipeline/front_silhouette.py -- \
    outputs/jobs/omega-speedmaster-black-v013/build.blend /tmp/sil.png
python3 -c "from pipeline.front_compare import silhouette_report; print(silhouette_report('/tmp/sil.png','/tmp/diff.png'))"
python3 -c "from pipeline import front_compare as fc; fc.board('outputs/jobs/omega-speedmaster-black-v013/cmp-front.png','board.png',['crown_right','dial_centre'])"
```

How to run the loop with **few iterations**:

1. Compare **all regions in one board** (add regions to `front_compare.REGIONS`) and write the full list of differences before touching the spec.
2. Fix **by cause category in one pass**: planform (silhouette) first, then part shapes, then shading/material, then print/hands, last lighting.
3. Re-run once, re-board once. Use `silhouette_report` (IoU per band: case, lugs, bracelet) only to see where the outline is off; it is not a quality score.
4. Differences caused by the **white kit** (crystal veil greying the dial, light-card reflections) are lighting, not shape: do not chase them in geometry.
5. A sudden improvement from a clean change (e.g. a dark backing exposing a profile bug) means the previous look was hiding a defect: debug by
   making problems visible (dark plate, flat shading, wire boards) instead of tuning materials.
6. Hand the designer **one board per round** with the remaining differences listed; their red/green annotations drive the next round.
   No automated visual QA, similarity gate or screenshot loop decides anything.

## 6. Phase 4: presentation scene

Job `jobs/omega-speedmaster-black-v014.json`: same build, kit `config/presets/watch_kit_front.json` (reflection-first kit: emissive gradient cards,
black flags, gradient world, compositor glow/vignette), cameras `front_ref` and `front_ref_macro`, 4:5 portrait, render profile `preview` for review.
Final quality only after designer approval (`final` profile).

Kit facts: the kit forces Cycles (an empty input scene defaults to EEVEE); orthographic scale is in metres; `preview` halves the resolution;
in Blender 5.2 the compositor is `scene.compositing_node_group` with a `NodeGroupOutput`.

## 7. Pitfall table (symptom -> cause -> rule)

| Symptom | Cause | Rule |
| --- | --- | --- |
| Everything 2 % too small | scale anchored on the black bezel insert | two independent verified dimensions, assert them |
| Pill-shaped, banded links | twisted/self-crossing link profile | build the profile as a proper closed rounded rectangle; expose bugs with a dark plate |
| Spikes at lug corners | mitre inset on jittery traced outline | `rdp` simplify, cap mitre (`subd.inset` 0.45) |
| Notch beside the lug root | outline switched from left to right edge with a 0.4 mm step | blend edges over 3 mm (`lug.sym_until_y`) |
| White crescent on the dial | glare in the reference traced as print | exclude by area, review traced shapes on an overlay |
| Swirl brushing on links | tangent about Z | tangent about the bracelet axis (`steel.brushed-links`, axis X) |
| Fingerprint did not change after editing a trace | job hashed only the spec | `param_files` hashes files named inside the spec (fixed in `jobs.py`) |
| Comparison looked half size | `preview` profile scales 50 % | use `comparison` profile |
| Dial grey in comparison | crystal reflecting the white kit | lighting only, ignore for shape work |
| Ref picture misleading | perspective/asymmetry in the render | note it, model the verified symmetric value |

## 8. Files that make the final asset work (kept)

* Jobs: `jobs/omega-speedmaster-black-v013.json` (comparison), `jobs/omega-speedmaster-black-v014.json` (presentation).
* Spec and traces: `config/watches/speedmaster-moonwatch-black-v11.json`, `speedmaster-trace.json`, `speedmaster-print.json`, `speedmaster-hands.json`, `ref_landmarks/`.
* Kits: `config/presets/watch_kit_front.json`, `watch_kit_white_front.json`, `watch_kit_white.json` (registered 3/4 cameras).
* Materials: `config/material_library/` presets `steel.brushed-aniso`, `steel.brushed-links`, `steel.polished-clean`, `aluminium.anodised-black`,
  `dial.matte-black`, `print.white-bright`, `lume.bright`, `glass.hesalite-v2` and textures `textures/sources/ambientcg_metal009_2k`, `ambientcg_metal012_1k`.
* Code: `pipeline/steps/watch_speedmaster_v3.py`, `watch_speedmaster.py` (shared helpers), `watch_kit.py`; `pipeline/subd.py`, `pbr_material.py`,
  `material_library.py`, `watch_trace.py`, `watch_print.py`, `watch_hands.py`, `watch_base.py`, `ref_register.py`, `ref_overlay.py`,
  `front_compare.py`, `front_silhouette.py`; `config/render_profiles.json`.
* Inputs: `assets/watches/baseline/casio_studio_base.blend` (studio base), `assets/casio-f91w/` (original Casio asset), `references/omega-speedmaster-310-30-42-50-01-001/`.
* Latest outputs: `outputs/jobs/omega-speedmaster-black-v013/` (comparison) and `-v014/` (presentation previews).

Superseded jobs (v001-v012), specs (v3-v10), kits, presets and outputs were moved aside during the 2026-11-03 cleanup and then deleted on the
user's confirmation; v013/v014 and the files above are the only watch versions kept.

## 9. Known gaps (as of v014)

Dial grain and sub-dial recess bevels; steel reads duller in the dark kit than in studio shots; lug outer chamfer should be dark polished;
crown emblem has no Omega engraving; side profile and lug-end heights are inferred from a registered 3/4 photo; back view and clasp
not yet compared; final-quality render not run. Pose with the bracelet closed into a loop is not built (only the straight pose).

## 10. Starting a new watch: shortest path

1. Phase 0 dossier (references, scale anchors, macro study, known gaps) and get the designer's OK on the reference set.
2. Copy `watch_trace.py`/`watch_print.py`/`watch_hands.py` constants for the new reference, run them, look at the overlays once.
3. Copy the spec (latest version) and step, change numbers, **run the comparison job once**, review one multi-region board.
4. Fix by category (4.1 order), re-run, then the presentation job. Expect 3-4 rounds, not 13.
