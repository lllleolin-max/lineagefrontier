"""Post-review SDK artifact/snapshot association probes."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from workflow import create
from lineagefrontier import Manifest, LineageError, assess, plan


class SnapshotReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = create(self.root)
        self.manifest = Manifest.from_dict(self.raw)
        (self.root / "raw.bin").write_bytes(b"changed source")
        self.assessment = assess(self.manifest, self.root)

    def test_snapshot_from_another_inventory_revision_is_rejected(self):
        raw = copy.deepcopy(self.raw)
        next(a for a in raw["artifacts"] if a["id"] == "raw")["path"] = "backup.bin"
        other_manifest = Manifest.from_dict(raw)
        with self.assertRaisesRegex(LineageError, "snapshot.*manifest"):
            plan(other_manifest, self.assessment, ["release"])

    def test_accidentally_modified_snapshot_availability_is_rejected(self):
        self.assessment["available"].append("release")
        with self.assertRaisesRegex(LineageError, "snapshot.*integrity"):
            plan(self.manifest, self.assessment, ["release"])

    def test_snapshot_roundtrip_and_catalog_only_changes_remain_supported(self):
        import json
        raw = copy.deepcopy(self.raw)
        raw["actions"][0]["cost"] += 1
        self.assertEqual(plan(Manifest.from_dict(raw), json.loads(json.dumps(self.assessment)), ["release"])["cost"], 12)

    def test_invalid_sdk_request_returns_actionable_error(self):
        for request in (["release", None], [{"id": "release"}], "release"):
            with self.assertRaises(LineageError):
                plan(self.manifest, self.assessment, request)


if __name__ == "__main__":
    unittest.main()
