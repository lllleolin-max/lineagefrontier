"""Synthetic research release workflow. Runs real writes/checksums in a temp root.

This explicit demo executor runs only its own functions, never manifest commands.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from lineagefrontier import Manifest, assess, plan
from lineagefrontier.model import STATEMENT, PREDICATE


CATALOG = [
    ("clean", ["raw", "code"], ["cleaned"], 3),
    ("recover-clean", ["backup", "code"], ["cleaned"], 7),
    ("fit-batch", ["cleaned"], ["model", "metrics"], 5),
    ("fit-model", ["cleaned"], ["model"], 4),
    ("fit-metrics", ["cleaned"], ["metrics"], 3),
    ("chart", ["metrics"], ["chart"], 2),
    ("bundle", ["model", "chart"], ["release"], 1),
    ("notes", ["notes"], ["notes-html"], 2),
]
HISTORY = {"cleaned": ["raw", "code"], "model": ["cleaned"], "metrics": ["cleaned"], "chart": ["metrics"], "release": ["model", "chart"], "notes-html": ["notes"]}


def execute(root, action):
    """Demo-only deterministic transforms. Catalog recipes are policy declarations."""
    root = Path(root)
    _, inputs, outputs, _ = next(a for a in CATALOG if a[0] == action)
    content = b"|".join((root / f"{aid}.bin").read_bytes() for aid in inputs)
    for aid in outputs:
        (root / f"{aid}.bin").write_bytes(aid.encode() + b":" + content)


def statement(root, outputs, inputs):
    def descriptor(aid):
        return {"name": "unrelated-name/" + aid, "digest": {"sha256": hashlib.sha256((root / f"{aid}.bin").read_bytes()).hexdigest()}}
    return {"_type": STATEMENT, "subject": [descriptor(a) for a in outputs], "predicateType": PREDICATE, "predicate": {"buildDefinition": {"buildType": "https://example.invalid/research-transform/v1", "externalParameters": {"synthetic": True}, "resolvedDependencies": [descriptor(a) for a in inputs]}, "runDetails": {"builder": {"id": "https://example.invalid/unverified-demo-builder"}}}}


def create(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    for aid, content in {"raw": b"rows:v1", "code": b"transform:v1", "backup": b"curated:backup-v1", "notes": b"notes:v1"}.items():
        (root / f"{aid}.bin").write_bytes(content)
    for aid in ("clean", "fit-batch", "chart", "bundle", "notes"):
        execute(root, aid)
    raw = {"schema_version": 1, "artifacts": [], "statements": [], "actions": []}
    for aid in sorted({"raw", "code", "backup", "notes", *HISTORY}):
        raw["artifacts"].append({"id": aid, "digest": {"sha256": hashlib.sha256((root / f"{aid}.bin").read_bytes()).hexdigest()}, "path": f"{aid}.bin", "kind": "output" if aid in HISTORY else "input"})
    for aid, deps in HISTORY.items():
        raw["statements"].append(statement(root, [aid], deps))
    for aid, inputs, outputs, cost in CATALOG:
        raw["actions"].append({"id": aid, "inputs": inputs, "outputs": outputs, "cost": cost, "instruction": f"demo executor function: {aid}; adapt to your own reviewed build runner"})
    (root / "manifest.json").write_text(json.dumps(raw, indent=2), encoding="utf-8")
    return raw


def refresh_records(root, raw, order):
    """Actual demo execution followed by fresh SHA-256/provenance generation."""
    history = dict(HISTORY)
    for aid in order:
        execute(root, aid)
        _, inputs, outputs, _ = next(a for a in CATALOG if a[0] == aid)
        for output in outputs:
            history[output] = inputs
    for artifact in raw["artifacts"]:
        artifact["digest"]["sha256"] = hashlib.sha256((root / artifact["path"]).read_bytes()).hexdigest()
    raw["statements"] = [statement(root, [aid], deps) for aid, deps in history.items()]
    return raw


def run(root):
    raw = create(root)
    manifest = Manifest.from_dict(raw)
    initial = assess(manifest, root)
    (root / "raw.bin").write_bytes(b"rows:v2; new measurement")
    changed = assess(manifest, root)
    decision = plan(manifest, changed, ["release"])
    after = assess(Manifest.from_dict(refresh_records(root, raw, decision["execution_order"])), root)
    return {"initial_valid": initial["valid"], "changed_stale": changed["stale"], "release_evidence": changed["artifacts"]["release"]["evidence"], "decision": decision, "after_execution_and_recapture_stale": after["stale"], "notes_branch_preserved": "notes-html" in decision["reused"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--keep", type=Path, help="write synthetic local fixture here, overwriting its named fixture files")
    args = parser.parse_args()
    if args.keep:
        print(json.dumps(run(args.keep), indent=2, sort_keys=True))
    else:
        with tempfile.TemporaryDirectory() as temp:
            print(json.dumps(run(Path(temp)), indent=2, sort_keys=True))
