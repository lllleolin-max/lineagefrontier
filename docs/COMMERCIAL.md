# Bounded pilot value / 商业价值边界

Potential operator: a research engineer or release engineer reviewing generated models, metrics, plots and release bundles with provenance records. The owner withdrawing a data source or replacing local bytes needs an auditable deliverable-specific rebuild decision while retaining independent notes/documentation branches. SLSA's documented use cases establish provenance verification/rebuilding as real workflows; they do not validate demand for this particular package.

The synthetic demo shows a concrete decision: input bytes change under the same filename, final artifact bytes still match their historical checksum, yet rebuilding is required. Requesting the release costs 11 declared units rather than 13 for the supplied full history rebuild. Atomic shared model+metrics generation costs 5 rather than 7 in separate declared recipes. With a withdrawn source, the caller-supplied curated backup recipe yields a conditional plan at cost 15; removing that recipe proves infeasibility. Missing both sources is deliberately a failure case.

If a team calibrates one unit to one runner-minute and executes exactly those successful recipes, the changed-source case saves 2 minutes per such event. At N matching events/year and p currency/minute, modeled compute savings = 2*N*p; neither N nor p is measured here. Review labor, avoided invalid releases and willingness to pay are unknown. The 15-unit revoked-source plan costs more than the ordinary rebuild because a different approved preparation recipe is required. No observed customer, adoption or revenue is claimed.

接入方式：从既有构建流程导出原始 in-toto Statement/SLSA SHA-256 记录，补充本地路径及经过审核的动作成本目录；CI 先运行 CLI；人或外部构建系统执行返回顺序，然后核验新字节并重新生成来源记录。当前包不提供企业签名策略、远端缓存、任务运行器或完整 SLSA 认证。

This MIT package is a bounded local pilot. Sustainability depends on keeping the supported subset explicit, rejecting ambiguous imports, retaining deterministic evidence and accepting focused tests. Potential paid integration/support is a hypothesis, not an established business. A full build system may be more suitable when execution, parallel scheduling or authenticated remote caches are the principal requirement.
