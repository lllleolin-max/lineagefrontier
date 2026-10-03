# 为什么做、作用和怎么用

发布工程师或科研工程师常同时保存模型、指标、图表和发布包。最终文件本身的校验和没有变化，不表示它使用的原始测量数据仍然有效。数据源换了字节、某个历史结果被撤销时，既要重新生成真正受影响的交付物，也要保留有效的独立分支。

LineageFrontier 把“历史制品是什么来源”与“现在允许怎样重建”分开。它用 SHA-256 解析原始 in-toto Statement v1 / SLSA provenance v1 子集，实际读取根目录中的文件，给出每个过期制品的来源证据路径。动作目录记录每个动作消耗的输入、原子输出组和成本单位。软件会为请求的交付物选择有前置依赖顺序的方案，并通过另一个前向 checker 核验。共同生成模型和指标只收费一次；批量覆盖仍有效的指标时，旧图表也要失效，防止混用两代成果。

## 本地安装和试用

```sh
python -m pip install .
python examples/workflow.py
python benchmarks/compare.py
```

第一个命令安装 SDK 与 `lineagefrontier` CLI。第二个命令创建真实合成文件、记录来源、改变同名输入文件、输出影响和重建顺序、执行演示函数、重新核验；看到 `cost=11`、顺序 `clean/fit-batch/chart/bundle`、`notes_branch_preserved=true`、重新记录后 `stale=[]`。第三个命令对比逐文件校验、全部重建、移除共享输出/替代配方/版本一致性等机制；数值是预先声明的合成成本单位，不是实测时长、收入或客户收益。

```sh
python examples/workflow.py --keep demo-work
lineagefrontier plan demo-work/manifest.json --root demo-work --request release --revoke raw=withdrawn
```

保留示例后，撤销 raw 会使用声明的 backup 恢复配方，代价 15。替代配方是否科学或技术等价必须由使用方明确批准，程序不会从文件名或自然语言推断。用户实际接入时，从已有构建系统导出裸 attestation，添加本地 inventory 路径和经过审阅的 action 目录；在稳定快照上运行决策，再由外部构建系统执行，最后核验并重新记录来源。

## 结果边界

最多 18 个相关动作进行精确子集求解，最小化的是所给目录及“每个输出槽每计划最多一个 producer”范围内的总成本。超过边界返回 `optimality=UNKNOWN`，有方案则是已核验上界；未找到方案也不会声称不可行。精确范围内找不到受支持方案返回 INFEASIBLE。目录中可有替代 recipe，但一个计划不能选择会重复生成同一槽的动作组合。

来源记录和 builder 字符串均不是身份认证。当前只核验本地 SHA-256；不验证 DSSE/签名，不下载远端材料，不授予 SLSA 等级，不运行清单中的命令。对文件变化、错误/不完整来源、失败构建和配方等价的保证均有明确边界。商业上可作为本地 pilot，真实用户、采纳、收入和愿付价格全部未知；最终三个维度评分应由独立审阅者给出，构建者未自称过门槛。
