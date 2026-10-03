"""Historical invalidation and bounded exact atomic-action scheduling."""
from __future__ import annotations

from pathlib import Path
from .model import Manifest, LineageError, hash_file
from .checker import check_plan

MAX_CAUSES = 128


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
    return {"schema_version": 1, "trust": "UNAUTHENTICATED_RECORDED_PROVENANCE", "artifacts": records, "stale": stale, "valid": valid, "available": available}


def _schedule(manifest, selected, initial):
    outputs = []
    for aid in selected:
        outputs.extend(manifest.actions[aid].outputs)
    if len(set(outputs)) != len(outputs):
        return None
    available = set(initial) - _descendants(manifest, outputs)
    remaining = set(selected)
    order = []
    while remaining:
        ready = sorted(a for a in remaining if set(manifest.actions[a].inputs) <= available)
        if not ready:
            return None
        aid = ready[0]
        available.update(manifest.actions[aid].outputs)
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


def _relevant(manifest, targets, initial):
    needed, relevant = set(targets) - set(initial), set()
    while True:
        addition = {a for a, action in manifest.actions.items() if set(action.outputs) & needed} - relevant
        if not addition:
            return sorted(relevant)
        relevant.update(addition)
        outputs = {o for a in relevant for o in manifest.actions[a].outputs}
        reusable = set(initial) - _descendants(manifest, outputs)
        needed.update(set(targets) - reusable)
        for aid in relevant:
            needed.update(set(manifest.actions[aid].inputs) - reusable)


def plan(manifest: Manifest, assessment: dict, requested, *, exact_limit: int = 18) -> dict:
    """Minimum total cost conditional rebuild, accounting for atomic co-outputs.

    Enumerates all relevant action subsets at <=exact_limit, otherwise computes
    a replay-checked feasible upper bound and reports UNKNOWN optimality.
    This is a decision, not execution, output-byte prediction or authentication.
    """
    targets = sorted(set(requested))
    if not targets or any(t not in manifest.artifacts for t in targets):
        raise LineageError("requested must contain known artifact IDs")
    if type(exact_limit) is not int or not 0 <= exact_limit <= 18:
        raise LineageError("exact_limit must be an integer in 0..18")
    initial = set(assessment["available"])
    relevant = _relevant(manifest, targets, initial)
    exact = len(relevant) <= exact_limit
    best, states = None, 0
    if exact:
        for mask in range(1 << len(relevant)):
            states += 1
            chosen = tuple(a for i, a in enumerate(relevant) if mask & (1 << i))
            key = (sum(manifest.actions[a].cost for a in chosen), len(chosen), chosen)
            if best is not None and key >= best[0]:
                continue
            result = _schedule(manifest, chosen, initial)
            if result and set(targets) <= result[1]:
                best = (key, result[0])
    else:
        # Conservative unique-producer greedy scheduling can miss feasible plans.
        # Reverse deletion shrinks a found plan; failure is UNKNOWN, not proof.
        outputs = {o for a in relevant for o in manifest.actions[a].outputs}
        available, remaining, order = set(initial) - _descendants(manifest, outputs), set(relevant), []
        produced = set()
        while remaining:
            ready = sorted((a for a in remaining if set(manifest.actions[a].inputs) <= available and not set(manifest.actions[a].outputs) & produced), key=lambda a: (manifest.actions[a].cost, a))
            if not ready:
                break
            aid = ready[0]
            remaining.remove(aid)
            order.append(aid)
            available.update(manifest.actions[aid].outputs)
            produced.update(manifest.actions[aid].outputs)
        if set(targets) <= available:
            selected = set(order)
            for aid in sorted(selected, key=lambda a: (-manifest.actions[a].cost, a)):
                trial = _schedule(manifest, selected - {aid}, initial)
                if trial and set(targets) <= trial[1]:
                    selected.remove(aid)
            chosen = tuple(sorted(selected))
            best = ((sum(manifest.actions[a].cost for a in chosen), len(chosen), chosen), _schedule(manifest, selected, initial)[0])
    if best is None:
        return {"status": "INFEASIBLE" if exact else "UNKNOWN", "optimality": "EXACT" if exact else "UNKNOWN", "requested": targets, "affected_requested": sorted(set(targets) & set(assessment["stale"])), "execution_order": [], "cost": None, "relevant_actions": relevant, "states_examined": states, "reason": "No supported unique-producer plan found." if exact else "Bounded greedy search found no plan; this is not an infeasibility proof."}
    order = best[1]
    checked = check_plan(manifest, initial, targets, order)
    if not checked["feasible"] or checked["cost"] != best[0][0]:
        raise AssertionError("independent replay rejected optimizer result")
    produced = set().union(*(set(manifest.actions[a].outputs) for a in order)) if order else set()
    effective_initial = initial - _descendants(manifest, produced)
    frontier = [a for a in order if set(manifest.actions[a].inputs) <= effective_initial]
    return {"status": "CONDITIONAL_FEASIBLE", "optimality": "EXACT" if exact else "UNKNOWN", "requested": targets, "affected_requested": sorted(set(targets) & set(assessment["stale"])), "cost": checked["cost"], "cost_lower_bound": checked["cost"] if exact else 0, "execution_order": order, "ready_frontier": frontier, "reused": sorted(effective_initial), "invalidated_by_plan": checked["invalidated_reuse"], "replaced_valid_outputs": sorted(produced & set(assessment["valid"])), "relevant_actions": relevant, "states_examined": states, "checker": checked, "actions": [{"id": a, "instruction": manifest.actions[a].instruction} for a in order], "condition": "Catalog actions succeed with declared complete inputs and outputs; capture fresh digests/provenance after actual execution."}
