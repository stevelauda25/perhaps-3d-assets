"""Parameter-driven Private Edition look update on an existing finished scene.

Reuses the v010 implementations: production.materials rebuilds the two PE6 leather
node trees from params; reference_studio.refine moves/resizes the existing reflection
cards in place. Geometry, wraps, deboss and cameras are untouched (the job runner
verifies the canonical lock after this step). Note: rebuilding leather also replaces
any later hand edits to "PE6 | Pressed leather" (e.g. v011 deboss shading).
"""


def run(params):
    from pipeline import production, reference_studio
    summary = {}
    if "leather" in params:
        production.materials({"source_manifest": params["source_manifest"], "leather": params["leather"]})
        summary["leather_materials"] = list(production.MATERIAL_NAMES)
    if "studio_lights" in params:
        summary["cards"] = sorted(reference_studio.refine({"lights": params["studio_lights"]}))
    return summary
