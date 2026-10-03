# Real review and correction history

Initial implementation and verification are recorded separately from the three required post-implementation review cycles. Each later entry records a reproduced deficiency, substantive correction, fail/pass command and before/after commit. This file is filled from actual runs; no independent score is claimed.

## Initial complete implementation (not a review round)

Windows / Python 3.14.3. Built a non-editable wheel with `py -3 -m pip wheel --no-deps --wheel-dir dist .`, created `.venv-check`, installed with `.venv-check/Scripts/python -m pip install --no-index --find-links dist lineagefrontier`. `python -m unittest discover -s tests -v`: 11 passed. Actual `examples/workflow.py`: cost 11, order clean/fit-batch/chart/bundle, notes branch preserved, post-execution recapture stale list empty. `benchmarks/compare.py`: changed-source 11 versus rebuild-all 13 / unbatched 13; revoked-source 15 versus fixed history infeasible; missing inputs infeasible; bounded search UNKNOWN with nonoptimal cost 13. Results are synthetic declared units, not wall-clock cost claims. No remote CI run yet.

## Review 1 — strict JSON/provenance parsing

Before: `1bca610f53a229a867598df374ca6ea038568c81`. Review found the standard JSON loader silently accepted duplicate fields (last value won) and NaN in ignored extensions, `True == 1` accepted an invalid version, and `value or empty` accepted false/empty wrong-typed optional provenance fields. This permitted ambiguous wire evidence, not merely cosmetic input variation.

Reproduction before correction: `.venv-check/Scripts/python -m unittest discover -s tests -p test_boundary_review.py -v` exited 1: 5 tests, 4 failures (`LineageError not raised`). Correction: duplicate-key hook, nonfinite rejection, exact integer version type, null-only optional coercion, bounded actual manifest read and actionable JSON nesting failure.

Verification: rebuilt wheel and force-reinstalled it; `.venv-check/Scripts/python -m unittest discover -s tests -v` exited 0, 16 passed; demo and benchmark exited 0 with unchanged intended 11-unit plan. Fix commit subject: `Reject ambiguous JSON and wrong-typed provenance values`; exact after SHA is in the final history table below. Remaining boundary: supported subset only; no signature or remote verification.
