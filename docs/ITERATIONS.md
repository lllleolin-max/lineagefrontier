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

## Review 3 — bind decisions to the assessed inventory

Before: `f54f950a08b9f64a71622792d529f4cb8e8b791d`. Review found SDK decisions accepted an assessment from another inventory/path revision, and an accidental edit adding a stale release to availability silently produced a zero-cost reuse decision. Malformed mixed request types raised an unhelpful TypeError. These were concrete decision association failures.

Before correction: `.venv-check/Scripts/python -m unittest discover -s tests -p test_snapshot_review.py -v` exited 1: 4 tests, 2 failures and 1 error. Correction: canonical inventory/recorded-provenance fingerprint, report integrity digest, strict SDK requested-ID collection validation; recipe-only changes deliberately remain compatible with the same assessment.

Verification: rebuilt/reinstalled non-editable wheel; full tests exited 0, 23 passed. Demo and benchmark exited 0. JSON roundtrip/catalog-only adjustment passes; wrong inventory and modified availability now reject. Fix commit subject: `Bind rebuild decisions to intact provenance snapshots`; exact after SHA appears in final history table. Remaining boundary: unkeyed integrity is not signer authentication; a valid old assessment does not observe later filesystem changes.

## Exact review history

| Round | Before SHA | After correction SHA |
|---|---|---|
| 1 | 1bca610f53a229a867598df374ca6ea038568c81 | a73b4ff0af64437a6d322a910590fa196e5bd43b |
| 2 | a73b4ff0af64437a6d322a910590fa196e5bd43b | f54f950a08b9f64a71622792d529f4cb8e8b791d |
| 3 | f54f950a08b9f64a71622792d529f4cb8e8b791d | c90c4f61cd1ce33baf1697619e55a681b4a42d0c |

## Additional verification (not counted as a fourth correction cycle)

80 deterministic randomized acyclic recipe catalogs, including zero costs, atomic outputs, alternatives, unavailable inputs and infeasibility, match the independent version-aware action-order oracle. Real sparse 64 MiB+1 artifact and 2 MiB+1 manifest are rejected. Assessment/planning preserve every input/output byte. Expanded benchmark actually executes/recaptures each feasible fixed-demo plan and reports explicit synthetic owner approval when replacing withdrawn output records. A generation ablation computes cost 2 by executing monotone availability, while independent checker rejects it and the correct selected plan costs 4.

Final local suite: 28 tests run, 27 passed, 1 skipped. The root-escaping symlink probe was skipped on Windows because WinError 1314 denies symlink creation; the Ubuntu CI job includes that probe but remote CI remains unverified. Python 3.11 is declared/test-matrix scope, not a locally observed run (only Python 3.14.3 is installed here). No remote repository or publication was created by this builder.
