"""Post-initial review regression probes. Uses installed package, not src path."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from workflow import create
from lineagefrontier import Manifest, LineageError, load_manifest


class ParsingReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = create(self.root)

    def test_duplicate_json_keys_are_not_silently_last_wins(self):
        path = self.root / "duplicate.json"
        path.write_text('{"schema_version":999,' + json.dumps(self.raw)[1:], encoding="utf-8")
        with self.assertRaisesRegex(LineageError, "duplicate JSON key"):
            load_manifest(path)

    def test_json_nonfinite_even_in_ignored_extension_is_rejected(self):
        path = self.root / "nonfinite.json"
        path.write_text('{"ignored_extension":NaN,' + json.dumps(self.raw)[1:], encoding="utf-8")
        with self.assertRaisesRegex(LineageError, "nonfinite"):
            load_manifest(path)

    def test_boolean_schema_version_is_not_integer_one(self):
        self.raw["schema_version"] = True
        with self.assertRaisesRegex(LineageError, "schema_version"):
            Manifest.from_dict(self.raw)

    def test_falsy_wrong_typed_provenance_fields_are_rejected(self):
        for field, value in (("externalParameters", False), ("externalParameters", []), ("resolvedDependencies", {}), ("resolvedDependencies", "")):
            raw = copy.deepcopy(self.raw)
            raw["statements"][0]["predicate"]["buildDefinition"][field] = value
            with self.assertRaisesRegex(LineageError, field):
                Manifest.from_dict(raw)

    def test_null_optional_fields_still_interoperate(self):
        for statement in self.raw["statements"]:
            statement["predicate"]["buildDefinition"]["externalParameters"] = None
        self.assertEqual(len(Manifest.from_dict(self.raw).artifacts), 10)


if __name__ == "__main__":
    unittest.main()
