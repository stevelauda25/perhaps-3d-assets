import json
import unittest

from pipeline.config import ROOT


class TierTests(unittest.TestCase):
    def test_tiers_are_single_source(self):
        tiers = json.loads((ROOT / "config/tiers.json").read_text())
        self.assertEqual(list(tiers), ["spark", "wonder", "select", "prestige", "icon"])
        self.assertEqual(len({t["name"] for t in tiers.values()}), 5)
        self.assertEqual(set(json.loads((ROOT / "config/materials.json").read_text())) - {"technical"}, set(tiers))
        for tid, t in tiers.items():
            self.assertEqual(json.loads((ROOT / t["preset"]).read_text())["tier"], tid)
            if t["status"] == "approved":
                self.assertTrue((ROOT / t["scene"]).is_file() and t["version"] in t["scene"] + t["job"], tid)
                self.assertEqual(json.loads((ROOT / t["job"]).read_text())["tier"], tid)
