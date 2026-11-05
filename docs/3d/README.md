# Perhaps 3D production documentation

Approved assets: **The Spark Box v002** and **The Icon Box v014** (tier registry: [config/tiers.json](../../config/tiers.json)).
The canonical packaging geometry is approved and locked (`assets/canonical/`). v010 was the
earlier baseline; its outputs were removed in the [workspace cleanup](WORKSPACE_CLEANUP.md).
Approval does not certify a pixel-perfect match.

The system produces editable Blender masters and actual Cycles product images:

```text
AI coding agent → configuration / Python → Blender CLI / bpy → Cycles renders
                → manual designer review → future baked GLB delivery
```

## Read in this order

0. [Job-based workflow](OPTIMIZED_PRODUCTION_WORKFLOW.md): **start here for routine
   production**; parameter-driven jobs, incremental stages, render queue. Enough on its own
   for look changes and renders. [Job spec](ASSET_JOB_SPEC.md),
   [performance audit](PERFORMANCE_AND_TOKEN_OPTIMIZATION.md).
0b. [Watch workflow](WATCH_PRODUCTION_WORKFLOW.md): **watch assets**. For Casio reference-based GLB delivery, start at section 0: `cc-blender-skill`, base reuse, reference preparation/export at 2× or higher, HTML viewer review and SKU-based publishing. Sections 1–10 cover the full-model Speedmaster pipeline.
1. [Production workflow](PRODUCTION_WORKFLOW.md): the canonical operating procedure,
   safety policy, command selection and extension workflow.
2. [v010 baseline](BASELINE_V010.md) (historical; artifacts removed, see cleanup report): exact scene, settings, integrity manifest,
   reproduction instructions and outstanding limitations.
3. [Reference and asset specifications](REFERENCE_AND_ASSET_SPECS.md): common box
   construction, tier materials and the visual acceptance contract.
4. [Troubleshooting](TROUBLESHOOTING.md): symptom-to-source inspection guide.

Maintain this documentation system rather than adding competing agent workflows.
The root [AGENTS.md](../../AGENTS.md), [CLAUDE.md](../../CLAUDE.md) and
[GEMINI.md](../../GEMINI.md) are thin entry points. The older root
[README](../../README.md) retains implementation history; its older "current"
descriptions are superseded by this documentation and the verified v010 snapshot.

## Quick start: inspect first

Run from the project root. These commands were executed successfully during the
documentation audit and do not render or save Blender scenes:

```sh
rtk proxy python3 -B -m pipeline --help
rtk proxy python3 -B -m pipeline.production --help
rtk proxy python3 -B -m pipeline check
```

The current workstation root is `/Users/admin/Documents/perhaps-3d-assets`.
On another machine, use the copied project's root. `rtk proxy` is the local shell
convention; if RTK is unavailable elsewhere, run the same Python command without
that wrapper. Do not install tooling merely to read this project.

Open these existing artifacts for review:

- [Final editable v010 scene](../../outputs/packaging/private-edition-v010/private_edition_calibrated.blend)
- [Actual hero](../../outputs/packaging/private-edition-v010/hero.png) and
  [reference comparison](../../outputs/packaging/private-edition-v010/hero_comparison.png)
- [Approved canonical master](../../outputs/packaging/canonical-v001/canonical_box.blend)
- [Original Private Edition reference](../../references/packaging/06_private_edition.png)
- [Production implementation](../../pipeline/production.py) and
  [final working config](../../config/private_edition_production.json)

For reproduction, follow the [baseline recovery procedure](BASELINE_V010.md#recovery-and-reproduction).
Do not run production stages with the shipped default output: v010 already exists.

## Master scene versus real-time delivery

The Blender master preserves original 8K sources, Cycles node graphs, debossed
appearance wraps and photographic reflection cards. A GLB/React Three Fiber asset
needs a separate delivery scene, appropriate texture baking, selected geometry and
real-time lighting validation. The foundational GLB utility exists, but v010 has
not been baked or qualified for real-time delivery. A successful export would not
prove parity with the Cycles master.

This documentation audit created no model, render, material update or GLB.

## Handoff to a new agent

```text
Read AGENTS.md and docs/3d/README.md, then docs/3d/PRODUCTION_WORKFLOW.md and
docs/3d/BASELINE_V010.md. Treat Private Edition v010 as the selected best baseline,
preserve the locked geometry and historical outputs, inspect actual references and
configs, and continue only within the requested task's scope.
```
