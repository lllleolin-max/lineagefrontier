"""Executed synthetic decision comparisons; no incumbent execution claim."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from workflow import create
from lineagefrontier import Manifest, assess, plan, check_plan


def scenario(name):
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        raw = create(root)
        manifest = Manifest.from_dict(raw)
        revoked = {}
        if name == "changed-bytes-same-filename":
            (root / "raw.bin").write_bytes(b"changed raw measurements")
        elif name == "revoked-source":
            revoked = {"raw": "input withdrawn by researcher"}
        elif name == "independent-branch":
            (root / "notes.bin").write_bytes(b"changed release notes")
        elif name == "missing-inputs":
            (root / "raw.bin").unlink()
            (root / "backup.bin").unlink()
        elif name == "shared-output-revocation":
            revoked = {"model": "old run rejected", "metrics": "old run rejected"}
        assessment = assess(manifest, root, revoked)
        targets = ["release"]
        decision = plan(manifest, assessment, targets)
        # Actual independent per-file SHA-256: checks only target bytes, no lineage.
        checksum_reuse = all((root / manifest.artifacts[t].path).is_file() and hashlib.sha256((root / manifest.artifacts[t].path).read_bytes()).hexdigest() == manifest.artifacts[t].digest for t in targets)
        # Disclosed fixed history rebuild-all executes each original action once,
        # including unrelated notes. Replay checks source availability.
        all_order = ["clean", "fit-batch", "chart", "bundle", "notes"]
        try:
            all_check = check_plan(manifest, assessment["available"], targets, all_order)
            all_cost = all_check["cost"]
            all_feasible = all_check["feasible"]
        except ValueError:
            all_cost, all_feasible = None, False
        # Remove atomic batching while retaining the same single-output recipes.
        unbatched = copy.deepcopy(raw)
        unbatched["actions"] = [a for a in unbatched["actions"] if a["id"] != "fit-batch"]
        no_batch = plan(Manifest.from_dict(unbatched), assessment, targets)
        no_alternatives = copy.deepcopy(raw)
        no_alternatives["actions"] = [a for a in no_alternatives["actions"] if a["id"] != "recover-clean"]
        no_alt = plan(Manifest.from_dict(no_alternatives), assessment, targets)
        bounded = plan(manifest, assessment, targets, exact_limit=0)
        return {"scenario": name, "checksum_reuses_release": checksum_reuse, "actual_release_stale": "release" in assessment["stale"], "lineage_cost": decision["cost"], "lineage_status": decision["status"], "lineage_order": decision["execution_order"], "unbatched_cost": no_batch["cost"], "no_alternative_status": no_alt["status"], "rebuild_all_cost": all_cost, "rebuild_all_feasible": all_feasible, "independent_notes_preserved": "notes-html" in decision.get("reused", []), "bounded_optimality": bounded["optimality"], "bounded_cost": bounded["cost"]}


if __name__ == "__main__":
    print(json.dumps({"fixture": "Synthetic 10-artifact research release; integer costs are declared units, not measured seconds or dollars", "results": [scenario(name) for name in ["changed-bytes-same-filename", "shared-output-revocation", "revoked-source", "independent-branch", "missing-inputs"]]}, indent=2, sort_keys=True))
