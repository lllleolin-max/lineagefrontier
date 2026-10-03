"""Synthetic actual graph-work and complete-plan cost; supports old/new wheels."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import tempfile
import time
import tracemalloc
from types import SimpleNamespace

from lineagefrontier import Manifest, assess, plan
import lineagefrontier.engine as engine


def fixture(root, size, shape):
    ids = [f"n{i:04d}" for i in range(size)]
    digests = {}
    for key in ids:
        payload = ("synthetic recorded bytes " + key).encode()
        (root / (key + ".bin")).write_bytes(payload)
        digests[key] = hashlib.sha256(payload).hexdigest()
    def descriptor(key):
        return dict(name=key, digest=dict(sha256=digests[key]))
    statements = []
    for i, key in enumerate(ids[1:], 1):
        parent = ids[i - 1] if shape == "chain" else ids[(i - 1) // 2]
        statements.append(dict(_type="https://in-toto.io/Statement/v1",
            predicateType="https://slsa.dev/provenance/v1", subject=[descriptor(key)],
            predicate=dict(buildDefinition=dict(buildType="synthetic", externalParameters={},
                resolvedDependencies=[descriptor(parent)]), runDetails=dict(builder=dict(id="unauthenticated-synthetic")))))
    targets = ids[-9:]
    actions = [dict(id=f"a{2*i+alternative:02d}", inputs=[ids[0]], outputs=[key], cost=1,
        instruction="Caller-owned synthetic transform; never executed by planner")
        for i, key in enumerate(targets) for alternative in range(2)]
    raw = dict(schema_version=1,
        artifacts=[dict(id=key, path=key + ".bin", digest=dict(sha256=digests[key]),
            kind="input" if i == 0 else "output") for i, key in enumerate(ids)],
        statements=statements, actions=actions)
    (root / (ids[0] + ".bin")).write_bytes(b"actual new source bytes")
    return raw, targets


def measured(operation, samples):
    times = []
    for _ in range(samples):
        start = time.perf_counter()
        operation()
        times.append((time.perf_counter() - start) * 1000)
    return dict(milliseconds=times, median_ms=statistics.median(times))


def counted_plan(manifest, assessment, targets):
    counts = dict(descendant_calls=0, descendant_nodes=0, descendant_edges=0,
                  schedule_calls=0, checker_nodes=0, checker_edges=0)
    def iterable(values, counter):
        for value in values:
            counts[counter] += 1
            yield value
    class Dependencies:
        def __init__(self, edge_counter):
            self.counter = edge_counter
        def __getitem__(self, key):
            return iterable(manifest.dependencies[key], self.counter)
    def proxy(kind):
        return SimpleNamespace(topological=iterable(manifest.topological, kind + "_nodes"),
            dependencies=Dependencies(kind + "_edges"), actions=manifest.actions, artifacts=manifest.artifacts)
    original_desc = engine._descendants
    original_schedule = engine._schedule
    original_check = engine.check_plan
    original_index = getattr(engine, "_ScheduleIndex", None)
    instances = []
    def descendants(_, seeds):
        counts["descendant_calls"] += 1
        return original_desc(proxy("descendant"), seeds)
    def schedule(*args):
        counts["schedule_calls"] += 1
        return original_schedule(*args)
    def check(_, available, requested, order):
        return original_check(proxy("checker"), available, requested, order)
    engine._descendants, engine._schedule, engine.check_plan = descendants, schedule, check
    if original_index:
        def index(*args):
            result = original_index(*args)
            instances.append(result)
            return result
        engine._ScheduleIndex = index
    try:
        decision = plan(manifest, assessment, targets)
    finally:
        engine._descendants, engine._schedule, engine.check_plan = original_desc, original_schedule, original_check
        if original_index:
            engine._ScheduleIndex = original_index
    if instances:
        counts["index_work"] = dict(instances[0].work)
    return decision, counts


def run(size, shape, samples, clean=False):
    with tempfile.TemporaryDirectory(prefix="lineagefrontier-synthetic-") as directory:
        root = Path(directory)
        raw, targets = fixture(root, size, shape)
        if clean:
            (root / "n0000.bin").write_bytes(b"synthetic recorded bytes n0000")
        manifest = Manifest.from_dict(raw)
        start = time.perf_counter()
        snapshot = assess(manifest, root)
        assessment_ms = (time.perf_counter() - start) * 1000
        before = json.dumps(raw, sort_keys=True), json.dumps(snapshot, sort_keys=True)
        decision, counts = counted_plan(manifest, snapshot, targets)
        assert decision["cost"] == (0 if clean else 9)
        assert len(decision["relevant_actions"]) == (0 if clean else 18)
        assert decision["states_examined"] == (1 if clean else 2 ** 18)
        assert len(decision["execution_order"]) == (0 if clean else 9)
        assert (json.dumps(raw, sort_keys=True), json.dumps(snapshot, sort_keys=True)) == before
        timing = measured(lambda: plan(manifest, snapshot, targets), samples)
        index_cost = None
        if hasattr(engine, "_ScheduleIndex"):
            index_cost = measured(lambda: engine._ScheduleIndex(manifest, snapshot["available"]), samples)
            tracemalloc.start()
            index = engine._ScheduleIndex(manifest, snapshot["available"])
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            index_cost["python_traced_peak_bytes"] = peak
            index_cost["descendant_mask_payload_bytes"] = sum((value.bit_length() + 7) // 8 for value in index.descendants.values())
        tracemalloc.start()
        start = time.perf_counter()
        dense = json.dumps(dict(assessment=snapshot, plan=decision), sort_keys=True).encode()
        dense_ms = (time.perf_counter() - start) * 1000
        _, output_peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return dict(artifacts=size, edges=size - 1, shape=shape, actions=18, clean=clean,
            raw_manifest_sha256=hashlib.sha256(before[0].encode()).hexdigest(),
            decision=decision, actual_work=counts, assessment_ms=assessment_ms, complete_plan=timing,
            index_construction=index_cost, dense_json=dict(bytes=len(dense), milliseconds=dense_ms,
                python_traced_peak_bytes=output_peak, sha256=hashlib.sha256(dense).hexdigest()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=int, default=1000)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--shapes", nargs="+", choices=["chain", "branch"], default=["chain", "branch"])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--clean", action="store_true", help="No byte change; requested artifacts already valid")
    args = parser.parse_args()
    if not 10 <= args.artifacts <= 1000 or not 1 <= args.samples <= 7:
        parser.error("artifacts must be 10..1000 and samples 1..7")
    result = dict(scope="Synthetic full plan including fingerprint/integrity/index/enumeration/checker/output construction",
        assessment_and_dense_serialization_reported_separately=True, new_bug_claim=False,
        cases=[run(args.artifacts, shape, args.samples, args.clean) for shape in args.shapes])
    with args.out.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
