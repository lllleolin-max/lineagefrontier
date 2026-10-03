"""Raw-input forward exhaustive oracle; no optimizer/checker helpers in oracle."""
from copy import deepcopy
import hashlib
from itertools import combinations
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from lineagefrontier import Manifest, LineageError, assess, plan
import lineagefrontier.engine as engine


def raw_manifest(root, history, actions):
    ids = ["s", "backup", *history]
    digests = {}
    for key in ids:
        content = ("synthetic forward-check bytes " + key).encode()
        (root / (key + ".bin")).write_bytes(content)
        digests[key] = hashlib.sha256(content).hexdigest()
    def descriptor(key):
        return dict(name="opaque-" + key, digest=dict(sha256=digests[key]))
    return dict(schema_version=1,
        artifacts=[dict(id=key, path=key + ".bin", digest=dict(sha256=digests[key]),
            kind="output" if key in history else "input") for key in ids],
        statements=[dict(_type="https://in-toto.io/Statement/v1",
            predicateType="https://slsa.dev/provenance/v1", subject=[descriptor(key)],
            predicate=dict(buildDefinition=dict(buildType="synthetic", externalParameters={},
                resolvedDependencies=[descriptor(parent) for parent in parents]),
                runDetails=dict(builder=dict(id="unauthenticated-synthetic"))))
            for key, parents in history.items()], actions=actions)


def reached(history, seeds):
    todo, found = list(seeds), set(seeds)
    while todo:
        parent = todo.pop()
        for child, inputs in history.items():
            if parent in inputs and child not in found:
                found.add(child)
                todo.append(child)
    return found


def exhaustive_forward(history, actions, initial, targets):
    """Reserve chosen new generations then independently replay every order.

    This works on raw catalog/history dictionaries, uses breadth-first invalidation
    and explores all eligible next actions, unlike the production subset scheduler.
    """
    best = None
    for size in range(len(actions) + 1):
        for chosen in combinations(actions, size):
            outputs = [key for action in chosen for key in action["outputs"]]
            if len(outputs) != len(set(outputs)):
                continue
            key = (sum(action["cost"] for action in chosen), size, tuple(sorted(action["id"] for action in chosen)))
            if best is not None and key > best[0]:
                continue
            ready = set(initial) - reached(history, outputs)
            frontier = sorted(action["id"] for action in chosen if set(action["inputs"]) <= ready)
            def visit(available, remaining, order):
                nonlocal best
                if not remaining:
                    if set(targets) <= available:
                        candidate = (key, tuple(order), frontier, sorted(ready))
                        if best is None or candidate[:2] < best[:2]:
                            best = candidate
                    return
                for action in remaining:
                    if set(action["inputs"]) <= available:
                        visit(available | set(action["outputs"]),
                              [other for other in remaining if other is not action], [*order, action["id"]])
            visit(ready, list(chosen), [])
    return best


class MaskPlanningTests(unittest.TestCase):
    def test_120_new_catalogs_full_forward_order_and_frontier(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for case in range(120):
                rng = random.Random(620261003 + case)
                outputs = ["o" + str(i) for i in range(5)]
                history = {key: rng.sample(["s", "backup", *outputs[:i]], rng.randrange(min(3, i + 2) + 1))
                           for i, key in enumerate(outputs)}
                actions = []
                for i in range(6):
                    produced = rng.sample(outputs, rng.randrange(1, 3))
                    inputs = rng.sample(["s", "backup", *[key for key in outputs if key not in produced]], rng.randrange(3))
                    actions.append(dict(id="a" + str(i), inputs=inputs, outputs=produced,
                        cost=rng.randrange(5), instruction="Never execute this synthetic instruction"))
                raw = raw_manifest(root, history, actions)
                revoked = set(rng.sample(["s", "backup", *outputs], rng.randrange(4)))
                changed = set(rng.sample(["s", "backup"], rng.randrange(3)))
                for key in changed:
                    (root / (key + ".bin")).write_bytes(("changed source " + key).encode())
                stale = reached(history, changed | revoked)
                initial = {key for key in ["s", "backup", *outputs]
                           if (key not in revoked if key in {"s", "backup"} else key not in stale)}
                targets = rng.sample(outputs, rng.randrange(1, 4))
                expected = exhaustive_forward(history, actions, initial, targets)
                manifest = Manifest.from_dict(raw)
                assessment = assess(manifest, root, {key: "synthetic withdrawal" for key in revoked})
                originals = deepcopy(raw), deepcopy(assessment), list(targets)
                bytes_before = {key: (root / (key + ".bin")).read_bytes() for key in initial | stale}
                decision = plan(manifest, assessment, targets)
                with self.subTest(case=case):
                    self.assertEqual(set(assessment["stale"]), stale)
                    self.assertEqual(set(assessment["available"]), initial)
                    if expected is None:
                        self.assertEqual(decision["status"], "INFEASIBLE")
                    else:
                        self.assertEqual(decision["optimality"], "EXACT")
                        self.assertEqual((decision["cost"], len(decision["execution_order"]),
                            tuple(sorted(decision["execution_order"]))), expected[0])
                        self.assertEqual(tuple(decision["execution_order"]), expected[1])
                        self.assertEqual(decision["ready_frontier"], expected[2])
                        self.assertEqual(decision["reused"], expected[3])
                    self.assertEqual((raw, assessment, targets), originals)
                    self.assertEqual(bytes_before, {key: (root / (key + ".bin")).read_bytes() for key in bytes_before})

    def test_no_repeated_historical_graph_walk_per_subset(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            history = {"x": ["s"], "y": ["s"], "z": ["y"], "goal": ["x", "z"]}
            actions = [dict(id=key, inputs=inputs, outputs=outputs, cost=cost, instruction="synthetic")
                       for key, inputs, outputs, cost in [("batch", ["s"], ["x", "y"], 1),
                           ("x-only", ["s"], ["x"], 5), ("z", ["y"], ["z"], 2),
                           ("bundle", ["x", "z"], ["goal"], 1)]]
            manifest = Manifest.from_dict(raw_manifest(root, history, actions))
            assessment = assess(manifest, root, {"x": "old run rejected"})
            original = engine._ScheduleIndex
            indexes = []
            def capture(*args):
                index = original(*args)
                indexes.append(index)
                return index
            with patch.object(engine, "_ScheduleIndex", side_effect=capture), \
                 patch.object(engine, "_descendants", side_effect=AssertionError("repeated full graph walk")):
                decision = plan(manifest, assessment, ["goal"])
            self.assertEqual(decision["execution_order"], ["batch", "z", "bundle"])
            self.assertEqual(decision["cost"], 4)
            self.assertEqual(indexes[0].work["index_graph_nodes"], 2 * len(manifest.artifacts))
            self.assertEqual(indexes[0].work["index_graph_edges"], 2 * sum(map(len, manifest.dependencies.values())))
            self.assertGreater(indexes[0].work["schedule_calls"], 1)
            edited = deepcopy(assessment)
            edited["available"].append("x")
            with self.assertRaisesRegex(LineageError, "integrity"):
                plan(manifest, edited, ["goal"])


if __name__ == "__main__":
    unittest.main()
