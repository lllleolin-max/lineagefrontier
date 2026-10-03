# LineageFrontier

Decide which release or research artifacts need rebuilding after a local input changes or an owner withdraws an input. Read an in-toto/SLSA provenance subset, verify actual file bytes, explain affected deliverables, then price a prerequisite-respecting rebuild using declared atomic multi-output actions. Independent valid branches stay reusable.

用于发布工程和研究制品管理：核验本地真实字节；输入改变或显式撤销后，解释哪些成果过期、证据经过哪些依赖；为指定交付物选择有成本和先后顺序的重建方案。共享动作的多个输出只收费一次，声明的替代配方可以绕开被撤销的输入。

## Install and run / 安装与完整演示

Install from a source checkout with Python 3.11+:

```sh
git clone https://github.com/lllleolin-max/lineagefrontier.git
cd lineagefrontier
```

Linux/macOS:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install .
.venv/bin/python examples/workflow.py
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.venv\Scripts\python.exe -m pip install .
.venv\Scripts\python.exe examples/workflow.py
```

In the remaining examples, `python` means this environment's interpreter:
`.venv/bin/python` on Linux/macOS or `.venv\Scripts\python.exe` on Windows.
The runtime uses the standard library; source installation may download build
dependencies. No PyPI release is required for these instructions.

The first run exits `0` and prints JSON: `changed_stale` contains the six
artifact IDs below, `decision.cost` is `11`, `notes_branch_preserved` is `true`,
and `after_execution_and_recapture_stale` is `[]`. Its temporary fixture is
removed afterward. Optional checks: `python benchmarks/compare.py` and
`python -m unittest discover -s tests -v`.

The demo writes synthetic research inputs and derived files in a temporary directory, records SHA-256 and raw in-toto statements, changes `raw.bin` without renaming it, verifies the impact, chooses `clean → fit-batch → chart → bundle` at cost **11 declared units**, executes its own fixed demo transforms and captures fresh provenance. The independent `notes-html` branch remains reusable. After actual execution/recapture, no artifacts are stale. No manifest instruction is executed by the package.

演示完成“输入→记录→字节核验→输入变更→影响证据→重建决策→实际演示执行→重新记录”的完整流程。预期过期制品为 `chart, cleaned, metrics, model, raw, release`，代价 11；这不是实际美元、秒数或用户收入。示例使用公开的合成材料。

To inspect the CLI on a retained synthetic fixture (its manifest is refreshed at the end):

```sh
python examples/workflow.py --keep demo-work
python -m lineagefrontier digest --root demo-work raw.bin
python -m lineagefrontier plan demo-work/manifest.json --root demo-work --request release
python -m lineagefrontier plan demo-work/manifest.json --root demo-work --request release --revoke raw=withdrawn
```

`--keep` writes and overwrites the demo's named fixture files in the selected
directory. Use a dedicated demo directory, not a directory holding real artifacts.
The installed `lineagefrontier` command is equivalent to the module form above.

The separate retained CLI run without revocation reports `assessment.stale: []`, `plan.cost: 0` and no execution actions. With `--revoke raw=withdrawn`, it reports cost **15** and `recover-clean → fit-batch → chart → bundle`. The demo persists the recaptured inventory and statements to the same `manifest.json`, so these checks read fresh records from disk rather than an in-memory snapshot.

保留演示目录后，单独 CLI 无撤销应报告零过期、零成本；撤销 `raw` 后选择替代恢复方案，成本 15。重新采集的记录实际写回 `manifest.json`，不是仅在演示进程内显示成功。

JSON on stdout. Exit `0` means a conditional feasible decision, `2` invalid input/file-safety error, `3` proven infeasible within the supported unique-producer model, `4` bounded search found no plan and cannot decide. `optimality: EXACT` certifies the minimum total declared cost **within the supplied catalog and at most one producer per output slot per plan**, with ties by fewer actions then lexicographic action IDs. `UNKNOWN` with a feasible plan supplies a checker-verified upper bound, never a minimum claim. `ready_frontier` lists selected actions ready now; `execution_order` includes every prerequisite step. The returned plan is conditional on the declared recipe inputs being complete and successful execution; verify and reattest outputs afterward.

## SDK

Run after the retained-fixture command above. For your own build, provide a local
file root, inventory/provenance manifest and reviewed action catalog. Read the
assessment to decide what is stale, pass requested deliverable IDs to the planner,
execute approved actions in your own runner, then capture and reassess new records.
[中文实操手册](docs/RUNBOOK.zh-CN.md) covers this handoff.

```python
from lineagefrontier import load_manifest, assess, plan, check_plan

manifest = load_manifest("demo-work/manifest.json")
snapshot = assess(manifest, "demo-work", revoked={"raw": "withdrawn input"})
decision = plan(manifest, snapshot, ["release"], exact_limit=18)
# plan() already invokes the independent forward checker for feasible outputs.
verified = check_plan(manifest, snapshot["available"], ["release"],
                      decision["execution_order"])
```

Use `Manifest.from_dict()` for existing bare attestation JSON plus local inventory and a reviewed action catalog. The example constructs every field. Inventory IDs are local logical slots; provenance edges match SHA-256, **regardless of names**, and paths identify current files only. Missing nodes, duplicate IDs or ambiguous duplicate inventory digests, repeated output provenance and provenance cycles are rejected. Valid renamed files are reusable after updating their locator.

Version 0.2 precomputes historical descendant and action input/output masks for
each `plan()` invocation. Candidate subsets reuse those masks instead of walking
the complete historical graph again. Atomic co-output replacement still
invalidates every historical descendant, and the separate forward checker still
replays a selected plan against the full graph. The 18-action exact bound, tie
rules, conditional execution and UNKNOWN fallback remain unchanged; no masks
are reused across manifests or assessments.

To measure a disclosed 1000-artifact chain and branch with 18 candidate actions:

```sh
python benchmarks/planner_work.py --out planner-work.json
python benchmarks/planner_work.py --artifacts 10 --shapes branch --clean --samples 7 --out small-clean-work.json
```

Choose new output filenames: the benchmark refuses to overwrite existing files.
It constructs and assesses real temporary synthetic files, then reports complete
plan timings, graph visits, index allocation cost and dense JSON size/cost.
The larger local case improved, while an already-valid 10-artifact case became
slower because it still builds the index. Dense witness output and the bounded
exponential subset search remain real costs. These are measured synthetic cases,
not production latency or memory guarantees. [Cost scope and results](docs/PLANNER_WORK.md).

输入表的 `kind=input` 是当前原材料；变更后的原材料可提供新字节供重建，但旧版后代均失效。撤销/缺失的输入不可复用。`kind=output` 必须具有来源记录，字节匹配和整个历史依赖均有效才可复用。撤销的是记录的旧制品版本；可通过合法动作重新生成新版本，永久封禁逻辑名称须由外部策略处理。

0.2 在一次规划内预计算历史后代失效集合及动作 bitmasks，减少候选子集重复全图遍历；仍保留原子多输出的代际失效与独立 checker 完整重放。18 动作上限、成本与平局规则、UNKNOWN 边界不变。映射不跨 manifest/assessment 缓存；初建有额外内存与时间，小型且已经有效的输入可能更慢。

## Evidence, limits and comparisons

An assessment reports every artifact's recorded/current SHA-256, file verification, staleness and one deterministic shortest path per direct cause. Builder IDs remain **unauthenticated claims**. This tool neither verifies DSSE/signatures nor awards SLSA levels; hashes do not establish identity, completeness of provenance or the truth of remote files. It performs local read-only checks and planning, not arbitrary build execution or remote downloads.

Assessments bind their inventory/provenance revision and report digest. Keep them intact; JSON roundtrips and recipe-only cost changes are supported. Reassess after files or recorded provenance change. These unkeyed digests prevent accidental mixups and do not authenticate a report author.

The executed benchmark compares (1) actual requested-file checksums, (2) an explicit fixed-history rebuild-all recipe, (3) removal of atomic batching, (4) removal of the alternate recovery recipe. The changed-input fixture retains byte-identical `release.bin`; its checksum passes although its provenance is stale. A shared batch costs 5 versus independent model/metrics recipes costing 7. The revoked-source case needs the explicitly declared recovery recipe. A missing-source case is infeasible. There is no claim that GNU Make, SLSA or in-toto cannot support similar workflows, nor that a full incumbent was benchmarked.

It also executes direct-only invalidation and generation-consistency ablations. In the latter, an inexpensive batch replaces a rejected model **and valid metrics**. Reusing the old chart gives a 2-unit plan that the independent checker rejects; the valid plan includes chart rebuilding and costs 4, while a model-only alternative costs 5 and preserves that chart. Feasible benchmark plans run the fixed demo transforms and recapture actual SHA-256. The synthetic owner explicitly approves fresh rebuilt output records and clears their old-record revocations; revoked input policy remains active. The library never clears revocation policy itself. [Recorded results](docs/BENCHMARK_RESULTS.json) include both infeasible and UNKNOWN boundaries.

The useful combination is **historical digest invalidation + current local sources + future action catalogs with atomic co-outputs + checked costed decisions**. It differs from claim/answer freshness systems: these are real software/data files, producer records, source byte verification and concrete rebuild prerequisites. Alternative recipes are caller-supplied acceptable ways to make a logical deliverable, not inferred scientific equivalence or predicted output bytes.

See [format and architecture](docs/ARCHITECTURE.md), [bounded commercial rationale](docs/COMMERCIAL.md), [security](SECURITY.md), [contributing](CONTRIBUTING.md), and [real iteration evidence](docs/ITERATIONS.md). Checked-in CI covers Ubuntu/Windows with Python 3.11/3.14; local verification is distinct from remote CI success.
