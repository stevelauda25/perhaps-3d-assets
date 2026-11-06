# Baseline: TUDOR Royal 36 M2836C1A0-0102 (saved 2026-11-07, not yet designer-reviewed)

First complete build, kept to compare later changes against the reference photo. Approval is the designer's; this file is not a similarity score.

| Item | Value |
| --- | --- |
| GLB | `models/watches/tudor-m2836c1a0-0102.glb`, 1,436,960 bytes, sha256 `bc6b6ef8f26e296a0ff8409b8e2192b4f1d483d2bbc495a4766dbd8abb79a9b9` (GLB 2.0, 2 embedded JPEG images, no external URIs) |
| Comparison render | `baseline_cmp-front_1800.png` (1800 px, white kit, same frame as the 2x reference), sha256 `4a10a6de59d9cd2a7d161a0ba1ff3d8c205c76afc29d7ff54dd2e96d8281caee` |
| Side by side | `baseline_vs_reference.png` (left: reference 2x crop on white, right: render) |
| Reference | `../tudor-m2836c1a0-0102_900x1200.png` (original), `../tudor-m2836c1a0-0102_1800x2400.png` (2x working copy) |
| Job / step / spec | `jobs/tudor-royal36-m2836c1a0-0102.json`, `pipeline/steps/watch_tudor_royal36.py` (unchanged, shared), `baseline_spec.json`, `baseline_job.json` |

Rebuild: `python3 -B -m pipeline.tudor_royal36_prep 0102 && python3 -B -m pipeline.jobs run jobs/tudor-royal36-m2836c1a0-0102.json --force`

Region means render : photo (white-composited, frame = 2x photo centred on the pivot): dial 0.997, bracelet top 1.005, bracelet bottom 0.991, bezel 1.045, case top 1.07. Mean absolute RGB difference inside the silhouette 10.5 / 255 (mostly edge softness of the resampled photo).

State: steel parts and hands carry the reference photo projected from the front; bracelet flat with rows and polished pieces at the measured positions; dial is the 2x photo map with 3D hands over the photographed ones; steel emission 0.4, dial emission 0.45, dial specular 0.

Known differences: drop shadow and background are not part of the asset; bezel and case top read 4 to 7 percent brighter than the photo; render is slightly softer than the photo (cubic sampling of a 2x upscale); the dark ring around the hub is the 3D hub shading; heights are estimated; the collection inside the build is still named for 0101 (shared step).
