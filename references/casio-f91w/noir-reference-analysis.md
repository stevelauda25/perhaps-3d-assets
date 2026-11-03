# Noir reference inspection and Casio refinement

Reference: /Users/admin/Documents/Blender File/Noir_Perfume/Noir_Perfume.blend. Read in an isolated Blender 5.2.3 process with --disable-autoexec; never saved. Its actual Hero camera was rendered to assets/casio-f91w/noir_reference_preview.png. Companion final renders inspected.

## Actual findings

- SI modeled bottle approximately70×32×126mm; carefully curved profiles and small manufacturing radii define the gradients.
- Five rectangular area sources: tall left key5W,115×230mm; fill.6W,120×180mm; right strip3W,25×210mm; shoulder.8W; rear ground pool.7W.
- Cycles256, AgX, exposure-.7, no contrast look. No attached compositor group/effects; no external image textures. Read-only node graph and source measurements recorded in noir_reference_inspection.json and noir_compositor_inspection.json.
- Clear/smoked glass: IOR1.52, roughness.075, absorption density75. Black anodized metal: metallic1, roughness.24, anisotropy.25. Molded polymer: metallic0, roughness.32. Procedural noise approximately90micron features, restrained bump and15% roughness variation.

## Transferred principles

Shaped tall-softbox reflection gradients, material-specific dielectric/metal response, manufactured curvature, physically separated layers and seams. The perfume's metal finish and smoked color are not copied to the Casio. Accepted upright closed-loop pose and portrait composition remain intact.

## Casio manufacturing fixes

Replaced raised tubular blue/white outlines with flat printing. Added opaque under-crystal aperture mask. Lowered module backing and recessed LCD polarizer/electrodes so the display is physically behind the printing, with clean separated flat segments and flat bell/signal indicators. Reconstructed squared rounded CASIO lettering as planar outlines from official imagery. Replaced broad straight bezel chamfer with a convex molded profile, improved edge normals and added the actual back/case gasket boundary. Resin retains metallic0, plausible IOR1.48, satin roughness and fine subtle mold grain.

Acrylic variation was reduced after preview revealed cloudy aliasing; a512sample production-resolution camera crop verified a clean face. Final rendering uses512samples, adaptive.004,16bitPNG and denoising. Existing rear engraving/subcomponent measurement limitations remain documented in sources.md.
