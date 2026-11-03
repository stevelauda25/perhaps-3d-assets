# Performance and token audit (2026-10-30)

Hardware verified by `pipeline.jobs check`: Blender 5.2.3 LTS, Apple M4 10-core Metal,
16 GB. **Verified** = measured from logs, transcripts or runs listed here.
**Estimate** = reasoned, not measured.

## Where the 30–60 minutes go

Sources: the five Codex sessions in this workspace (Oct 24–29,
`~/.codex/sessions/2026/10/**`), stage logs/events under `outputs/packaging/`, and
read-only Blender probes run during this audit.

| Session start | Model requests | Avg / max context (k tok) | Input tokens (cached) | Tool calls | Image views | Largest text outputs (k chars) |
| --- | ---: | --- | --- | ---: | ---: | --- |
| 10-24 18:16 | 419 | 114 / 206 | 45.9M (98 %) | 386, incl. 107 `sleep` polls | 92 | 27, 22, 20 |
| 10-24 18:31 | 137 | 173 / 284 | 21.4M (98 %) | 121 | 43 | 39, 24, 16 |
| 10-28 16:43 | 97 | 232 / 415 | 22.5M (99 %) | 91 | 35 | 44, 42, 41 |
| 10-29 10:54 | 52 | 114 / 176 | 25.6M (98 %) | 48 | 12 | 43, 26, 23 |
| 10-29 15:08 | 64 | 141 / 243 | 34.5M (96 %) | 60 | 18 | 41, 37, 34 |

Blender compute per iteration (verified): scene open 4.0 s + 3.4 s to touch the four
packed 8K maps, 2.9 GB RSS; final 512-sample views 72–102 s each (v010: 4 views
381.7 s; v011: 168.7 s; v012: 156.0 s for 2 views); diagnostic crops 8–15 s.
A full v011/v012-style iteration is therefore **≈3–7 min of Blender time**. The rest
of a 30–60 min task is agent turns: input tokens ≈ requests × context size, and every
request waits on the model.

### Top three bottlenecks (verified, ranked by impact)

1. **Context accumulation × request count.** 52–419 requests at 114–232k tokens each.
   Context is inflated by multi-file `cat` dumps of 20–50k chars (the same
   `RTK.md`, skill files and 293-line legacy `MASTER_PROMPT_V2.md` re-read in several
   sessions), 12–92 image views, ~25k tokens of mandatory docs before any work, and
   polling (107 `sleep` calls in one session, each a full-context request).
2. **Prompt-driven bespoke scripts.** Each version is a new hand-written 240–255-line
   script (`build_v011.py`, `build_v012.py`) that re-implements open → edit → save →
   render. Writing, reading and debugging that code costs most of the requests, and
   coupling edit with render means any rerun repeats everything.
3. **Full-quality renders for targeted questions.** v011/v012 answered wordmark
   questions with full 512-sample frames (≈75–90 s each); v010 had already shown that a
   256-sample border crop at final pixel density answers a material question in 8–15 s.

Not bottlenecks (verified): Blender startup/scene load (≈3.5 s per process), shader
setup and texture checksum/pack (look stage 5.4–5.9 s including a 327 MB save).

## What changed

| Problem | Change |
| --- | --- |
| Bespoke script per version | `jobs/<id>.json` + reusable steps; a look change is a parameter edit |
| Everything reruns | Stage fingerprints; unchanged stages skip, render-only edits rerun one render |
| Verbose logs in context | One JSON line per stage, logs on disk, ≤1500-char error tail |
| Polling | `run`/`batch` block until done and print results; no `sleep` loops needed |
| Large mandatory reading | One ~130-line workflow page + job file for routine work |
| Unbounded parallel renders | `flock` GPU slot (default 1) + Blender memory slots (default 2) |
| Shared-file collisions | Output fixed to `outputs/jobs/<id>/`; per-job lock; atomic state writes |
| Legacy MCP-first Codex agent prompt | `.codex/agents/asset-builder.toml` now points to the job workflow |

## Measured after (same machine, `selftest-private-edition` and `casio-f91w-preview`)

| Operation | Result |
| --- | --- |
| Unchanged job rerun | 0.3 s wall, 0 Blender processes (all 3 stages skipped) |
| Crop border change | Only `crop-leather` reran: 11.5 s; look stage and preview skipped |
| Leather roughness change | `look` 5.9 s + both renders; geometry lock still `81e2f2c9…` |
| Process overhead per render stage | ≈3.5 s (12.7 s wall vs 9.2 s render, hero preview) |
| Two agents rendering at once | Second printed `waiting` on `gpu`, queued 2.0 s, then ran |
| Same job started twice | Second exits immediately: "already running in another process" |
| Bad camera name | `failed` + 6-line traceback tail, exit 1, log path |
| Peak RSS | Scene stage 1.4 GB; Private Edition render stage 3.9 GB; Casio render 2.1 GB |
| Render settings recorded | Standard / None / −0.25, 12 bounces, light tree, 1 px filter = v010 |

`private-edition-v013` (v010 look values, `final` profile), first full run 193.2 s wall:

| Stage | Wall s | Render s | Peak RSS | Same view, old path |
| --- | ---: | ---: | ---: | --- |
| look (rebuild leather, verify lock, save) | 6.0 | – | 1.3 GB | – |
| crop-leather (diagnostic, 256) | 11.0 | 8.6 | 3.1 GB | v010 crops 8–15 s |
| hero (final, 2048) | 94.5 | 90.5 | 4.3 GB | v010 100.2, v011 92.3, v012 83.6 |
| branding-macro (final, 1536) | 81.7 | 78.1 | 3.9 GB | v010 101.6, v011 76.4, v012 72.4 |

Recorded settings: 512 / 0.003 / denoise, 12 bounces, light tree, 1 px filter, Standard /
None / −0.25; lock `81e2f2c9…` before and after; 16-bit RGB PNG + half EXR. Immediate
rerun: all four stages skipped, 0.0 s. Render time is within the old path's run-to-run
spread: the runner does not make a single render faster; the saving is in skipped work
and agent turns. `look.blend` is the same size as the v010 scene but not byte-identical
(node trees are rebuilt); visual parity is for the designer to judge.

**Estimate, not measured:** a routine look-tweak task becomes ~5–10 agent requests
(read one page + job file, edit a number, run, report) instead of 50–140, and context
stays near 10–20k tokens instead of 114–232k, so input tokens drop by well over 50 %.
Verify by running the next real task this way and repeating the transcript query below.

## Re-measuring token use

```sh
python3 - <<'PY'
import glob, json, os
for f in sorted(glob.glob(os.path.expanduser('~/.codex/sessions/2026/*/*/*.jsonl')))[-5:]:
    reqs, last = 0, None
    for line in open(f):
        p = json.loads(line).get('payload') or {}
        if p.get('type') == 'token_count' and p.get('info'):
            reqs += 1; last = p['info']['total_token_usage']
    print(os.path.basename(f)[8:27], reqs, last)
PY
```

## Recommended next steps

- Port v011/v012 wordmark/deboss logic into a `packaging_wordmark` step so branding
  changes become parameters too (needs one diagnostic crop to confirm parity with v012).
- Tier material steps for Essential–Reserve once their sources are qualified.
- The unconnected 8K height map is packed in every saved scene (107 MB). Dropping it
  from *new* job scenes would cut disk and load time with no expected visual change,
  but it alters scene content: designer decision.
- Model choice: strongest available model for new steps and debugging; a faster
  model for job-file edits, runs and batch orchestration. Codex `asset_builder` is set
  to `medium` effort; nothing provider-specific is required by the runner.
