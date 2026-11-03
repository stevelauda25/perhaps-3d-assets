# Perhaps 3D agent entry point

**Routine production** (job runs, parameter changes, renders, batches): read only
[docs/3d/OPTIMIZED_PRODUCTION_WORKFLOW.md](docs/3d/OPTIMIZED_PRODUCTION_WORKFLOW.md)
and the job file. Read the documents below only for new steps, geometry or debugging.

New or changed materials: read [docs/3d/MATERIAL_FIRST_WORKFLOW.md](docs/3d/MATERIAL_FIRST_WORKFLOW.md); use library IDs, no ad-hoc shaders.

Read [docs/3d/README.md](docs/3d/README.md), the canonical
[production workflow](docs/3d/PRODUCTION_WORKFLOW.md), and
[v010 baseline (historical)](docs/3d/BASELINE_V010.md) and [cleanup report](docs/3d/WORKSPACE_CLEANUP.md) before writing steps or changing geometry/material logic.

- Tiers live only in [config/tiers.json](config/tiers.json) (`spark`, `wonder`, `select`, `prestige`, `icon`; names are provisional). Approved: Spark v002, Icon v014. Wordmark on the box stays `perhaps`.
- Canonical geometry base: `assets/canonical/box_base.blend` + `geometry_lock.json`; geometry, controls, transforms, origins, bevels and seam stay locked.
- Reuse Blender Python / CLI; Blender MCP is optional.
- Inspect actual references, scene and configs before changing materials or lighting.
- Preserve source references and approved assets; use new output directories.
- Visual approval belongs to the designer. No automated visual QA, similarity scoring or screenshot/polish loops.
- Technical checks do not certify photorealism or 90–95% similarity.
- Do not run destructive commands or install dependencies without task-specific justification.
- Keep the Casio history and the separate Perhaps application repository untouched unless explicitly requested.

On this workstation, prefix shell commands with `rtk`, per
[/Users/admin/.codex/RTK.md](/Users/admin/.codex/RTK.md). RTK is a local execution
convention, not a Blender dependency on other machines.
