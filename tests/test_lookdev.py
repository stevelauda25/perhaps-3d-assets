import copy
import json
import unittest
from pipeline.config import ROOT
from pipeline.lookdev import validate_settings
from pipeline.grain_compare import grain_multiplier, CANDIDATES


class LookdevTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT/"config/private_edition_reference.json").read_text())

    def test_calibrated_settings(self):
        validate_settings(self.config)

    def test_grain_multiplier_default_and_candidates(self):
        self.config["leather"].pop("leather_grain_scale_multiplier", None)
        validate_settings(self.config)
        self.assertEqual(grain_multiplier(self.config["leather"].get("leather_grain_scale_multiplier", 1.0)), 1.0)
        for _, value in CANDIDATES:
            self.config["leather"]["leather_grain_scale_multiplier"] = value
            validate_settings(self.config)
            self.assertAlmostEqual(32*grain_multiplier(value), {1.5:48, 2.25:72, 3.0:96}[value])

    def test_rejects_invalid_grain_multiplier(self):
        for value in (0, -1, True, "2", None, float("nan"), float("inf"), 1e-300, 1e300):
            self.config["leather"]["leather_grain_scale_multiplier"] = value
            with self.assertRaises(ValueError):
                validate_settings(self.config)

    def test_secondary_refinement_locks_variant_c(self):
        config = json.loads((ROOT/"config/private_edition_v009.json").read_text())
        validate_settings(config)
        for value in (1.0,2.25,4.0):
            config["leather"]["leather_grain_scale_multiplier"] = value
            with self.assertRaises(ValueError):
                validate_settings(config)

    def test_secondary_detail_rejects_excessive_or_invalid_relief(self):
        for key,value in (("pore_depth_um",25),("pore_strength",2),("pore_spacing_mm",0),
                          ("roughness_variation",float("nan")),("finish_spacing_mm",True)):
            config = json.loads((ROOT/"config/private_edition_v009.json").read_text())
            config["leather"]["surface_refinement"][key] = value
            with self.assertRaises(ValueError):
                validate_settings(config)

    def test_reference_reconstruction_resources(self):
        config = json.loads((ROOT/"config/private_edition_reference.json").read_text())
        validate_settings(config)
        # Leather037 maps were removed in the workspace cleanup (legacy v009 candidate); the config remains valid.
        self.assertEqual(config["reference_camera"]["lens_mm"], 150)

    def test_rejects_invalid_scale_and_relief(self):
        self.config["leather"]["source_maps"]["tile_width_mm"] = -1
        with self.assertRaises(ValueError):
            validate_settings(self.config)
        config = copy.deepcopy(json.loads((ROOT/"config/private_edition_reference.json").read_text()))
        config["leather"]["grain_height_um"] = 250
        with self.assertRaises(ValueError):
            validate_settings(config)

    def test_rejects_finishing_that_changes_silhouette(self):
        self.config["branding"]["deboss_depth_mm"] = 2
        with self.assertRaises(ValueError):
            validate_settings(self.config)

    def test_entry_never_builds_canonical_geometry(self):
        import ast
        tree = ast.parse((ROOT/"pipeline/lookdev_entry.py").read_text())
        calls = [ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)]
        self.assertNotIn("box.build", calls)
        self.assertNotIn("bpy.ops.wm.read_factory_settings", calls)
