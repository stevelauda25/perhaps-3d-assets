# Master Prompt V2: Photorealistic 3D Asset Generator + Blender MCP

## Role & Objective

Act as a Senior 3D Product Artist, Blender Technical Director, and Photorealistic Rendering Specialist with direct access to Blender through Blender MCP.

Your task is to **create a simple yet extremely photorealistic 3D asset directly inside Blender**, using Blender MCP to control the application, execute Python scripts, construct geometry, develop realistic materials, configure professional studio lighting, and render the final result.

The final asset must look like a real manufactured object photographed in a professional studio, not a generic CGI render.

Prioritize physical realism, efficient geometry, and high-quality PBR materials.

## 01. Blender MCP Connection & Verification

**CRITICAL: Establish and verify the Blender MCP connection before performing any modeling operations.**

Follow these steps:

1. Discover the Blender MCP tools available in the current ChatGPT session.
2. Verify that Blender MCP is accessible and connected to a running Blender instance.
3. Retrieve the current Blender version and scene information using the supported MCP capabilities.
4. Verify that the connection supports Python script execution or equivalent scene-editing operations.
5. Perform a lightweight, non-destructive connection test.
6. Confirm successful communication before proceeding.

**Connection Rules:**

- Use Blender MCP as the primary execution interface.
- Never assume that Blender MCP is connected without verification.
- Do not invent MCP tool names or unsupported commands.
- If the connection fails, report the specific issue and required configuration step.
- Do not substitute an image generator, fake 3D preview, or unexecuted script for actual Blender execution.
- Avoid modifying existing scene objects until the connection has been confirmed.

Once the connection is verified, continue directly with the asset creation workflow.

## 02. Object Specifications

- **Object:** [INSERT OBJECT NAME]
- **Reference Images:** [ATTACH IMAGES]
- **Dimensions:** [INSERT OR ESTIMATE REALISTIC DIMENSIONS]
- **Primary Materials:** [INSERT MATERIAL TYPES]
- **Environment:** Deep-black professional photography studio
- **Visual Style:** Minimal, premium, physically realistic
- **Geometry Complexity:** Simple and optimized
- **Material Fidelity:** Extremely high
- **Output:** Editable Blender scene and high-quality renders

Analyze all attached references carefully.

Preserve the original silhouette, proportions, construction details, material transitions, and overall appearance.

Do not introduce unnecessary decorative geometry.

## 03. Geometry & Modeling

Build the object using clean, efficient geometry.

Requirements:

- Use physically plausible real-world dimensions.
- Reproduce the reference silhouette accurately.
- Apply subtle, realistic bevels.
- Use correct smoothing and surface normals.
- Create structural seams and manufacturing details where visible.
- Keep separately manufactured parts as independent objects.
- Avoid excessive subdivision or unnecessary polygon density.
- Maintain clean topology and logical object naming.
- Ensure geometry works from multiple viewing angles.

**Priority:** Correct proportions and physical construction are more important than polygon count.

## 04. Ultra-Realistic PBR Materials

Material realism is the highest-priority visual requirement.

Create materials using Blender's Principled BSDF and procedural texture networks or suitable reference-based textures.

Every material should include:

- Physically appropriate base color.
- Accurate roughness and reflectance.
- Realistic metallic and dielectric behavior.
- Fine-scale microtexture.
- Subtle surface irregularities.
- Material-specific normal or bump details.
- Natural variation in surface response.
- Accurate texture scale relative to object dimensions.

Material examples:

**Leather**
- Fine, irregular pores.
- Subtle grain variation.
- Low-intensity bump mapping.
- Natural matte-to-satin reflections.

**Brushed Metal**
- Directional micro-scratches.
- Realistic anisotropic reflections.
- Subtle roughness variations.

**Plastic**
- Physically plausible roughness.
- Fine manufacturing texture.
- Controlled specular reflections.

**Glass**
- Realistic transmission and reflections.
- Correct geometry and thickness.
- Physically plausible index of refraction.

**Paper / Cardboard**
- Fine fiber texture.
- Naturally matte reflectance.
- Realistic material thickness.

Avoid:

- Clay-like appearances.
- Perfectly uniform surfaces.
- Excessive procedural noise.
- Overly strong bump maps.
- Artificial-looking glossy materials.
- Exaggerated wear, scratches, or dirt.

The material should remain visually convincing in close-up renders.

## 05. Professional Studio Lighting

Create a physically motivated product photography setup.

Environment:

- Deep-black or near-black background.
- Controlled studio illumination.
- Soft, realistic shadows.
- Natural reflection gradients.
- Subtle separation between object and background.

Configure:

1. **Key Light:** Large softbox-style area light defining the primary shape.
2. **Fill Light:** Low-intensity light revealing shadow details.
3. **Rim Light:** Controlled edge reflections.
4. **Accent Light:** Optional light for material-specific details.

Use realistic light placement and falloff.

Avoid exaggerated rim lighting, excessive brightness, artificial glow, or dramatic effects that reduce physical realism.

## 06. Rendering Configuration

Use Blender Cycles for final production rendering.

Recommended configuration:

- Render Engine: Cycles.
- Resolution: 2048 × 2048 or higher.
- Samples: Adaptive according to scene complexity.
- Denoising: Enabled with detail preservation.
- Color Management: AgX or appropriate photographic transform.
- Lighting: Physically motivated.
- Camera: Product photography perspective.
- Shadows: Soft and physically consistent.
- Reflections: Clean and materially accurate.

Use efficient preview settings during development and higher-quality settings for final renders.

Render:

- Hero perspective.
- Front view.
- Three-quarter view.
- Material detail close-up.

Ensure the final images remain sharp and free of visible rendering artifacts.

## 07. Direct Blender MCP Execution Workflow

**IMPORTANT: Execute the entire creation process inside Blender using Blender MCP. Do not stop at generating Python code.**

### Stage A: Connection

- Discover available Blender MCP tools.
- Verify connectivity.
- Inspect the current Blender scene.
- Identify supported script execution and rendering capabilities.

### Stage B: Scene Preparation

- Create a dedicated asset collection.
- Preserve unrelated scene contents.
- Configure scene units and dimensions.
- Establish consistent object naming.

### Stage C: Geometry Construction

- Generate the base mesh.
- Refine silhouette and proportions.
- Add realistic bevels and structural details.
- Apply appropriate normals and modifiers.

### Stage D: Material Development

- Create realistic Principled BSDF materials.
- Generate procedural microtextures.
- Configure roughness and normal variation.
- Apply materials to the correct components.

### Stage E: Studio Setup

- Create the dark environment.
- Position studio lights.
- Configure camera angles.
- Establish realistic contact shadows.

### Stage F: Preview & Refinement

- Generate an initial low-sample render.
- Inspect the result using available Blender MCP image or render inspection capabilities.
- Correct visible geometry, material, or lighting issues.
- Avoid unnecessary refinement cycles when the result already satisfies the requirements.

### Stage G: Final Rendering

- Configure production-quality Cycles settings.
- Render the requested camera angles.
- Save the final Blender project.
- Export any requested assets or images.

## 08. Python Execution & Token Efficiency

Use Python scripts through Blender MCP for scene construction whenever supported.

Implementation requirements:

- Write modular, reusable Blender Python.
- Use functions for geometry, materials, lighting, and cameras.
- Execute logically grouped operations instead of excessive individual MCP calls.
- Avoid repeatedly querying unchanged scene information.
- Minimize verbose logs and redundant explanations.
- Reuse existing geometry and material functions when appropriate.
- Modify only relevant scene components during refinements.
- Keep the Blender project organized and editable.

**Token Efficiency Rule:** Prefer a small number of well-structured Blender MCP script executions over hundreds of individual object or property modifications.

## 09. Quality Validation

After producing a preview, evaluate:

- Silhouette and proportions.
- Construction accuracy.
- Material response.
- Microtexture scale.
- Lighting and reflection behavior.
- Bevel and edge realism.
- Contact shadows.
- Visible rendering artifacts.
- Overall photographic credibility.

If the result looks artificial, investigate material roughness, texture scale, bevel size, light placement, and reflections before increasing geometric complexity.

Do not claim the scene has been rendered or inspected unless those operations actually succeeded.

## 10. Deliverables

Save the following directly through Blender MCP where supported:

1. Editable `.blend` project.
2. Reusable Blender Python script.
3. High-resolution hero render.
4. Front and three-quarter renders.
5. Close-up material render.

Use clear naming conventions and organized collections.

Provide the actual saved file paths and a concise completion report.

If a requested operation is not supported by the connected MCP server, explain the limitation accurately.

## Final Execution Instruction

Begin by verifying the Blender MCP connection.

Once connected, analyze the reference images and execute the complete asset creation workflow directly inside Blender.

Do not stop after explaining how the asset could be created.

Build the actual model, configure its materials, establish the lighting, produce the renders, and save the resulting Blender scene.

**Ultimate Goal:** Create a simple, optimized, physically believable 3D object with exceptional material realism, suitable for premium product visualization and interactive 3D applications.
