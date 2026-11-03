import copy
import json
import unittest

from pipeline.jobs import ROOT, validate


class JobSpecTests(unittest.TestCase):
    def setUp(self):
        self.job = json.loads((ROOT / "jobs/spark-v002.json").read_text())

    def test_example_jobs_validate(self):
        for path in sorted((ROOT / "jobs").glob("*.json")):
            validate(json.loads(path.read_text()))

    def test_unsafe_specs_are_rejected(self):
        for mutate in (lambda j: j.update(output="outputs/packaging/private-edition-v010"),
                       lambda j: j.update(output="outputs/jobs/other-id"),
                       lambda j: j["stages"][2]["render"].update(profile="draft"),
                       lambda j: j["stages"][1]["render"].pop("border"),
                       lambda j: j["stages"][0].update(step="missing_step"),
                       lambda j: j["stages"].append(copy.deepcopy(j["stages"][0]))):
            job = copy.deepcopy(self.job)
            mutate(job)
            with self.assertRaises(ValueError):
                validate(job)
