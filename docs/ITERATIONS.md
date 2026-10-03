# Real review and correction history

Initial implementation and verification are recorded separately from the three required post-implementation review cycles. Each later entry records a reproduced deficiency, substantive correction, fail/pass command and before/after commit. This file is filled from actual runs; no independent score is claimed.

## Initial complete implementation (not a review round)

Windows / Python 3.14.3. Built a non-editable wheel with `py -3 -m pip wheel --no-deps --wheel-dir dist .`, created `.venv-check`, installed with `.venv-check/Scripts/python -m pip install --no-index --find-links dist lineagefrontier`. `python -m unittest discover -s tests -v`: 11 passed. Actual `examples/workflow.py`: cost 11, order clean/fit-batch/chart/bundle, notes branch preserved, post-execution recapture stale list empty. `benchmarks/compare.py`: changed-source 11 versus rebuild-all 13 / unbatched 13; revoked-source 15 versus fixed history infeasible; missing inputs infeasible; bounded search UNKNOWN with nonoptimal cost 13. Results are synthetic declared units, not wall-clock cost claims. No remote CI run yet.

## Review 1 — strict JSON/provenance parsing

Before: `1bca610f53a229a867598df374ca6ea038568c81`. Review found the standard JSON loader silently accepted duplicate fields (last value won) and NaN in ignored extensions, `True == 1` accepted an invalid version, and `value or empty` accepted false/empty wrong-typed optional provenance fields. This permitted ambiguous wire evidence, not merely cosmetic input variation.

Reproduction before correction: `.venv-check/Scripts/python -m unittest discover -s tests -p test_boundary_review.py -v` exited 1: 5 tests, 4 failures (`LineageError not raised`). Correction: duplicate-key hook, nonfinite rejection, exact integer version type, null-only optional coercion, bounded actual manifest read and actionable JSON nesting failure.

Verification: rebuilt wheel and force-reinstalled it; `.venv-check/Scripts/python -m unittest discover -s tests -v` exited 0, 16 passed; demo and benchmark exited 0 with unchanged intended 11-unit plan. Fix commit subject: `Reject ambiguous JSON and wrong-typed provenance values`; exact after SHA is in the final history table below. Remaining boundary: supported subset only; no signature or remote verification.

## Review 2 — co-output generation consistency

Before: `a73b4ff0af64437a6d322a910590fa196e5bd43b`. Review found that rebuilding a revoked model through an inexpensive batch also overwrote valid metrics, but the planner reused the historical chart built from those metrics. That mixed generations and falsely priced release repair at 2 units instead of 4.

Before correction: `.venv-check/Scripts/python -m unittest discover -s tests -p test_coproduction_review.py -v` exited 1, 3 tests / 2 failures: cost `2 != 4`, and the old checker accepted cross-generation reuse. Correction: selected producer outputs invalidate their historical descendants before scheduling/replay; candidate closure expands for initially valid prerequisites that a batch may displace; a separate version-aware sequence oracle models dynamic invalidation. Support is explicit: at most one producer per logical slot in one plan. Overlapping producer subsets are not eligible. Above the bound, failure now returns UNKNOWN instead of an unsound reachability proof.

After correction: rebuilt/reinstalled wheel; full unittest command exited 0, 19 passed; corrected fixture produces fit-batch/chart/bundle cost 4 and independently matches the sequence oracle; model-only alternative cost 5 retains the chart. Demo/benchmark exited 0. Fix commit subject: `Prevent cross-generation reuse after atomic co-output rebuild`; exact after SHA appears in final history table. Remaining boundary: no repeated producer schedules, concurrency or output-byte predictions; greedy failure is UNKNOWN.
