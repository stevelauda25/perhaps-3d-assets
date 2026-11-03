import json
import unittest
from pathlib import Path

from pipeline import jobs

ROOT = Path(__file__).resolve().parents[1]


class WatchSpec(unittest.TestCase):
    def test_job_validates_and_spec_matches_omega(self):
        jobs.validate(json.loads((ROOT / "jobs/omega-speedmaster-black-v014.json").read_text()))
        spec = json.loads((ROOT / "config/watches/speedmaster-moonwatch-black-v11.json").read_text())
        self.assertEqual(spec["verified_mm"], {"diameter": 42.0, "thickness": 13.54, "lug_to_lug": 47.5, "lug_width": 20.0})
        self.assertEqual(spec["case"]["lug"]["tip_y"] * 2, spec["verified_mm"]["lug_to_lug"])


if __name__ == "__main__":
    unittest.main()
