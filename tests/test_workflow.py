import copy
import hashlib
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from workflow import create, refresh_records
from lineagefrontier import Manifest, LineageError, assess, plan, check_plan, load_manifest
from lineagefrontier.cli import main


def exhaustive_order_oracle(manifest, initial, targets):
    """Independent version-aware sequence oracle, with dynamic invalidation."""
    best = None
    def visit(available, used, cost, produced, dependencies):
        nonlocal best
        if set(targets) <= available:
            key = (cost, len(used), tuple(sorted(used)))
            best = key if best is None or key < best else best
            return
        if best is not None and cost > best[0]:
            return
        for aid, action in manifest.actions.items():
            if aid not in used and not produced.intersection(action.outputs) and all(i in available for i in action.inputs):
                changed = set(action.outputs)
                while True:
                    old_len = len(changed)
                    changed.update(n for n, ds in dependencies.items() if any(d in changed for d in ds))
                    if len(changed) == old_len:
                        break
                next_deps = dict(dependencies)
                for output in action.outputs:
                    next_deps[output] = action.inputs
                visit((available - changed) | set(action.outputs), used | {aid}, cost + action.cost, produced | set(action.outputs), next_deps)
    visit(set(initial), set(), 0, set(), dict(manifest.dependencies))
    return best


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.raw = create(self.root)
        self.manifest = Manifest.from_dict(self.raw)

    def test_actual_input_change_impacts_transitive_outputs_and_preserves_branch(self):
        self.assertEqual(assess(self.manifest, self.root)["stale"], [])
        (self.root / "raw.bin").write_bytes(b"same filename, changed bytes")
        assessment = assess(self.manifest, self.root)
        self.assertEqual(assessment["stale"], ["chart", "cleaned", "metrics", "model", "raw", "release"])
        self.assertIn("notes-html", assessment["valid"])
        self.assertEqual(assessment["artifacts"]["release"]["evidence"][0]["path"], ["raw", "cleaned", "model", "release"])
        decision = plan(self.manifest, assessment, ["release"])
        self.assertEqual(decision["cost"], 11)
        self.assertEqual(decision["execution_order"], ["clean", "fit-batch", "chart", "bundle"])
        self.assertEqual(decision["ready_frontier"], ["clean"])
        self.assertIn("notes-html", decision["reused"])
        final = Manifest.from_dict(refresh_records(self.root, self.raw, decision["execution_order"]))
        self.assertEqual(assess(final, self.root)["stale"], [])

    def test_revoked_source_requires_declared_alternative_recipe(self):
        assessment = assess(self.manifest, self.root, {"raw": "source withdrawn"})
        self.assertNotIn("raw", assessment["available"])
        decision = plan(self.manifest, assessment, ["release"])
        self.assertEqual(decision["cost"], 15)
        self.assertEqual(decision["execution_order"][0], "recover-clean")
        self.raw["actions"] = [a for a in self.raw["actions"] if a["id"] != "recover-clean"]
        self.assertEqual(plan(Manifest.from_dict(self.raw), assessment, ["release"])["status"], "INFEASIBLE")

    def test_revoked_output_can_be_rebuilt_missing_source_cannot(self):
        decision = plan(self.manifest, assess(self.manifest, self.root, {"metrics": "bad prior measurement"}), ["release"])
        self.assertEqual(decision["execution_order"], ["fit-metrics", "chart", "bundle"])
        self.assertEqual(decision["cost"], 6)
        (self.root / "raw.bin").unlink()
        (self.root / "backup.bin").unlink()
        self.assertEqual(plan(self.manifest, assess(self.manifest, self.root), ["release"])["status"], "INFEASIBLE")

    def test_subject_names_and_file_rename_do_not_define_content_identity(self):
        (self.root / "model.bin").rename(self.root / "different-name.bin")
        next(a for a in self.raw["artifacts"] if a["id"] == "model")["path"] = "different-name.bin"
        self.assertEqual(assess(Manifest.from_dict(self.raw), self.root)["stale"], [])
        self.assertEqual(assess(self.manifest, self.root)["trust"], "UNAUTHENTICATED_RECORDED_PROVENANCE")

    def test_order_permutations_produce_identical_reports(self):
        (self.root / "raw.bin").write_bytes(b"changed")
        expected = assess(self.manifest, self.root)
        expected_plan = plan(self.manifest, expected, ["release", "chart"])
        rng = random.Random(42)
        for _ in range(20):
            raw = copy.deepcopy(self.raw)
            for key in ("artifacts", "statements", "actions"):
                rng.shuffle(raw[key])
            for statement in raw["statements"]:
                rng.shuffle(statement["predicate"]["buildDefinition"]["resolvedDependencies"])
            manifest = Manifest.from_dict(raw)
            assessment = assess(manifest, self.root)
            self.assertEqual(assessment, expected)
            self.assertEqual(plan(manifest, assessment, ["chart", "release"]), expected_plan)

    def test_duplicate_missing_and_cycle_provenance_rejected(self):
        for change, pattern in (("duplicate", "duplicate artifact"), ("missing", "missing dependency"), ("cycle", "cycle")):
            raw = copy.deepcopy(self.raw)
            if change == "duplicate":
                raw["artifacts"].append(raw["artifacts"][0])
            elif change == "missing":
                raw["statements"][0]["predicate"]["buildDefinition"]["resolvedDependencies"][0]["digest"]["sha256"] = "0" * 64
            else:
                clean = next(s for s in raw["statements"] if s["subject"][0]["name"].endswith("/cleaned"))
                release = next(a for a in raw["artifacts"] if a["id"] == "release")
                clean["predicate"]["buildDefinition"]["resolvedDependencies"] = [{"digest": release["digest"]}]
            with self.assertRaisesRegex(LineageError, pattern):
                Manifest.from_dict(raw)

    def test_resource_and_path_boundary_errors(self):
        for value in ("../escape", "C:/secret", "\\\\server\\share", "/tmp/secret", "a/../b"):
            raw = copy.deepcopy(self.raw)
            raw["artifacts"][0]["path"] = value
            with self.assertRaisesRegex(LineageError, "relative"):
                Manifest.from_dict(raw)
        for cost in (-1, float("nan"), 1.5, True):
            raw = copy.deepcopy(self.raw)
            raw["actions"][0]["cost"] = cost
            with self.assertRaisesRegex(LineageError, "integer"):
                Manifest.from_dict(raw)
        with self.assertRaisesRegex(LineageError, "exact_limit"):
            plan(self.manifest, assess(self.manifest, self.root), ["release"], exact_limit=19)

    def test_independent_checker_rejects_invalid_execution(self):
        (self.root / "raw.bin").write_bytes(b"changed")
        available = assess(self.manifest, self.root)["available"]
        with self.assertRaisesRegex(LineageError, "prerequisites"):
            check_plan(self.manifest, available, ["release"], ["bundle"])
        with self.assertRaisesRegex(LineageError, "repeated"):
            check_plan(self.manifest, available, ["cleaned"], ["clean", "clean"])
        self.assertFalse(check_plan(self.manifest, available, ["release"], ["clean"])["feasible"])

    def test_exact_plan_matches_independent_order_oracle(self):
        for revoked in ({"raw": "withdrawn"}, {"metrics": "withdrawn"}, {"chart": "withdrawn"}, {"model": "withdrawn", "metrics": "withdrawn"}):
            assessment = assess(self.manifest, self.root, revoked)
            for targets in (["release"], ["model", "metrics"], ["chart", "notes-html"]):
                decision = plan(self.manifest, assessment, targets)
                oracle = exhaustive_order_oracle(self.manifest, assessment["available"], targets)
                self.assertEqual((decision["cost"], len(decision["execution_order"]), tuple(sorted(decision["execution_order"]))), oracle)

    def test_bounded_search_reports_unknown_and_checker_verified_upper_bound(self):
        (self.root / "raw.bin").write_bytes(b"changed")
        assessment = assess(self.manifest, self.root)
        decision = plan(self.manifest, assessment, ["release"], exact_limit=0)
        self.assertEqual(decision["optimality"], "UNKNOWN")
        self.assertTrue(decision["checker"]["feasible"])
        self.assertEqual(decision["cost_lower_bound"], 0)

    def test_cli_load_and_exit_codes(self):
        import contextlib
        import io
        self.assertEqual(len(load_manifest(self.root / "manifest.json").artifacts), 10)
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(["plan", str(self.root / "manifest.json"), "--root", str(self.root), "--request", "release"]), 0)
        self.assertEqual(json.loads(output.getvalue())["plan"]["cost"], 0)
        with contextlib.redirect_stderr(io.StringIO()) as output:
            self.assertEqual(main(["plan", str(self.root / "manifest.json"), "--root", str(self.root), "--request", "unknown"]), 2)
        self.assertIn("known", output.getvalue())


if __name__ == "__main__":
    unittest.main()
