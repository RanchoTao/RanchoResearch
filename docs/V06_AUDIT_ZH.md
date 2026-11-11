# v0.6 现状审计（P0，修改前）

审计日期：2026-11-01。对象为 RanchoTao/RanchoResearch，基线提交
`1ca8c5e1023df0d27085dcdcf75bf51907f92612`。使用隔离浅检出；没有修改旧
AutoResearchClaw 工作区，没有恢复历史 HOLD 课题，也没有远程写入。
本报告是代码与本地测试审计，不是科学成果认证或完整安全审计。

## 实际能力与证据

| 能力 | 实现与调用证据 | 判定及边界 |
|---|---|---|
| 23 阶段流水线 | `researchclaw/pipeline/stages.py` 的 Stage/StageStatus；`executor.py:execute_stage`；`runner.py:execute_pipeline` | 有真实实现与大量本地 mock 测试；不是仅有接口。任务由 run_dir 工件、StageResult、stage 元数据传递，失败/暂停/回滚由 runner 管理。没有本轮真实模型全链路验收。 |
| 文献与假设 | `stage_impls/_literature.py`、`_synthesis.py`，literature 搜索客户端 | 存在 API 和模型路径及离线模板；输出存在不证明检索覆盖或原创。Skill 的相关工作审核主要仍是提示词方法。 |
| 实验设计/代码 | `_experiment_design.py`、`_code_generation.py`、experiment validator | 可生成与执行代码，AST/入口检查有测试；冻结测量规则与实际执行逐项一致尚无统一硬门。 |
| 实验执行 | `_execution.py:_execute_experiment_run` | sandbox/docker 真实执行、远程及领域适配存在；simulated 明确标记但后续汇总仍能读取。sandbox 主要是子进程，不能视为恶意代码的完整安全边界。未验 Docker、SSH、GPU、领域执行环境。 |
| 汇总与失败 | `_helpers.py:_collect_experiment_results`；`_analysis.py` | 原始 run 文件保留，但聚合未统一过滤运行 status；有限值过滤不等于将整个测量置 INVALID。工程失败与科学阴性尚无统一五轴传播。 |
| 科研决策 | `_analysis.py:_execute_research_decision`，runner 的 pivot/refine | 有决策和有限循环。runner 在资源/循环止损后存在强制 PROCEED 路径，不能作为科学成功证据。 |
| 数值注册表 | `verified_registry.py:VerifiedRegistry`，`tests/test_verified_registry.py` | 有有限值、条件、四舍五入和差值核对；来源是聚合 JSON，没有统一原始运行/哈希核验。非空不证明真实实验，数值相同不证明上下文相同。 |
| 论文审核 | `paper_verifier.py`、`_review_publish.py` | 有确定性 LaTeX 数值检查及测试；默认常数白名单/宽容区段，注册表为空、异常及 ablation 路径可跳过；Stage22 发现问题后存在清洗再继续，不能称完全 fail-closed。 |
| HITL/权限 | executor pre/post、`hitl/`、config、CLI | 存在暂停、成本、人工介入工具；旧 gate 在执行后应用，可 auto-approve，SKIP 可直接返回 DONE。不能把它当自动执行前的完整授权检查。`allow_publish_without_approval` 没有完整生产调用。Stage22 主要是本地导出。 |
| ClaimVerifier/checksum | `hitl/claim_verifier.py`、`hitl/checksums.py` | 有代码和单测；未发现流水线生产调用，不能当强制证据绑定。 |
| 科研状态 | `autoresearch_state/`、`schemas/research_state_v0.1.schema.json` | 有稳定 ID、证据支持/反对关联、supersedes、checkpoint、分支状态及验证 CLI；没有 claim_version 与五轴运行契约，没有不可覆盖版本库，也没有语义级重复课题识别。 |
| 运行恢复/记忆 | checkpoint、`memory/`、hitl/copilot branching | 工件支持阶段恢复；通用 MemoryStore 可裁剪重写，不能充当科学证据账本。runner 的 ExperimentMemory 构造/record_outcome 与实现不匹配且吞异常；event_log/cost_tracker 导入目标缺失。自动记忆及预算覆盖不能宣称已验证。 |
| 研究 Skill | `.agents/skills/research-evidence-gate/SKILL.md` 指向 canonical builtin Skill | 已加载的方法规则，不是运行门禁。五轴、精确先例、测量、简单基线、曝光历史等规则尚未统一代码化。 |
| ARC-Bench | `experiments/arc_bench/` manifest/rubric/adapter/scripts | 有现成对照框架；旧原始结果不在发布树。本轮未运行代理科学基准，不能从单测或官方自报推导性能提升。 |

流水线顺序：1–2 目标拆分；3–6 文献；7–8 综合与假设；9–11 设计/代码/资源；
12–13 运行与优化；14–15 分析决策；16–19 写作与评阅；20–23 质量、归档、本地导出、引用。
每个 executor 都有函数实现；LLM、网络、外部工具是否可用取决于环境。
离线模板/mock/simulated 测试只支持软件控制流程结论。

## 初始测试与不确定性

Python 3.13.9 / Windows。本地初始定向检查：41 passed、4 skipped、8 failed，
另有 18 subtests passed。失败均为两个状态测试依赖已删除的个人研究示例（首轮只运行了其中 schema 文件）。
全量测试在修改前启动，结果见最终验证报告；不把原有失败归因于本轮补丁。
未运行 e2e_real_llm、真实远程计算或付费裁判。没有穷尽旧 Git 历史的敏感内容；
浅检出不足以做历史清除结论。

## 上游归属与许可证

`THIRD_PARTY_NOTICES.md`、根 Apache-2.0、`LICENSES/AutoResearchClaw-MIT.txt`
共同定义发行边界；后者保留 2026 Aiming Lab MIT 版权。researchclaw 名称空间及大量
流水线/基准继承上游，不能改称独立开发。`autoresearch_state`、软件发布边界及
research-evidence-gate 属于当前项目扩展，但浅历史不能逐行证明独立权属。
`external/agents` 的 Biology-Agent/stat_research_agent 未找到独立 LICENSE 文件，
ColliderAgent 是指针；第三方再发行核验仍未完成。保留文件与声明，不擅自删除或重许可。

## 最小决策矩阵

| 对象 | 决策 | 原因 |
|---|---|---|
| 现有 23 阶段、CLI、import、工件/检查点 | KEEP | 已有成熟执行链，避免整体重写。 |
| VerifiedRegistry/论文检查 | MODIFY/REUSE | 复用数字与来源能力，在关键阶段外层加入不可跳过的真实性门。 |
| evidence Skill | KEEP | 方法仍需人或研究代理判断，补充实际运行覆盖说明。 |
| 状态 v0.1 | KEEP + additive sidecar | 不改历史格式；用主张版本快照和审查记录关联现有 ID/工件。 |
| 统一 runtime gate、执行收据与冻结核对 | ADD | 这是已证实缺口；共享一套检查，避免各阶段再做互相冲突的裁决。 |
| 私有示例依赖/安装后 schema | MODIFY | 用通用 synthetic fixture 修复测试，补 wheel 资源，保留旧契约。 |
| 两套分支、失效记忆/遥测 hooks | HOLD consolidation | 暂不扩大重构；明确它们不能替代不可覆盖科学记录。 |
| 大型外部集成/新数据库/新前端 | KILL for this scope | 尚无对照收益证据，当前文件工件足够。 |
| MLflow/LangGraph/Prefect/PaperQA2/GPT Researcher/AIDE | DEFER | 对现有能力的局部增益未被实测；先修正证据边界。 |

实施范围：本地 JSON 证据契约、原始执行收据、版本化不可覆盖记录、统一前后置门、
中文 CLI 解释、关键负例与一个受控 CPU 实验、固定预算评测方案。理论证明、
领域测量语义、真正独立新颖性判断继续保留人工审核/UNKNOWN；不冒充通用科学裁判。
