import copy
import json
import unittest

from pipeline.production import ROOT, validate_config


class ProductionSafetyTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "config/private_edition_production.json").read_text())

    def test_source_version_and_external_output_are_rejected(self):
        validate_config(self.config)
        for output in (str((ROOT / self.config["input"]).parent), "/tmp/production"):
            c = copy.deepcopy(self.config)
            c["output"] = output
            with self.assertRaises(ValueError):
                validate_config(c)
        self.config["final_scene"] = "../private_edition.blend"
        with self.assertRaises(ValueError):
            validate_config(self.config)

    def test_invalid_physical_scale_and_structural_depth_are_rejected(self):
        for section, key, value in (("leather", "tile_mm", 0),
                                    ("leather", "tile_mm", float("nan")),
                                    ("leather", "uv_base_tile_mm", 96),
                                    ("finishing", "deboss_depth_mm", 2)):
            c = copy.deepcopy(self.config)
            c[section][key] = value
            with self.assertRaises(ValueError):
                validate_config(c)
