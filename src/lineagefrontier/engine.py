"""Historical invalidation and bounded exact atomic-action scheduling."""
from __future__ import annotations

from pathlib import Path
import hashlib
import json
from .model import Manifest, LineageError, hash_file
from .checker import check_plan

MAX_CAUSES = 128


def _snapshot_digest(report):
    try:
        data = {k: v for k, v in report.items() if k != "snapshot_digest"}
        encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except (TypeError, ValueError, RecursionError) as exc:
        raise LineageError("snapshot integrity: expected finite JSON assessment from assess()") from exc
    return hashlib.sha256(encoded).hexdigest()


def assess(manifest: Manifest, root: str | Path, revoked: dict[str, str] | None = None) -> dict:
    """Compare a caller-supplied stable local snapshot with recorded provenance.

    Stale historical input slots may supply current bytes to a future rebuild.
    Revoked/missing inputs cannot. Derived bytes need both digest match and a
    non-stale historical dependency closure before they are reused.
    """
    revoked = revoked or {}
    if not isinstance(revoked, dict) or any(a not in manifest.artifacts or not isinstance(r, str) or not r or len(r) > 2048 for a, r in revoked.items()):
        raise LineageError("revocations require known artifact IDs and nonempty reason strings <=2048 characters")
    root = Path(root)
    if not root.is_dir():
        raise LineageError("root must be an existing directory")
    records, causes = {}, {}
    for aid, artifact in manifest.artifacts.items():
        try:
            current = hash_file(root, artifact.path)
            verification = "MATCH" if current == artifact.digest else "CHANGED"
        except FileNotFoundError:
            current, verification = None, "MISSING"
        except OSError as exc:
            raise LineageError(f"cannot verify artifact {aid}: {exc}") from exc
        seeds = []
        if verification != "MATCH":
            reason = "missing_file" if verification == "MISSING" else "changed_bytes"
            seeds.append((f"{aid}:{reason}", {"artifact": aid, "reason": reason}))
        if aid in revoked:
            seeds.append((f"{aid}:revoked", {"artifact": aid, "reason": "revoked", "detail": revoked[aid]}))
        records[aid] = {"kind": artifact.kind, "recorded_digest": artifact.digest, "current_digest": current, "verification": verification}
        causes[aid] = {}
        for cid, cause in seeds:
            causes[aid][cid] = (cause, (aid,))
    if sum(map(len, causes.values())) > MAX_CAUSES:
        raise LineageError(f"more than {MAX_CAUSES} direct causes; split the inventory into bounded snapshots")
    for aid in manifest.topological:
        for dep in manifest.dependencies[aid]:
            for cid, (cause, path) in causes[dep].items():
                witness = (*path, aid)
                existing = causes[aid].get(cid)
                if existing is None or (len(witness), witness) < (len(existing[1]), existing[1]):
                    causes[aid][cid] = (cause, witness)
    available, stale, valid = [], [], []
    for aid in manifest.artifacts:
        record = records[aid]
        record["status"] = "STALE" if causes[aid] else "VALID"
        record["evidence"] = [{"cause": cause, "path": list(path)} for _, (cause, path) in sorted(causes[aid].items())]
        # Current source bytes are usable even when their old version changed.
        can_use = (record["verification"] != "MISSING" and aid not in revoked) if record["kind"] == "input" else not causes[aid]
        record["available_for_rebuild"] = can_use
        if can_use:
            available.append(aid)
        (stale if causes[aid] else valid).append(aid)
        if aid in manifest.builders:
            record["claimed_builder"] = manifest.builders[aid]
    report = {"schema_version": 1, "trust": "UNAUTHENTICATED_RECORDED_PROVENANCE", "provenance_fingerprint": manifest.provenance_fingerprint(), "artifacts": records, "stale": stale, "valid": valid, "available": available}
    report["snapshot_digest"] = _snapshot_digest(report)
    return report


class _ScheduleIndex:
    """One plan's bounded historical closures and action masks; never persisted.

    All mappings belong to this manifest/assessment invocation. Integer masks
    encode logical slots, not digests or independently authenticated generations.
    """

    def __init__(self, manifest, initial):
        self.work = dict(artifact_bit_assignments=0, index_graph_nodes=0, index_graph_edges=0,
                         action_input_slots=0, action_output_slots=0, descendant_queries=0,
                         schedule_calls=0, selected_action_checks=0, readiness_checks=0)
        self.bits = {}
        for i, key in enumerate(manifest.artifacts):
            self.work["artifact_bit_assignments"] += 1
            self.bits[key] = 1 << i
        children = {key: [] for key in manifest.artifacts}
        for key, dependencies in manifest.dependencies.items():
            self.work["index_graph_nodes"] += 1
            for parent in dependencies:
                self.work["index_graph_edges"] += 1
                children[parent].append(key)
        self.descendants = {}
        for key in reversed(manifest.topological):
            self.work["index_graph_nodes"] += 1
            mask = self.bits[key]
            for child in children[key]:
                self.work["index_graph_edges"] += 1
                mask |= self.descendants[child]
            self.descendants[key] = mask
        self.inputs, self.outputs, self.invalidates = {}, {}, {}
        for key, action in manifest.actions.items():
            self.work["action_input_slots"] += len(action.inputs)
            self.work["action_output_slots"] += len(action.outputs)
            self.inputs[key] = self.mask(action.inputs)
            self.outputs[key] = self.mask(action.outputs)
            self.invalidates[key] = self.descendant_mask(action.outputs)
        self.initial = self.mask(initial)

    def mask(self, keys):
        result = 0
        for key in keys:
            result |= self.bits[key]
        return result

    def descendant_mask(self, keys):
        result = 0
        for key in keys:
            self.work["descendant_queries"] += 1
            result |= self.descendants[key]
        return result

    def invalidation(self, selected):
        result = 0
        for key in selected:
            result |= self.invalidates[key]
        return result

    def ids(self, mask):
        return {key for key, bit in self.bits.items() if mask & bit}


def _schedule(index, selected):
    index.work["schedule_calls"] += 1
    outputs = 0
    for aid in selected:
        index.work["selected_action_checks"] += 1
        if outputs & index.outputs[aid]:
            return None
        outputs |= index.outputs[aid]
    available = index.initial & ~index.invalidation(selected)
    remaining = set(selected)
    order = []
    while remaining:
        ready = []
        for aid in sorted(remaining):
            index.work["readiness_checks"] += 1
            if index.inputs[aid] & available == index.inputs[aid]:
                ready.append(aid)
        if not ready:
            return None
        aid = ready[0]
        available |= index.outputs[aid]
        remaining.remove(aid)
        order.append(aid)
    return order, available


def _descendants(manifest, seeds):
    """Include seeds: a new generation invalidates its historical descendants."""
    invalid = set(seeds)
    for aid in manifest.topological:
        if set(manifest.dependencies[aid]) & invalid:
            invalid.add(aid)
    return invalid


def _relevant(index, targets):
    needed, relevant = targets & ~index.initial, set()
    while True:
        addition = {a for a, outputs in index.outputs.items() if outputs & needed} - relevant
        if not addition:
            return sorted(relevant)
        relevant.update(addition)
        reusable = index.initial & ~index.invalidation(relevant)
        needed |= targets & ~reusable
        for aid in relevant:
            needed |= index.inputs[aid] & ~reusable


def plan(manifest: Manifest, assessment: dict, requested, *, exact_limit: int = 18) -> dict:
    """Minimum total cost conditional rebuild, accounting for atomic co-outputs.

    Enumerates all relevant action subsets at <=exact_limit, otherwise computes
    a replay-checked feasible upper bound and reports UNKNOWN optimality.
    This is a decision, not execution, output-byte prediction or authentication.
    """
    if not isinstance(requested, (list, tuple, set, frozenset)) or not requested or any(not isinstance(t, str) or t not in manifest.artifacts for t in requested):
        raise LineageError("requested must contain known artifact IDs")
    targets = sorted(set(requested))
    if not isinstance(assessment, dict) or assessment.get("provenance_fingerprint") != manifest.provenance_fingerprint():
        raise LineageError("snapshot does not match manifest inventory/recorded provenance; call assess() again")
    if assessment.get("snapshot_digest") != _snapshot_digest(assessment):
        raise LineageError("snapshot integrity mismatch; do not modify assess() reports")
    if type(exact_limit) is not int or not 0 <= exact_limit <= 18:
        raise LineageError("exact_limit must be an integer in 0..18")
    initial = set(assessment["available"])
    index = _ScheduleIndex(manifest, initial)
    target_mask = index.mask(targets)
    relevant = _relevant(index, target_mask)
    exact = len(relevant) <= exact_limit
    best, states = None, 0
    if exact:
        for mask in range(1 << len(relevant)):
            states += 1
            chosen = tuple(a for i, a in enumerate(relevant) if mask & (1 << i))
            key = (sum(manifest.actions[a].cost for a in chosen), len(chosen), chosen)
            if best is not None and key >= best[0]:
                continue
            result = _schedule(index, chosen)
            if result and target_mask & result[1] == target_mask:
                best = (key, result[0])
    else:
        # Conservative unique-producer greedy scheduling can miss feasible plans.
        # Reverse deletion shrinks a found plan; failure is UNKNOWN, not proof.
        available, remaining, order = index.initial & ~index.invalidation(relevant), set(relevant), []
        produced = 0
        while remaining:
            ready = sorted((a for a in remaining if index.inputs[a] & available == index.inputs[a]
                            and not index.outputs[a] & produced), key=lambda a: (manifest.actions[a].cost, a))
            if not ready:
                break
            aid = ready[0]
            remaining.remove(aid)
            order.append(aid)
            available |= index.outputs[aid]
            produced |= index.outputs[aid]
        if target_mask & available == target_mask:
            selected = set(order)
            for aid in sorted(selected, key=lambda a: (-manifest.actions[a].cost, a)):
                trial = _schedule(index, selected - {aid})
                if trial and target_mask & trial[1] == target_mask:
                    selected.remove(aid)
            chosen = tuple(sorted(selected))
            best = ((sum(manifest.actions[a].cost for a in chosen), len(chosen), chosen), _schedule(index, selected)[0])
    if best is None:
        return {"status": "INFEASIBLE" if exact else "UNKNOWN", "optimality": "EXACT" if exact else "UNKNOWN", "requested": targets, "affected_requested": sorted(set(targets) & set(assessment["stale"])), "execution_order": [], "cost": None, "relevant_actions": relevant, "states_examined": states, "reason": "No supported unique-producer plan found." if exact else "Bounded greedy search found no plan; this is not an infeasibility proof."}
    order = best[1]
    checked = check_plan(manifest, initial, targets, order)
    if not checked["feasible"] or checked["cost"] != best[0][0]:
        raise AssertionError("independent replay rejected optimizer result")
    produced = set().union(*(set(manifest.actions[a].outputs) for a in order)) if order else set()
    effective_mask = index.initial & ~index.invalidation(order)
    effective_initial = index.ids(effective_mask)
    frontier = [a for a in order if index.inputs[a] & effective_mask == index.inputs[a]]
    return {"status": "CONDITIONAL_FEASIBLE", "optimality": "EXACT" if exact else "UNKNOWN", "requested": targets, "affected_requested": sorted(set(targets) & set(assessment["stale"])), "cost": checked["cost"], "cost_lower_bound": checked["cost"] if exact else 0, "execution_order": order, "ready_frontier": frontier, "reused": sorted(effective_initial), "invalidated_by_plan": checked["invalidated_reuse"], "replaced_valid_outputs": sorted(produced & set(assessment["valid"])), "relevant_actions": relevant, "states_examined": states, "checker": checked, "actions": [{"id": a, "instruction": manifest.actions[a].instruction} for a in order], "condition": "Catalog actions succeed with declared complete inputs and outputs; capture fresh digests/provenance after actual execution."}
