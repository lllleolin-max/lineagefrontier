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

## Additional workflow correction — persist retained demo recapture

Before: `3b929ddf0f9b6092320008cc212704e08b268f13`. Root/peer review found `refresh_records()` changed inventory/statements only in memory; only `create()` wrote `manifest.json`. Consequently the demo printed `after_execution_and_recapture_stale: []` while a later installed CLI loaded old records, found six stale artifacts and planned the original 11-unit repair. This correction is additional to, and does not replace, the three original cycles above. Implementer: GPT-6.1-Sol / Ultra, under root's explicit scope extension.

Actual fail-before command: `.venv-release/Scripts/python -m unittest discover -s tests -p test_retained_workflow.py -v` exited 1, one failed test: separate CLI returned `['chart', 'cleaned', 'metrics', 'model', 'raw', 'release'] != []`. The test starts the demo subprocess, then an independent installed CLI subprocess against the retained disk manifest; it also checks revoked-source alternative cost 15. Correction: persist fresh inventory and raw statements to the same `manifest.json` after successful execution/recapture. No core source algorithm changes.

After correction: `f59880cc9cf0b7382097bbcb03d73684cec899fa` (`Persist retained demo inventory after provenance recapture`). Rebuilt a normal wheel with `py -3 -m pip wheel --no-deps --wheel-dir dist .` and force-installed `dist/lineagefrontier-0.1.0-py3-none-any.whl` into `.venv-release`. `.venv-release/Scripts/python -m unittest discover -s tests -v` exited 0: 29 run, 28 passed, 1 skipped (unchanged Windows symlink privilege limitation). New separate-process regression passed.

Actual SDK demo `.venv-release/Scripts/python examples/workflow.py --keep demo-work` and executed contrast `.venv-release/Scripts/python benchmarks/compare.py` exited 0. Installed console CLI `.venv-release/Scripts/lineagefrontier plan demo-work/manifest.json --root demo-work --request release` reported stale count 0, cost 0, action count 0. Adding `--revoke raw=withdrawn` reported cost 15 and `[recover-clean, fit-batch, chart, bundle]`. Core `src/` diff from the before SHA is empty. Local checks remain Windows/Python 3.14.3; no remote CI result is claimed. The retained demo explicitly overwrites its named synthetic fixture files as documented; the library still does not execute manifest commands.
