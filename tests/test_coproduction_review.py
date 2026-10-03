"""Real review regression: a batch can invalidate an initially valid branch."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from workflow import create
from lineagefrontier import Manifest, LineageError, assess, plan, check_plan
from test_workflow import exhaustive_order_oracle


class CoProductionReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = create(self.root)
        next(a for a in self.raw["actions"] if a["id"] == "fit-batch")["cost"] = 1
        self.manifest = Manifest.from_dict(self.raw)
        self.assessment = assess(self.manifest, self.root, {"model": "old model rejected"})

    def test_batch_overwrite_requires_valid_metrics_downstream_refresh(self):
        self.assertIn("chart", self.assessment["available"])
        result = plan(self.manifest, self.assessment, ["release"])
        self.assertEqual(result["cost"], 4)
        self.assertEqual(result["execution_order"], ["fit-batch", "chart", "bundle"])
        self.assertNotIn("chart", result["reused"])
        self.assertEqual(result["invalidated_by_plan"], ["chart", "metrics"])
        self.assertEqual(result["cost"], exhaustive_order_oracle(self.manifest, self.assessment["available"], ["release"])[0])

    def test_checker_rejects_cross_generation_reuse_after_batch(self):
        with self.assertRaisesRegex(LineageError, "prerequisites"):
            check_plan(self.manifest, self.assessment["available"], ["release"], ["fit-batch", "bundle"])

    def test_alternative_without_batch_preserves_valid_chart(self):
        raw = copy.deepcopy(self.raw)
        next(a for a in raw["actions"] if a["id"] == "fit-batch")["cost"] = 9
        manifest = Manifest.from_dict(raw)
        result = plan(manifest, self.assessment, ["release"])
        self.assertEqual(result["cost"], 5)
        self.assertEqual(result["execution_order"], ["fit-model", "bundle"])
        self.assertIn("chart", result["reused"])


if __name__ == "__main__":
    unittest.main()
