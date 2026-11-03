# Reference plan: Speedmaster Moonwatch Professional 310.30.42.50.01.001 (1:1 target)

Written 2026-11-03 after the v009 comparison. Goal: the model matches the product 1:1; only scene and lighting differ. This file lists which views the geometry needs, what we already hold, what is missing, and candidate sources found. The white-background studio set is now in `studio_white/` (see sources.md for file list and sizes).

## Views needed to build the case, lugs, bracelet and clasp accurately

| # | View | Why it is needed | Status |
| --- | --- | --- | --- |
| 1 | Front, straight-on | dial/bezel/hands/lug planform, bracelet widths | HAVE: `hires/official_main_2000.png` (Omega), scale anchor = bezel 42 mm (±2 %, see `config/watches/speedmaster-trace.json`) |
| 2 | Caseback, straight-on | caseback ring, lug undersides, medallion, engraving | HAVE: `hires/gallery_1_caseback_1600x2000.png` (Omega) |
| 3 | **Side profile, crown side, straight-on** | case height profile, lug slope/twist, crown guards, crown and pusher size/height, crystal height, bezel thickness | **MISSING** (best public find: Wikimedia side view, older cal. 1861 model of the same case family) |
| 4 | **Side profile, opposite side** | confirms symmetry of lugs/flank | MISSING |
| 5 | **Top-down along the 12-6 axis (lug end view)** | lug twist/curvature, case flank shape, bracelet end-link fit | MISSING |
| 6 | 3/4 views | cross-check of all of the above | HAVE: user's `watch.avif` (Omega 3/4 render, 1505×1793) + Omega gallery_2/3/6 |
| 7 | Crown/pusher macro | flutes, caps, Ω on crown, guard shape | HAVE: `gallery_3`, `gallery_6` (Omega, 1200 px; native 3000 px available) |
| 8 | Dial macro | print, step ring, subdial recess, index frames, crystal edge | HAVE: `hires/gallery_5_dial_macro.jpg` (3000×3750) |
| 9 | Bracelet laid flat (full length, taper), link close-ups, end links | row structure, widths, scalloped link outlines, taper | PARTIAL: Omega gallery_7/8 (clasp), W&W flat-lay (candidate) |
| 10 | Clasp open + closed + side | fold-over clasp with comfort slider | HAVE: `hires/gallery_7`, `gallery_8` (3000×3750) |
| 11 | Bracelet side thickness (link profile) | link height, arch, ends | PARTIAL: W&W side/hanging bracelet (candidate) |

Verified numbers (Omega): 42 mm case, 13.54 mm thick, 47.5 mm lug-to-lug, 20 mm lug width, Hesalite, 5 bar.

## Primary reference (supplied by the user)
`omega_catalog_front_white.webp` (1024², Omega catalogue render on pure white, straight bracelet): the style of reference wanted: clean product cut-outs on white, no props. Also `watch.avif` (3/4 Omega render on white, 1505x1793). Target pose of the final render: bracelet closed into a loop (circular), as retailer studio shots show it.

## Candidates found: clean white-background studio sets (DOWNLOADED to `studio_white/` on 2026-11-03 with approval)

| Source | Files | What they show | Notes |
| --- | --- | --- | --- |
| Jomashop, ref 310.30.42.50.01.001 (stock studio set, 800x800 served; larger sizes may exist) | `..._31030425001001_2_1.jpg`, `_3.jpg`, `_4.jpg`, `_5.jpg`, `_6.jpg` (under `cdn2.jomashop.com/media/catalog/product/...`) | `_2_1`: side/3/4 with crown + pushers + the bracelet curving round; `_3`: back, bracelet closed in a loop, clasp, caseback; `_4`: 3/4 front; `_5`: back, closed loop with sticker; `_6`: back, clasp open | white background; exactly the bracelet-in-a-loop pose; resolution low |
| Bob's Watches, pre-owned 310.30.42.50.01.001, SKU 192092 (served up to 1000 px) | `.../omega/images/zUsed-OMEGA-Speedmaster-Moonwatch-310.30.42.50.01.001-SKU192092.jpg` (1000x1529 front on white), `-SKU192092-Black-Dial.jpg` (3/4 side with loop + clasp), `-SKU192092-Steel.jpg` (back 3/4, loop + clasp) | front straight-on, 3/4 side with the closed loop, back 3/4 | white background; a real watch (slight wear); `...SKU192092w.jpg` is a wrist shot (not wanted) |
| Bucherer US (Omega retailer) | `asset.bucherer.com/image/upload/c_limit,f_auto,w_1024/Assets/Watches/SWATCH/Omega/Manual/1337-038-0_FP.png` | front catalogue picture, white | only the front picture exists (other suffixes return 404) |
| Omega official (already held) | `hires/*` | front, back, dial/crown/clasp macros, transparent background | the 3/4 official render in `watch.avif` |

Rejected: lifestyle/wrist photos and dark-background galleries (European Watch Company is on black; Worn & Wound, WatchGecko, Wikimedia side view are on tables or in hands). They stay listed only as cross-checks in earlier notes.

## Method once the references are in
Register every view to one coordinate system (front/back 2000 px Omega renders, lug width 20 mm and bezel 42 mm as scale anchors), then fit the model by **silhouette overlay**: render our model with a camera matching each reference photo, overlay the outline on the photo, and adjust the profile until the outlines agree in all views. Boards of the overlays are for your review.

## What the public web does not provide
No orthographic side view of the 3861, no pure top-down lug-end view, no measured case-flank drawing. Without those, a 1:1 match of the lug twist, flank curvature and crown guards is not achievable by inference alone.

## Ways to close the gap (decision needed)
1. **Your own photographs of the actual watch** (or a colleague's): pure side profile (crown side and opposite side), top-down along the 12-6 axis, caseback, laid flat with the bracelet, each against a plain background with a ruler or a known object for scale, long lens, watch square to the camera.
2. **Licensed 3D model as geometry ground truth** (modeller's CAD-grade work): geometry reference or base; our materials/scene/lighting stack stays.
3. Public-web references only: build to the best available views, flagging every inferred surface; accuracy limited as noted.

## Status after download
Bob's Watches provided 2160 px originals (front, 3/4 side with loop + clasp, back with loop + clasp): the sharpest non-Omega references. Jomashop is capped at 800 px but adds a back view with the clasp open. Still no pure orthographic side/top-down; the registration-and-silhouette-fit method (above) is the way to get as close as possible from these; photos of the real watch from you would remove the remaining guesses.
