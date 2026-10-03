"""Independent randomized DAG oracle plus actual I/O/resource probes."""
import copy
import hashlib
from pathlib import Path
import random
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from workflow import create
from test_workflow import exhaustive_order_oracle
from lineagefrontier import Manifest, LineageError, assess, plan, load_manifest
from lineagefrontier.model import MAX_FILE_BYTES, MAX_MANIFEST_BYTES


class OracleResourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = create(self.root)

    def test_80_random_catalogs_against_independent_version_order_oracle(self):
        rng = random.Random(610)
        order = ["cleaned", "model", "metrics", "chart", "release", "notes-html"]
        for case in range(80):
            raw = copy.deepcopy(self.raw)
            actions = []
            for index in range(7):
                first = rng.randrange(len(order))
                outputs = rng.sample(order[first:], min(len(order) - first, rng.randint(1, 2)))
                min_pos = min(order.index(o) for o in outputs)
                eligible = ["raw", "backup", "code", "notes"] + order[:min_pos]
                inputs = rng.sample(eligible, rng.randint(0, min(2, len(eligible))))
                actions.append({"id": f"a{index}", "inputs": inputs, "outputs": outputs, "cost": rng.randrange(6), "instruction": "declared synthetic transform"})
            raw["actions"] = actions
            manifest = Manifest.from_dict(raw)
            revoked = {rng.choice(["model", "metrics", "raw", "notes"]): "synthetic rejection"}
            assessment = assess(manifest, self.root, revoked)
            targets = rng.sample(order, rng.randint(1, 3))
            oracle = exhaustive_order_oracle(manifest, assessment["available"], targets)
            result = plan(manifest, assessment, targets)
            with self.subTest(case=case):
                if oracle is None:
                    self.assertEqual(result["status"], "INFEASIBLE")
                else:
                    self.assertEqual((result["cost"], len(result["execution_order"]), tuple(sorted(result["execution_order"]))), oracle)
                    self.assertTrue(result["checker"]["feasible"])

    def test_actual_oversized_file_is_rejected_without_hashing_it(self):
        with (self.root / "raw.bin").open("wb") as stream:
            stream.seek(MAX_FILE_BYTES)
            stream.write(b"x")
        with self.assertRaisesRegex(LineageError, "exceeds"):
            assess(Manifest.from_dict(self.raw), self.root)

    def test_manifest_size_and_nesting_are_actionable(self):
        path = self.root / "oversized.json"
        path.write_bytes(b" " * (MAX_MANIFEST_BYTES + 1))
        with self.assertRaisesRegex(LineageError, "2 MiB"):
            load_manifest(path)
        path.write_text("[" * 2000 + "0" + "]" * 2000, encoding="utf-8")
        with self.assertRaises(LineageError):
            load_manifest(path)

    def test_assessment_is_read_only(self):
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.glob("*.bin")}
        manifest = Manifest.from_dict(self.raw)
        assessment = assess(manifest, self.root, {"raw": "explicit revocation"})
        plan(manifest, assessment, ["release"])
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.glob("*.bin")}
        self.assertEqual(before, after)

    def test_root_escaping_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            external = Path(outside) / "external.bin"
            external.write_bytes(b"outside")
            (self.root / "raw.bin").unlink()
            try:
                (self.root / "raw.bin").symlink_to(external)
            except OSError as exc:
                self.skipTest(f"host does not permit symlinks: {exc}")
            with self.assertRaisesRegex(LineageError, "escapes root"):
                assess(Manifest.from_dict(self.raw), self.root)


if __name__ == "__main__":
    unittest.main()
