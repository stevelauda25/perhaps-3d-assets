# Gemini CLI entry point

**Routine production** (job runs, parameter changes, renders, batches): read only
[docs/3d/OPTIMIZED_PRODUCTION_WORKFLOW.md](docs/3d/OPTIMIZED_PRODUCTION_WORKFLOW.md)
and the job file. Read the documents below only for new steps, geometry or debugging.

Read [AGENTS.md](AGENTS.md), [3D entry point](docs/3d/README.md),
[canonical workflow](docs/3d/PRODUCTION_WORKFLOW.md), and
[v010 baseline (historical)](docs/3d/BASELINE_V010.md), [cleanup report](docs/3d/WORKSPACE_CLEANUP.md). Follow those shared documents; do not
maintain a separate Gemini production workflow.

- Tiers live only in [config/tiers.json](config/tiers.json) (`spark`, `wonder`, `select`, `prestige`, `icon`; names are provisional). Approved: Spark v002, Icon v014. Wordmark on the box stays `perhaps`.
- Canonical geometry base: `assets/canonical/box_base.blend` + `geometry_lock.json`; geometry, controls, transforms, origins, bevels and seam stay locked.
- Use Blender Python / CLI; MCP is optional. Inspect actual references/configs before appearance changes.
- Use new output directories; preserve approved assets, original sources and the separate watch/application work.
- Manual designer approval only: no automated visual QA, similarity or screenshot/polish loops.
- Technical success is not proof of photorealism or 90–95% similarity.
- No destructive commands or dependency installation without task-specific justification.
