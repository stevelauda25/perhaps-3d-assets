# Reference and asset specifications

This is the design contract supporting the [production SOP](PRODUCTION_WORKFLOW.md).
The [exact baseline](BASELINE_V010.md) records implementation choices; the original
sheets remain visual authority for materials and presentation.

## Tier references

All six original PNGs were present and visually inspected in this documentation
audit. Each is 1024 × 1536 pixels. The
[packaging manifest](../../references/packaging/manifest.json) records the shared
construction, tier labels and reference limitations.

| Tier / label | Original sheets | Material and appearance contract |
| --- | --- | --- |
| The Spark Box (`spark`, was Essential) — $50 | [01_essential.png](../../references/packaging/01_essential.png) | Warm matte beige uncoated paperboard, delicate fibers; ivory satin/matte reveal; subtle serif deboss |
| The Wonder Box (`wonder`, was Signature) — $100 | [02_signature.png](../../references/packaging/02_signature.png) | Terracotta matte paper wrap, fine fibers; ivory reveal; restrained recessed serif |
| The Select Box (`select`) — $250 | [03_select_primary.png](../../references/packaging/03_select_primary.png), [04_select_secondary.png](../../references/packaging/04_select_secondary.png) | Forest-green woven bookcloth, coherent weave/fiber scale; champagne-ivory satin reveal; blind serif branding, exact relief direction requires manual review |
| The Prestige Box (`prestige`, was Reserve) — $500 | [05_reserve.png](../../references/packaging/05_reserve.png) | Oxblood/burgundy micro-suede with directional fibers; restrained champagne brushed metal; recessed serif |
| The Icon Box (`icon`, was Private Edition) — $1,000 | [06_private_edition.png](../../references/packaging/06_private_edition.png) | Obsidian black leather with subtle espresso undertone, rounded grain and fine pores; dark brushed metal; extremely subtle black-on-black lowercase serif deboss and restrained finishing stitches |

The sheets contain hero, front, mirrored left/right, top, rear, bottom, opened and
macro panels. Use both Select sheets; do not treat them as two tiers. They differ
in visible weave, framing and branding, so resolve any appearance discrepancy by
manual review rather than creating separate structural meshes.

## Shared structural contract

- One nearly cubic rigid-box geometry across all five tiers.
- Separate removable lid, base, fitted interior collar/reveal and tray floor.
- Tall front lid, shallow front base, narrow reveal and mirrored diagonal side
  separation. Horizontal front and rear edges occur at different heights in the
  approved continuous construction.
- Precise approved bevels, believable wall thickness and independent opening controls.
- Blank top. Lower-front **lid** branding area: lowercase serif `perhaps`; no logo
  added to the top. "Lower front" does not mean text belongs on the base.
- Lift vertically clear of the fitted collar, then move the free lid aside; no hinge,
  invented magnets or latches.

The canonical dimensions are documented assumptions, now part of the approved asset.
Do not rebuild or alter them to fit a photographic panel. See the
[locked component snapshot](BASELINE_V010.md#canonical-geometry-and-finishing).

## Reference ambiguity and configurable assumptions

These are visual concept sheets, not measured CAD, calibrated lighting or full PBR
capture. They do not establish exact dimensions, leather relief depth, IOR,
roughness, exposure, camera focal length or manufacturing tolerances.

The side diagonals imply a shallow-front/high-rear base. Some rear panels repeat a
low front-style seam, which cannot coexist with the continuous approved side seam
without additional construction. The existing model uses a high horizontal rear
edge and a wedge-shaped base; preserve that approved decision. A uniformly shallow
base is not the current canonical geometry.

The bottom panels suggest folded wrap construction. Detailed fold geometry is not
implemented in the canonical solid bottom. Do not invent or silently add folds.
Microscopic texture dimensions, deboss depth and stitch dimensions in v010 are
appearance assumptions, not measurements recovered from reference pixels.
Nearest-neighbor enlargement grids are not leather-grain measurements.

## What may vary by tier

With an authorized new-tier task, vary material source/morphology, pigmentation,
roughness, reflectance, fiber/weave direction, reveal finish and approved branding
treatment. Keep the same canonical mesh, dimensions, topology, bevels, separation,
component names, origins, parenting and opening controls. Isolate any finishing
treatment in its new version; never silently replace v010 or edit its meshes.

The existing [material catalogue](../../config/materials.json) holds placeholders.
It does not certify photorealistic completion of the other four tiers.

## Manual visual acceptance

| Check | Designer review question |
| --- | --- |
| Geometry | Do all views preserve the approved proportions, seam, clearances and opening construction? |
| Material morphology | Does leather show rounded organic grain, cloth a coherent weave, suede fine directional nap and paper appropriate fibers? |
| Physical scale | Is texture density plausible on the 140mm box and consistent across front, sides, top and edges? |
| Surface depth | Do normal/roughness responses feel tactile without artificial cracking, noise, wear or plastic glare? |
| Lighting | Are highlights and shadow transitions photographic while preserving deep material color and pure black background? |
| Camera | Are view angle, visible face proportions, framing and negative space comparable to the reference? |
| Manufacturing | Are corners, wrap transitions, stitching and edge compression credible without changing the silhouette? |
| Typography | Is the serif wordmark correctly placed/scaled and naturally pressed into the surface, with restrained contrast? |
| Reveal | Does the chosen finish read as the intended paper/satin/metal rather than a black gap or bright chrome? |
| Image quality | Are source detail, filtering, denoising, shadows and high-bit outputs adequate without retouching or artificial sharpening? |

The [v010 manual rubric](../../outputs/packaging/private-edition-v010/manual_review.json)
assigns 35/25/15/15/10 points to leather, lighting, camera, manufacturing and branding.
It is a designer-review framework. No automated score or 90–95% approval is recorded.
v010 is the selected best baseline; the [known limitations](BASELINE_V010.md#limitations-and-unverified-items)
remain part of the handoff.
