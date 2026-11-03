import unittest

from pipeline.config import ROOT, check_references, load_config, output_directory, validate_config


class ConfigTests(unittest.TestCase):
    def test_reference_set_and_tiers(self):
        config = load_config()
        check_references(config)
        self.assertEqual(len(config["references"]), 7)
        self.assertEqual(set(config["materials"]), {"technical", "spark", "wonder", "select", "prestige", "icon"})

    def test_rejects_colliding_collar(self):
        config = load_config()
        config["geometry_mm"]["collar_engagement"] = 100
        with self.assertRaisesRegex(ValueError, "ceiling"):
            validate_config(config)

    def test_rejects_invalid_dimensions(self):
        for value in (0, -1, float("nan"), True):
            config = load_config()
            config["geometry_mm"]["width"] = value
            with self.assertRaises(ValueError):
                validate_config(config)

    def test_output_protects_history(self):
        for path in (ROOT / "assets/casio-f91w/new", ROOT / "references/new", ROOT / "outputs"):
            with self.assertRaises(ValueError):
                output_directory(path)
        candidate = ROOT / "outputs" / "test-run"
        self.assertEqual(output_directory(candidate), candidate)


if __name__ == "__main__":
    unittest.main()
