# Planning work and bounded optimization

The public SDK/CLI and v1 report formats are unchanged. `plan()` validates the
manifest/assessment association and report integrity first, then constructs one
local `_ScheduleIndex`. It assigns a bit to every artifact and computes the
historical descendant closure, including self, in reverse topological order.
Each action's output mask has a corresponding union of those descendant masks.
This is the history graph, not just that action's future prerequisites: replacing
a valid atomic co-output must invalidate old downstream generations too.

The index is used for candidate relevance, overlapping-producer rejection,
initial reuse exclusion, prerequisite readiness, bounded greedy/reverse deletion
and the final ready frontier. It is constructed for each plan and never reused
across a manifest, assessment or recipe revision. The independent `check_plan`
continues to compute invalidation by walking the historical graph itself and
replaying prerequisites. No catalog instruction is executed by the package.
Cost pruning, 18 relevant actions for exact selection, the `(cost, count, sorted
IDs)` objective, lexical ready-action scheduling and UNKNOWN semantics are intact.

## Measurements

`python benchmarks/planner_work.py --out NEW_FILE.json` creates real temporary
synthetic bytes, changes the source, assesses 1000 artifacts and requests nine
outputs from 18 recipes. The same inputs exercise a long chain and a branching
history, with 999 historical edges. Counters wrap actual legacy descendant/checker
iterations and record the new index's executed graph/readiness operations; they
are not an exhaustive CPU-instruction or constant-time operation budget.

Full plan timing includes association/digest checks, index construction, catalog
closure, all 262144 subset states, existing pruning, scheduling, the final checker
and result construction. File assessment and dense JSON serialization are measured
separately. Tracemalloc index peaks include temporary index-building objects;
mask payload bytes exclude Python object/dictionary overhead. Measurements use
three untraced timing samples; tracing affects serialization/memory timing.

Observed Windows/Python 3.14 ordinary-wheel baseline
`fcdea689bca743dcf651feedf26248ef7135ba9c` and implementation
`1d72e8446fe8bfd94c4388397c0f0d389d94eaf9`:

| Case | Full plan old / new median | Initial mask time / Python peak | Dense JSON size |
|---|---:|---:|---:|
| 1000-artifact chain | 2956.843 / 707.756 ms | 0.730 ms / 424388 B | 4927282 B |
| 1000-artifact branch | 2926.045 / 721.688 ms | 0.456 ms / 312036 B | 503665 B |

Both cases examine 262144 subset states and call the scheduler 150712 times.
The old implementation invokes `_descendants` 19174 times, visiting 19174000
nodes and 19154826 edges. The new implementation invokes it zero times: index
initialization assigns 1000 artifact bits, visits 2000 historical nodes and 1998
edges, and resolves 18 action output closures. The final checker still visits
1000 nodes/999 edges in each case. Subset checks still inspect 576336 selected
actions and perform 410031 readiness checks. Raw manifest and entire dense
assessment/plan JSON hashes match before and after, not merely the cost field.

The old/new complete-plan Python-allocation peak is 8808108/8808148 B for the
chain and 943788/943828 B for the branch: no allocation-peak reduction is claimed.
The old process lifetime peak RSS was 47386624 B before and after planning;
the separate new process measured 47239168 B before and after. RSS is
lifetime-wide, not plan-owned memory or evidence of a meaningful reduction. The chain's
old dense serialization alone took 301.406 ms under allocation tracing versus
26.814 ms for the branch. Long cause paths/full reports remain substantial.
Index storage is an additional cost even when a plan needs no actions.

The already-valid 10-artifact/18-recipe branching case had identical full output
but old/new full-plan medians of 0.051/0.109 ms over seven samples. This slowdown
is retained, not omitted. An index is not automatically cheaper for small or
clean snapshots. These are disclosed local synthetic measurements, not a
production throughput claim or proof that every workload improves.

## Bounds and verification

Masks contain at most 1000 bits. Their operations have multiword cost; descendant
storage can use O(V^2) bits plus objects, with O(A*V) action-mask bits. Graph visits
are reduced, while subset enumeration remains exponential and dense cause-path
output remains proportional to the report. None of the existing artifact, edge,
file, cause or exact-action limits were increased.

The original suite, generation cheap-batch counterexample, retained workflow,
source withdrawal/alternatives, duplicate producers, file safety and assessment
digest rejection remain exercised. New tests independently breadth-first walk
raw historical dependencies, enumerate selected catalogs and every eligible
forward execution order for 120 new fixed-seed cases, and check infeasibility,
cost/count/lexical ties, complete order, ready frontier, reuse and unchanged
inputs/files. A targeted test prohibits repeated historical `_descendants`
calls during planning. Retained reviewer-owned 120 dynamic-order catalogs are
also run from unchanged copies; finite oracle agreement is not a general proof
or source/recipe authentication.
