# RanchoResearch v0.6 本地升级交付

日期：2026-11-01。基线：`1ca8c5e1023df0d27085dcdcf75bf51907f92612`；
本地分支：`upgrade/evidence-runtime-v06`。没有推送、提交论文、外部发布、
使用付费模型/GPU或恢复历史研究队列。工作对象是指定 RanchoResearch 的隔离检出，
不是带大量未提交历史研究的旧 AutoResearchClaw 工作区。

**总判断：MODIFY。** 受控本地证据一致性 MVP 已有可执行门禁和回归证据；
真实代理科研能力、科学新颖性、普遍复现能力和发行成熟度仍不能给 GO。

## 1. 现状审计

修改前完整结论与调用证据见 [P0 审计](V06_AUDIT_ZH.md)。主要发现：

- 23 阶段、真实 sandbox/适配器、工件、检查点、数值注册表、人审及状态图已经存在；保留它们。
- Skill 是提示词工作方法，五轴/主张版本未进入统一运行门。汇总可混合模拟与失败，论文审核存在跳过路径，runner 有强制 PROCEED，不能由“阶段完成”推导科学成立。
- v0.1 状态有稳定 ID、支持/反对证据、supersedes 和 checkpoint，但不能防止静默覆盖主张，也没有真正的跨任务科学去重。
- 通用记忆可裁剪，自动经验记忆和若干遥测 hook 还有接线缺口；没有将它们伪称为长期权威证据。
- 状态测试依赖已删除私人示例，wheel 丢失 schema，样式重复 force-include 曾导致打包失败。
- 上游 Aiming Lab MIT 与项目 Apache-2.0 声明保留；vendored 外部代理的逐文件清权、旧 Git 敏感历史仍未完全审计。

## 2. 架构决策

| 模块 | 决策 | 实际原因 |
|---|---|---|
| 引擎、23 阶段、CLI/import、checkpoint | KEEP | 保留成熟链路，没有重写或改名大迁移 |
| Skill、checksum、VerifiedRegistry、论文 tokenizer | REUSE + MODIFY | 复用规则和组件，补统一执行覆盖，不靠提示词自证 |
| v0.1 状态 | KEEP | 旧档只读验证保持兼容，不自动改科学历史 |
| 主张版本/执行证据 | ADD sidecar | 小型本地 JSON 快照/工件，无新数据库或分布式服务 |
| Docker/远程/领域执行、Stage13 | HOLD runtime certification | 未验证的后端/子任务不冒充已覆盖；旧底层接口保留 |
| 大型外部集成/全新 UI/整体重写 | DEFER / KILL rewrite | 没有实测收益支撑，当前缺口可在现有栈内修正 |

## 3. 代码与兼容性

| 文件 | 变更 |
|---|---|
| `researchclaw/pipeline/evidence_gate.py` | 共享 preflight、真实收据、原始来源、有限值/样本/基线/规则、五轴及论文绑定审核 |
| `researchclaw/pipeline/executor.py` | 前后置接线，覆盖恢复/auto-approve/HITL SKIP；分析/归档保留未决证据伴随报告 |
| `autoresearch_state/evidence.py` | 主张版本不可覆盖快照，显式修订/父分支，排他写入决策与收据 |
| `researchclaw/cli.py` | 新增中文 `evidence RUN_DIR [--json] [--paper ...]`，原命令保留 |
| `scripts/evidence_smoke.py` | 真实受控 CPU 算术运行与独立目录复跑，无模型服务 |
| `experiments/arc_bench/evidence_comparison.py` | 固定三系统身份/任务/模型/预算的离线 freeze/dry-run/summarize |
| `autoresearch_state/validation.py`、`pyproject.toml` | wheel 内 schema 路由；删除冗余样式打包映射，样式仍完整 |
| `tests/fixtures/research_state_generic.yaml` 与原状态测试 | 全新虚构示例替换缺失私人研究示例，不恢复旧档 |
| 新 runtime/comparison/packaging 测试、README、中文文档 | 关键正负例、安装边界与实际使用说明 |
| `pyproject.toml`、`researchclaw/__init__.py` | 本地候选版本 0.6.0；不自动发布或打远程 tag |

原 `ranchoresearch`/`researchclaw` 入口仍映射同一 CLI；Python namespace 不变；
状态 schema 0.1.0 不变。新 gate 会有意阻止没有证据的真实执行/写稿，旧运行不能被
回填为“新门已观察”；迁移要求见 [运行说明](EVIDENCE_RUNTIME_ZH.md)。

## 4. 科研证据门禁

已经强制：

- 实际运行前绑定稳定 claim/version、冻结协议及实际选中输入，并核对模式和单次预算授权；HITL 编辑后重新核验。
- 成功、异常与资源失败均保存收据和原始输出。输入字节、输出快照、旧 Stage12 文件保留；复跑不覆盖旧证据。
- 科学指标/有效性/样本只从选定收据的实际测量输出读取。预写输入、旧 stage 输出、复制入 sandbox 的输入不能冒充新测量。
- 阻断 NaN/Inf、范围/索引/来源标签错配、样本不足、冻结检查失败、基线缺失、非法方向和判决字段。
- 校准通过仍 NOT_TESTED；异常/缺证据不会 KILL；有效负结果只保留冻结作用域内的 CONTRADICTED_IN_SCOPE。
- 论文的十进制数字需要精确位置、来源 Pointer 与哈希绑定；最终 Markdown/LaTeX及 Stage23 标注稿重新审核；来源缺失或非有限结果暂停交付。
- 原创性、执行、测量、科学状态、论文就绪分开；测试集已曝光或历史未知不能计独立确认。

仍是领域/人工审查：检索完整性、真实语义和因果识别、样本独立单位、统计区间构造、
任意代码是否伪造指标、审核者身份及文献碰撞的语义正确性。本地哈希不是身份签名，
有权重写整个 run_dir 的主体仍可伪造记录。原 subprocess sandbox 不是恶意代码隔离环境。
本轮没有验证 Docker/SSH/GPU/领域代理或 Stage13 内部优化循环，没有全项目累计费用硬配额。
图中文字、中文数词和所有 PDF/数学表达不在十进制 tokenizer 的完整覆盖内。

## 5. 本地验证与实际运行

环境：Windows，Python 3.13.9，隔离 venv 复用本机依赖并安装项目 dev extras。
未调用真实 LLM、付费裁判、GPU或远程科研执行。

| 检查 | 真实结果与证据 |
|---|---|
| 修改前全量基线 | 2846 passed / 45 failed / 57 skipped，18 subtests；`artifacts/verification/baseline.log` |
| 旧执行器/runner/HITL/fabrication/e2e 软件回归 | 281 passed；`artifacts/verification/legacy-targeted.log` |
| 最终重点回归 | 82 passed，18 subtests；`artifacts/verification/focused.log`、`focused.xml` |
| 最终全量回归 | 2954 passed / 2 failed / 57 skipped，18 subtests；186.06秒；`artifacts/verification/full.log`、`full.xml` |
| 重点回归构成 | runtime 41、对照21、状态13、安装3、公开边界4；这些是软件测试，不是科研基准 |
| 实际 CPU 执行及复跑 | 两次独立目录的 Stage12 子进程，固定16个合成整数；两次指标一致，`artifacts/final-controlled-cpu/smoke.json` |
| 原始资料保留的正负例验收 | 8类，6类无效/未决；误放0/6、误杀0/6；同时接纳阳性、保留有效有界阴性；`artifacts/acceptance-suite/summary.json` |
| 安装包 | wheel 构建与隔离解包后的版本、状态schema、CLI、证据恢复检查通过；10个样式资源、0重复成员；`artifacts/verification/wheel-verification.json` |
| 静态/入口 | `git diff --check`、两个 CLI help 通过；正确 Git Bash 的 sentinel 语法检查通过 |

上述 0/6 只对八类固定、已知标签的受控用例成立，不能估计真实科研误放/误杀率。
没有靠全部 HOLD 过关：有效阳性进入后续审查，有效负结果保持有作用域的否定证据。
工程复跑通过不产生新颖性或真实数据发现；科学价值保持 HOLD。

P3 所需十二类逐一有测试：完整真实执行、未执行漂亮报告、NaN/错位、简单基线解释增益、
有效负结果、资源失败、精确先例、部分重叠、仅校准、论文无来源数值、测试集曝光、
新反证版本修订。独立审查还实际复现并关闭了预写/复制结果误放、方向拼写误杀、
来源错配、Docker回退授权错配、最终稿遗漏等问题。

最终两个失败均为基线已有：`test_hitl_advanced.py::TestHookRegistry::test_shell_hooks`
在 Windows 直接执行 `.sh` 得 WinError193；`test_rc_sentinel.py::TestSentinelScript::test_sentinel_script_is_valid_bash`
使用当前系统 bash/Windows路径组合失败。额外用 Git Bash 对 sentinel 做语法检查通过，
但没有因此把原测试记为通过。保留失败与日志，不改测试制造全绿。
基线与最终全量的 dev extras 环境不同，45→2 不能解释为本轮补丁净修复了43个代码问题。

## 6. 外部组件与许可证

本轮新增运行时依赖为零。PaperQA2、GPT Researcher、AIDE、MLflow、LangGraph、Prefect
均未接入：先修正本地真实缺口，尚无最小对照证明这些组件能降低维护成本或改善结果。
后续若选用，需逐个核对同类现有能力、差异、许可、适配收益及退出路径。

八项参考系统/基准的一手来源、许可与运行条件见
[对照方案](../experiments/arc_bench/EVIDENCE_COMPARISON_ZH.md)。特别保留：
AI Scientist v2 当前自定义许可不能按 Apache-2.0 对待；AstaBench 数据接受条款及
资源条件未满足；ScienceAgentBench 应固定 verified 版本；ResearchClawBench 的
ResearchClaw 适配不能误认为 AutoResearchClaw。没有导入这些外部源码或下载受限数据。

## 7. 公平对照

真实三系统基准状态：**NOT_RUN**。实现了离线计划、未运行模板、计数/分母/UNKNOWN
及不可比检查，没有编造完成率、成本改善、独立复现率或胜过竞品的结论。
对照原版 AutoResearchClaw、升级前 RanchoResearch、升级后补丁，要求同模型参数、
任务、预算、种子和评判协议。公开题全部标探索性，不事后取优，失败不从分母删除。
建议从3个CPU任务×每系统2次开始；模型/数据/资源未就绪前保持 NOT_RUN。

## 8. 下一阶段三个优先问题

1. **可信评估器与真实小任务全链验收**：把测量语义、协议实现及数值产生过程交给独立、固定版本的评估器；对一个真实领域任务做干净环境复跑，先验证有效样本/控制而非追论文。
2. **逐子任务收据和隔离/预算覆盖**：扩展 Stage13、Docker 实际后端、远程及领域代理；核验实际资源成本与累计限额，修复失效遥测/记忆接线，不能只记录配置承诺。
3. **独立评测与发行边界**：在已授权模型/CPU预算下运行固定三系统对照，并完成第三方资产清权、Windows/Bash兼容及审核身份/历史修订检索验收；再决定是否发行。

## 9. 分轴最终判断

| 维度 | 状态 | 证据与限制 |
|---|---|---|
| ENGINEERING | MODIFY / bounded MVP | 原引擎回归、受控子进程、CLI及安装包验证；未验证所有后端，尚有平台测试问题 |
| EVIDENCE | MODIFY | 已有确定性前后置门和关键负例；仍不能自动证明测量语义、审核身份或任意程序诚实 |
| REPRODUCIBILITY | PARTIAL | 固定CPU合成任务跨目录、跨进程、安装布局恢复通过；真实科研独立复现率 UNKNOWN |
| SCIENTIFIC VALUE | HOLD | 无新的原创科学结果；算术阳性只是工程验收，基准未运行 |
| RELEASE READINESS | HOLD | 本地候选可审查；后端覆盖、平台测试、第三方权利和完整真实验收未完成 |

因此本轮建议继续最小修改，保留负证据与未决问题；**整体 MODIFY，发行 HOLD**。
没有因版本号、功能数量或测试通过自动给 GO。
