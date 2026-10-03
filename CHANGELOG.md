# Change log

## 0.2.0

- Precompute per-plan historical descendant masks and action input/output/
  invalidation masks. Relevant closure, subset scheduling, bounded fallback and
  ready-frontier calculation reuse them without another full historical walk.
- Preserve atomic multi-output generation invalidation, unique producers,
  minimum declared cost/fewer-actions/lexical ties, the 18-action bound and
  independent checker. Reports and assessment association remain unchanged.
- Add 120 raw-input exhaustive forward catalogs checking complete execution
  orders/frontiers and nonmutation, plus a graph-visit regression.
- Add a synthetic installed-SDK benchmark reporting full plan costs, initial
  index allocation and dense output costs, including a slower already-valid case.

## 0.1.0

Historical strict ingress, generation consistency, assessment association and
retained workflow corrections remain in [docs/ITERATIONS.md](docs/ITERATIONS.md).
