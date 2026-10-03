"""Independent forward replay checker. It does not call the optimizer."""
from .model import LineageError, Manifest


def check_plan(manifest: Manifest, available, requested, execution_order) -> dict:
    """Check prerequisites, one execution per action, goal coverage and exact cost.

    available must come from assess() of a stable snapshot. Supplying arbitrary
    availability to this checker is not a file verification or trust decision.
    """
    ready = set(available)
    targets = set(requested)
    unknown = (ready | targets) - manifest.artifacts.keys()
    if unknown:
        raise LineageError(f"checker: unknown artifact IDs {sorted(unknown)}")
    seen, cost, trace = set(), 0, []
    for aid in execution_order:
        if aid not in manifest.actions:
            raise LineageError(f"checker: unknown action {aid}")
        if aid in seen:
            raise LineageError(f"checker: repeated action {aid}")
        action = manifest.actions[aid]
        missing = set(action.inputs) - ready
        if missing:
            raise LineageError(f"checker: action {aid} has unavailable prerequisites {sorted(missing)}")
        seen.add(aid)
        ready.update(action.outputs)
        cost += action.cost
        trace.append({"action": aid, "consumed": list(action.inputs), "produced": list(action.outputs)})
    missing = targets - ready
    return {"feasible": not missing, "cost": cost, "missing": sorted(missing), "available_after": sorted(ready), "trace": trace}
