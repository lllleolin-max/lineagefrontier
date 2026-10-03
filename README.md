# LineageFrontier

Decide which release or research artifacts need rebuilding after a local input changes or an owner withdraws an input. Read an in-toto/SLSA provenance subset, verify actual file bytes, explain affected deliverables, then price a prerequisite-respecting rebuild using declared atomic multi-output actions. Independent valid branches stay reusable.

用于发布工程和研究制品管理：核验本地真实字节；输入改变或显式撤销后，解释哪些成果过期、证据经过哪些依赖；为指定交付物选择有成本和先后顺序的重建方案。共享动作的多个输出只收费一次，声明的替代配方可以绕开被撤销的输入。

## Install and run / 安装与完整演示

Python >=3.11, standard-library runtime. From the repository:

```sh
python -m pip install .
python examples/workflow.py
python benchmarks/compare.py
python -m unittest discover -s tests -v
```

The demo writes synthetic research inputs and derived files in a temporary directory, records SHA-256 and raw in-toto statements, changes `raw.bin` without renaming it, verifies the impact, chooses `clean → fit-batch → chart → bundle` at cost **11 declared units**, executes its own fixed demo transforms and captures fresh provenance. The independent `notes-html` branch remains reusable. After actual execution/recapture, no artifacts are stale. No manifest instruction is executed by the package.

演示完成“输入→记录→字节核验→输入变更→影响证据→重建决策→实际演示执行→重新记录”的完整流程。预期过期制品为 `chart, cleaned, metrics, model, raw, release`，代价 11；这不是实际美元、秒数或用户收入。示例使用公开的合成材料。

To inspect the CLI on a retained synthetic fixture (its manifest is refreshed at the end):

```sh
python examples/workflow.py --keep demo-work
lineagefrontier digest --root demo-work raw.bin
lineagefrontier plan demo-work/manifest.json --root demo-work --request release
lineagefrontier plan demo-work/manifest.json --root demo-work --request release --revoke raw=withdrawn
```

JSON on stdout. Exit `0` means a conditional feasible decision, `2` invalid input/file-safety error, `3` no plan. `optimality: EXACT` certifies the minimum total declared cost **within the supplied catalog** with ties by fewer actions then lexicographic action IDs. `UNKNOWN` supplies a checker-verified upper bound, never a minimum claim. `ready_frontier` lists selected actions ready now; `execution_order` includes every prerequisite step. The returned plan is conditional on the declared recipe inputs being complete and successful execution; verify and reattest outputs afterward.

## SDK

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

输入表的 `kind=input` 是当前原材料；变更后的原材料可提供新字节供重建，但旧版后代均失效。撤销/缺失的输入不可复用。`kind=output` 必须具有来源记录，字节匹配和整个历史依赖均有效才可复用。撤销的是记录的旧制品版本；可通过合法动作重新生成新版本，永久封禁逻辑名称须由外部策略处理。

## Evidence, limits and comparisons

An assessment reports every artifact's recorded/current SHA-256, file verification, staleness and one deterministic shortest path per direct cause. Builder IDs remain **unauthenticated claims**. This tool neither verifies DSSE/signatures nor awards SLSA levels; hashes do not establish identity, completeness of provenance or the truth of remote files. It performs local read-only checks and planning, not arbitrary build execution or remote downloads.

The executed benchmark compares (1) actual requested-file checksums, (2) an explicit fixed-history rebuild-all recipe, (3) removal of atomic batching, (4) removal of the alternate recovery recipe. The changed-input fixture retains byte-identical `release.bin`; its checksum passes although its provenance is stale. A shared batch costs 5 versus independent model/metrics recipes costing 7. The revoked-source case needs the explicitly declared recovery recipe. A missing-source case is infeasible. There is no claim that GNU Make, SLSA or in-toto cannot support similar workflows, nor that a full incumbent was benchmarked.

The useful combination is **historical digest invalidation + current local sources + future action catalogs with atomic co-outputs + checked costed decisions**. It differs from claim/answer freshness systems: these are real software/data files, producer records, source byte verification and concrete rebuild prerequisites. Alternative recipes are caller-supplied acceptable ways to make a logical deliverable, not inferred scientific equivalence or predicted output bytes.

See [format and architecture](docs/ARCHITECTURE.md), [bounded commercial rationale](docs/COMMERCIAL.md), [security](SECURITY.md), [contributing](CONTRIBUTING.md), and [real iteration evidence](docs/ITERATIONS.md). Checked-in CI covers Ubuntu/Windows with Python 3.11/3.14; local verification is distinct from remote CI success.
