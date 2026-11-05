# Job-based production workflow (shared by all agents)

This is the **only document an agent needs for routine production**: changing look
parameters, rendering views, batching assets. Read [BASELINE_V010.md](BASELINE_V010.md)
and [PRODUCTION_WORKFLOW.md](PRODUCTION_WORKFLOW.md) only when writing a new step
(new geometry, new material logic) or debugging appearance. Job format:
[ASSET_JOB_SPEC.md](ASSET_JOB_SPEC.md). Audit and measurements:
[PERFORMANCE_AND_TOKEN_OPTIMIZATION.md](PERFORMANCE_AND_TOKEN_OPTIMIZATION.md).

**Materials:** select a library material by ID; see [MATERIAL_FIRST_WORKFLOW.md](MATERIAL_FIRST_WORKFLOW.md). Do not hand-build procedural shaders for a new look.

**Scene size:** `python3 -B -m pipeline.optimize_scene SRC.blend OUT_DIR --name X.blend` makes a lossless portable copy (drops unlinked texture nodes, externalises packed images to `OUT_DIR/textures/`, verifies). Use the copy as a job `input`. Icon v014 package: [optimization_report.md](../../outputs/packaging/icon-v014/optimization_report.md).

## Rules that never change

- Tiers (ids, display names, prices, approved assets) live only in [config/tiers.json](../../config/tiers.json):
  `spark`, `wonder`, `select`, `prestige`, `icon`. Approved: **spark-v002** (`outputs/jobs/spark-v002/look.blend`)
  and **icon-v014** (`outputs/packaging/icon-v014/`). Canonical geometry base for new tiers:
  `assets/canonical/box_base.blend` + `assets/canonical/geometry_lock.json`. Never write into `outputs/packaging/`
  except a new, designer-requested package.
- Jobs write only to `outputs/jobs/<id>/`. The runner rejects any other output.
- Packaging jobs set `geometry_lock`; every scene stage re-verifies the canonical
  fingerprint (`81e2f2c9…`) and fails rather than save a changed box.
- Render profiles touch only sampling/resolution/output. View transform, exposure,
  bounces, filter and lights come from the saved scene. `final` = approved quality;
  do not edit it without designer approval.
- Designer approves visuals. Agents do not view renders to judge quality, score
  similarity or loop on polish. Technical success ≠ photorealism.

## Commands (run from the project root; prefix `rtk proxy` on this workstation)

```sh
python3 -B -m pipeline.jobs check                       # Blender, Metal, memory, slots (one line)
python3 -B -m pipeline.jobs validate jobs/<id>.json     # no Blender, instant
python3 -B -m pipeline.jobs run jobs/<id>.json          # run stale stages, skip unchanged
python3 -B -m pipeline.jobs run jobs/<id>.json --only hero   # one view (+ any stale upstream scene stage)
python3 -B -m pipeline.jobs run jobs/<id>.json --only hero --force   # re-execute named stage
python3 -B -m pipeline.jobs batch jobs/a.json jobs/b.json --workers 2
python3 -B -m pipeline.jobs status [id ...]             # one line per job
python3 -B -m pipeline.jobs report [id ...]             # timing / memory totals from events
python3 -B -m unittest discover -s tests                # host-side spec checks
```

Each stage prints **one JSON line** (`status`, seconds, `rss_mb`, outputs, log path).
Failures add a ≤1500-char error tail. Full Blender logs: `outputs/jobs/<id>/logs/`.
Do not `cat` whole logs into context; `grep -n Error` them if the tail is not enough.

## How a job runs

```text
input .blend ─▶ scene stage(s) ─▶ <stage>.blend ─▶ render stage(s) ─▶ <stage>.png [+ .exr]
               pipeline/steps/*.py                 config/render_profiles.json
```

- **Incremental:** a stage's fingerprint = its spec + render profile + upstream
  fingerprint (input file SHA-256, previous scene stage, and the hashes of every
  `pipeline/` module that stage loaded inside Blender). Unchanged → skipped.
  Changing a camera/border/resolution reruns that render only; changing leather or
  card params reruns the look stage and its renders; geometry is never rebuilt by
  look jobs. Editing a step's code reruns stages that loaded it.
- **Reuse, not rebuild:** packaging jobs start from the saved finished scene (packed 8K
  maps, wraps, cameras, cards). `packaging_look` reuses `production.materials` and
  `reference_studio.refine` with parameters from the job file.
- **Profiles:** `diagnostic` (final pixel density, 256 samples, border required) answers
  one material/lighting question in ~10 s; `preview` (50 %, 64 samples) checks
  composition only; `final` (512, 0.003, denoise, 16-bit PNG + EXR) for designer review.
  Evaluate a parameter with one diagnostic crop, not four full frames.

## Concurrency and file ownership

| Resource | Limit | Mechanism |
| --- | --- | --- |
| Agent / code work | unlimited, one job file per agent | separate `jobs/<id>.json` and `outputs/jobs/<id>/` |
| Same job | 1 process | `outputs/jobs/<id>/.job.lock` (second run exits immediately) |
| Blender processes (memory) | `PERHAPS_BLENDER_SLOTS`, default 2 | `outputs/.locks/blender-N.lock` |
| Cycles GPU renders | `PERHAPS_GPU_SLOTS`, default 1 | `outputs/.locks/gpu-N.lock`; others print `waiting` |

Locks are `flock`s: released automatically if a process dies, no cleanup needed.
Measured on the M4/16 GB: scene open ≈ 2.9 GB RSS, a render stage up to 3.9 GB at
preview size. Keep `GPU_SLOTS=1` until a measured final-render pair proves it safe.
State files are written atomically; `status` reports `stale` for a dead `running` pid.

## Multi-agent pattern

Default: **one agent per asset job**, no sub-agents. Agents never share a job file.

- **Orchestrator (optional, any model):** writes/edits job files, runs `batch`, reads
  the JSON lines and `status`, reports to the designer. It does not open scenes.
- **Step author (strong model, rare):** writes a new `pipeline/steps/<name>.py` when
  a job needs logic that does not exist (new tier material, watch geometry). Reads
  the baseline docs; tests with a `diagnostic` crop; hands back the step name + params.
- **Job worker (fast model):** edits parameters in one job file, runs it, returns
  the result lines. No doc reading beyond this page and the job file.

Geometry / material / studio / render "workers" are stages inside one job, not
separate agents. Parallel benefit comes from independent jobs; the GPU lock
serializes their renders automatically, so `batch --workers 2-3` is safe.

## Handoff (paste this, nothing more)

```text
Read docs/3d/OPTIMIZED_PRODUCTION_WORKFLOW.md and jobs/<id>.json only.
Goal: <one sentence, e.g. "raise exterior roughness max to 0.55 and render the leather crop">.
Constraints: canonical locked geometry; outputs only in outputs/jobs/<id>/; no visual judging.
Return: the JSON result lines from `pipeline.jobs run` and the output paths.
```

To continue unfinished work: `python3 -B -m pipeline.jobs status <id>` then rerun the
same `run` command — completed unchanged stages are skipped, failed ones rerun.

## Adding assets

- **Another box tier (wonder / select / prestige):** copy `jobs/spark-v002.json`, new `id`, `output`, `tier`;
  keep `input: assets/canonical/box_base.blend` and the lock; set `params.preset` to `config/tiers/<tier>.json`.
  `wonder` uses the `paperboard` builder; `select`/`prestige` are `pending-builder` until a builder is added to
  `pipeline/tier_materials.py`. Then set the tier's status/version/paths in `config/tiers.json`.
- **Wordmark:** scene step `logo_deboss` re-cuts the `perhaps` deboss from `references/brand/perhaps-wordmark.svg` (official outlines; params in
  `jobs/spark-v003.json` / `icon-v015.json`: width, depth, lip, `outset_mm`). It replaces only the lid wrap; `python3 -B -m pipeline.package_scene SRC.blend OUT_DIR`
  makes a portable package for external-texture scenes.
- **Icon changes:** `jobs/icon-v014.json` renders the approved scene. Its scene was assembled by historical scripts
  (`pipeline/build_v013.py`, `build_v014.py`; inputs removed, see [WORKSPACE_CLEANUP.md](WORKSPACE_CLEANUP.md)); treat the
  package as the source of truth. Spark history: [ESSENTIAL_V001_REPORT.md](ESSENTIAL_V001_REPORT.md) (pre-rename).
- **Watches:** for Casio reference-based GLB delivery, follow [Watch workflow, section 0](WATCH_PRODUCTION_WORKFLOW.md#0-casio-reference-based-glb-delivery), including skill use, 2× reference export, viewer review and publishing. Watches own `.blend` and steps; no packaging abstractions. A render-only job
  (see `jobs/casio-f91w-preview.json`) never saves a scene, so it cannot alter sources.
