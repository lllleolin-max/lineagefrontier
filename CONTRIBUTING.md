# Contributing

Use Python >=3.11. Build a wheel and install it into a clean virtual environment, then run `python -m unittest discover -s tests -v`, `python examples/workflow.py`, and `python benchmarks/compare.py`. Keep source imports out of install verification. CI tests Ubuntu/Windows and Python 3.11/3.14; unrun remote CI is unknown.

Changes to the optimizer need small independent action-order oracle cases, replay checks for every feasible plan, and permutation tests. Format widening must state exact interoperability and reject unsupported ambiguity. Never turn a bound into an optimality claim, signer text into authentication, or a conditional plan into a successful build. Add true failure cases to benchmark evidence. Do not change tests only to agree with an incorrect implementation. MIT licensing applies to contributions.
