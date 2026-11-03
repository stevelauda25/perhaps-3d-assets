> **Historical (pre-rename).** Essential is now `spark`; its outputs were removed. Approved: spark-v002. See [WORKSPACE_CLEANUP.md](WORKSPACE_CLEANUP.md).

# Essential v001 pilot report (2026-10-30)

Job `jobs/essential-v001.json` → `outputs/jobs/essential-v001/`. Pending designer review; no visual QA was run
(only numeric exposure/clipping stats on the crops: no pixels ≥0.98, medians 0.31–0.52).

## Measured (from `events.jsonl` / `state/*.json`; Blender 5.2.3, M4 16 GB, Metal)

| Stage | Seconds | Peak RSS MB | Notes |
| --- | --- | --- | --- |
| look (open v010, swap materials, cards, save) | 4.7 | 924 | scene 327 MB → 3.8 MB |
| crop-material (diagnostic) | 12.7 | 1025 | |
| crop-branding (diagnostic) | 24.3 | 2696 | |
| preview-hero (50 %, 64 spp) | 9.7 | 2769 | |
| hero (final, 512 spp, 2048², PNG+EXR) | 109.7 (render 107.2) | 5007 | |

- Job wall-clock: first pass (look + 3 diagnostics/preview, exposure/albedo setup run) 58.4 s; second pass after one
  config change (exposure +1 EV, exterior albedo) 161.1 s including the final hero. Total Blender executions: 10
  (4 + 5 + 1 forced `look` for the skip test), 0 failures.
- Skipping: full rerun with no change → 5/5 skipped, 0.0 s. Forced `look` rerun with identical output left every
  downstream stage fresh (chain hash unchanged). Same-job double run rejected by `.job.lock`.
- Output sizes: hero.png 11.9 MB, hero.exr 9.0 MB, look.blend 3.8 MB, crops 1.2/4.6 MB, preview 2.9 MB.
- Token usage: **not available** to the agent in this session; nothing is claimed.
- Agent wall-clock: not instrumented (no timer was started); not reported.
- Historical comparison: docs record 30–60 min for the previous workflow; the Private Edition v013 job took 193 s.
  Essential's total render+scene time here is ~220 s across both passes. This is the same job system, so the gain
  is carried by the runner, not by anything new in this pilot.

## Added

- `pipeline/tier_materials.py` (builder registry; `paperboard` builder), `pipeline/steps/packaging_tier.py`
- `config/tiers/essential.json` (full), `signature.json` (paperboard, `extends` essential; untested render-wise),
  `select|reserve|private_edition.json` (`pending-builder`: bookcloth / microsuede / leather builders not written)
- `jobs.py`: a stage's `params.preset` file hash now joins its fingerprint (editing the preset reruns the stage).

## Facts and caveats

- Geometry lock verified before/after `look` (job did not fail). Exterior = the v010 removable wrap meshes with new
  materials; stitching curve is hidden for render. Bevel/die-lip profile and the wordmark outline are the v010 ones,
  not Essential-specific; the wordmark is the existing recessed geometry, not a new Essential branding treatment.
- All four 8K leather maps (including the unused height map) are absent from the new scene because the swapped
  materials were the only users; protected v010 files are untouched.
- Paper is procedural (object-space noise, no licensed texture). Reflections come from the v010 card layout
  (`studio.lights` in the preset); the one adjustment was +1 EV and a lighter albedo.
- Multi-agent: per-job dirs, locks (job / Blender slots / GPU slot) were already verified; only the same-job lock
  was re-tested here. A concurrent pair of GPU renders was not run.

## Review paths

`outputs/jobs/essential-v001/{hero.png,hero.exr,preview-hero.png,crop-material.png,crop-branding.png,look.blend}`
