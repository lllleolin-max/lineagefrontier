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

## 0.2.0 self-review 1 — measure repeated graph work, then precompute

Baseline: `fcdea689bca743dcf651feedf26248ef7135ba9c` (0.1.0).
Parallel README additions `39ee94aca5b240a627d7511b1a4e09e73bec22cc`
were preserved through normal fast-forward. Implementation:
`1d72e8446fe8bfd94c4388397c0f0d389d94eaf9`.

The baseline canonical LF archive/ordinary wheel/fresh isolated site bytes matched
all six raw Git modules; pip check returned 0. Its original 29 tests ran in
3.075 s, 28 passed and one Windows file-symlink privilege test skipped. The
optimization started as a static scale candidate, not an already measured
performance regression or incorrect baseline decision. Actual synthetic 1000-node
chain/branch, 999 edges and 18-recipe probes each examined 262144 subset states,
scheduled 150712 candidates and performed 19174 complete descendant walks:
19174000 node and 19154826 edge visits. Full-plan medians were 2956.843 and
2926.045 ms. Dense JSON was 4927282 and 503665 B, measured separately.

One invocation-local index now computes each artifact's historical descendant
mask, including itself, and action input/output/invalidation masks. The same
index serves relevant closure, subset scheduling, fallback/reverse deletion and
ready-frontier calculation. Atomic co-output historical generation exclusion and
the independent final checker remain unchanged. Exact limits were not raised.
The implementation's new ordinary wheel passed the original 29 tests in 3.312 s
with the same permission skip. This is one substantive optimization; no new
correctness defect or artificial fail-before test is claimed.

## 0.2.0 self-review 2 — independent forward catalogs and honest costs

Verification changes: `958ebd17a5bd15735ad17e8f5e2ec0549a7f245d` (0.2.0),
with package source identical to `1d72e84`; new tests, benchmark, metadata and
documentation were added. No second source correction is claimed.

Two new tests passed against the normally installed implementation (2.589 s).
One covers 120 new fixed-seed raw catalogs, computes availability through an
independent breadth-first historical walk, and enumerates eligible forward
execution orders. It checks feasibility, cost, action count, lexical ties,
complete execution order, ready frontier, reused slots and unchanged raw data,
assessment, requests and file bytes. The other prohibits repeated full
`_descendants` calls while exercising the cheap batch/history-descendant case
and edited-assessment rejection. Unchanged copied prior reviewer probes ran
7 tests in 3.531 s, including another 120 dynamic-order catalogs with no mismatch
and actual Windows root-escaping junction rejection. Old reviews were not edited.

The 1000-artifact/18-recipe probe preserved complete dense JSON hashes. Full-plan
medians became 707.756 ms (chain) and 721.688 ms (branch). Every plan constructs
1000 artifact bits, visits 2000 historical nodes/1998 edges and performs 18
output-closure lookups; the final checker still visits 1000 nodes/999 edges.
Subset state/scheduler counts remain 262144/150712. Index construction costs
0.730 ms/424388 B Python peak for the chain and 0.456 ms/312036 B for the branch.
Complete-plan allocation peaks were effectively unchanged (old/new chain
8808108/8808148 B; branch 943788/943828 B). Lifetime process RSS is recorded
separately and is not plan-owned memory. An already-valid 10-artifact case became
slower: old/new medians 0.051/0.109 ms, with identical output. These unfavorable
costs and dense path output are retained. No total constant-memory, sublinear
solver or production latency promise follows from fewer graph visits.

## 0.2.0 self-review 3 — ordinary installed SDK and actual CLI handoff

At `958ebd17a5bd15735ad17e8f5e2ec0549a7f245d`, a fresh canonical LF archive,
ordinary 0.2.0 wheel and isolated site installation matched all six raw Git
module byte sequences; pip check returned 0. The complete suite ran 31 tests in
5.638 s: 30 passed, one unchanged Windows symlink privilege skip. The original
29 tests were unchanged, including generation consistency, duplicate producers,
association errors and bounded resource checks.

The actual sysconfig console executable ran 24 commands across native and
`PYTHONUTF8=0/1` modes. A separate retained demo handoff reports clean/cost 0;
raw-source withdrawal selects recovery at cost 15; another real raw-file change
and fresh assessment selects cost 11. Assessment/planning preserve manifest and
artifact bytes. An old assessment remains an explicit old snapshot and must be
replaced by reassessment after external writes; the test does not pretend the
planner automatically rehashes files. Altered availability is rejected. Removing
both source alternatives yields exact INFEASIBLE/exit 3, while the bounded
failure is UNKNOWN/exit 4. The original seven-case comparison and actual demo
execution/recapture passed, including rejection of the cheap generation ablation.

No new source defect was found in this round; it verifies integration and does
not fabricate a third repair. The final following documentation-only revision is
bound by its own canonical archive/wheel/site association and full-suite record.
Independent scoring and remote CI/publication are separate work. Historical
three corrections and retained-workflow failure remain unchanged; no adoption,
revenue or production claim is made.
