# Workspace cleanup and tier rename (2026-10-30)

Provisional tier names; ids are stable. Registry: [config/tiers.json](../../config/tiers.json) (the only place for names, prices, status, versions, paths).

| id | Display name | Was | Price | Status |
|---|---|---|---|---|
| `spark` | The Spark Box | Essential | $50 | approved, v002 |
| `wonder` | The Wonder Box | Signature | $100 | config only (preset `wonder.json`) |
| `select` | The Select Box | Select | $250 | config only |
| `prestige` | The Prestige Box | Reserve | $500 | config only |
| `icon` | The Icon Box | Private Edition | $1,000 | approved, v014 |

The physical wordmark stays `perhaps`. Version numbers kept.

## Approved baselines
- **spark-v002:** `outputs/jobs/spark-v002/` (`look.blend` with packed 2K Paper006 maps, crops, preview hero). Job `jobs/spark-v002.json`. Final `hero` stage is still unrendered.
- **icon-v014:** `outputs/packaging/icon-v014/` (scene, 3 external 2K maps, manifests, previews). Job `jobs/icon-v014.json` renders it (outputs in `outputs/jobs/icon-v014/`).
- **Shared canonical base (new):** `assets/canonical/box_base.blend` + `geometry_lock.json`, taken from v010 with all texture images detached (3.7 MB instead of 327 MB). Spark's `look` stage re-run on it gave 0 signature differences against the approved Spark scene (objects, materials, lights, cameras, scene settings). Both approved jobs use this lock. The lock's informational `source` field still names the deleted v009 file.

## Migration decisions
- Moved (not copied): `essential-v002` → `spark-v002`, `private-edition-v014` → `icon-v014`, v014 review job → `icon-v014`. Blend files untouched; Icon textures are relative so they still resolve.
- Job ids/inputs/lock/preset paths updated. Stage fingerprints were re-stamped (outputs unchanged), so `jobs run` skips completed stages (verified).
- Tier presets renamed `config/tiers/{spark,spark-v002,wonder,select,prestige,icon}.json`; `config/materials.json` keys renamed; `price_usd` removed from presets (registry only). Paper006 library entry marked approved (`spark-v002`); no parameter changed.
- Kept historical names: material names inside scenes (`Essential | exterior`, `PE6 | …`), reference file names (`01_essential.png`, `06_private_edition.png`), `jobs/material-essential-paper-v001.json`, docs describing v010/Essential history (bannered).
- New runs name materials `Spark | …` (from the tier id), so a rebuilt Spark differs from the approved scene in material names only.

## Removed (manifest verified: all inside the workspace, no symlinks, protected paths excluded, dry-run first, per-file deletion)
329 files / 39 directories, 3,824,433,180 bytes apparent:
- `outputs/packaging/private-edition-v007 … v013` (incl. benchmarks, verification, v012-optimized), 3.2 GB; v010 was 1.1 GB of it.
- Jobs outputs and configs: essential-material-check, essential-v001, selftest-private-edition, old private-edition-v013, v013-validation, pe-v012-* checks.
- `material-essential-paper-v001`: per-variant renders/scenes (comparison.png kept).
- Candidate leather maps: `textures/sources/private-edition-qualification/*.png`, `ambientcg_leather037_2k/*.png` (manifests/catalogs kept; re-downloadable).
- Superseded builders/configs: `pipeline/build_v011.py`, `build_v012.py`, `config/private_edition_v011.json`, `v012.json`.
- Lost with v010: its hero/macro renders and `manual_review.json`/`source_selection.json` provenance.

## Storage (measured, `du`)
| | Before | After |
|---|---|---|
| Workspace | 4,756,268 KB (start) | **1,024,404 KB** |
| Files / dirs | 853 / 103 (pre-delete) | 525 / 64 |

Recovered 3,731,864 KB (78.5 %). Pre-delete figure included 7.3 MB of new canonical base.

Active: spark-v002 29.8 MB (incl. packed 2K maps ≈16.7 MB); icon-v014 package 33.5 MB (textures 14.4 MB, scene 2.6 MB, previews 16.4 MB); its job renders 27.3 MB; canonical base 3.7 MB; references 19.7 MB; Paper006/Paper002 library sources 142 MB.
Historical/unrelated: `assets/casio-f91w` 440 MB (untouched, review-only).

## Left untouched (ambiguous, for your decision)
- `assets/casio-f91w` (440 MB).
- `textures/sources/polyhaven_leather_red_02_8k/leather_red_02_disp_8k.png` (106.8 MB, unused by Icon; source.json has URL + sha256) and the other three 8K originals (Icon's provenance).
- `textures/sources/ambientcg_paper006_2k/a.zip` (52.6 MB archive of already-extracted maps).
- Legacy v007–v010 tooling (`pipeline/production.py`, `realism.py`, `grain_compare.py`, lookdev*, their configs/tests): code kept, but their input folders are gone, so those commands no longer run. `build_v013.py`/`build_v014.py` likewise (provenance only).
- Icon scene contains one empty orphan object, `CTRL | Base.001` (no collection, no children, no effect), from the v013 build; left as is to avoid touching the approved scene.

## Validation
- Unit tests 18/18 (new `tests/test_tiers.py`; the Leather037-file check in `test_lookdev` was dropped; job test now uses spark-v002); `pipeline.jobs check` and `status` run; `jobs batch` runs both jobs.
- Both scenes reopen; canonical lock fingerprint `81e2f2c9…` verifies with the new lock; Spark: 3 packed 2K maps; Icon: 3 relative 2K maps resolved; CTRL objects and 19 cameras present. A scratch Icon crop (8 s, deleted) ran with the new lock.
- Mistake disclosed: `jobs batch` rendered Spark's never-run `hero` stage (104 s). I deleted its outputs, state and log line; Spark is back to 29.8 MB with `hero` pending. No other renders ran.

## Commands
```sh
python3 -B -m pipeline.jobs status spark-v002 icon-v014
python3 -B -m pipeline.jobs run jobs/spark-v002.json      # new tier: copy this file, see OPTIMIZED_PRODUCTION_WORKFLOW.md
python3 -B -m unittest discover -s tests
```
