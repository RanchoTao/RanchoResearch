# Research Evidence Runtime Gate v0.6

这是对既有引擎的增量修改。方法来源仍是 canonical
`researchclaw/skills/builtin/experiment/research-evidence-gate/SKILL.md`，
运行控制统一在 `pipeline/evidence_gate.py`，经 `executor.execute_stage` 调用。
原有 VerifiedRegistry、论文 tokenizer、checksum、StageResult、CLI 和状态 v0.1 保留。
没有新增数据库、消息队列、模型调用或 Web UI。

## 已强制覆盖的入口

| 时点 | 实际检查 | 失败行为 |
|---|---|---|
| Stage12 真实执行前 | claim/version、冻结协议、实际选中代码/数据/配置哈希、执行模式及单次时间预算授权；HITL 编辑后重验 | PAUSED / HOLD，不运行实验 |
| Stage12 执行后 | 对真实 executor 保存成功/失败收据与原始字节快照，不能由 HITL SKIP 代替 | 失败资料与收据保留；收据不足不能晋级 |
| Stage14/21 分析与归档后 | 保存五轴证据审查伴随文件与决策记录 | 软件步骤可完成以保留负证据，不等于科学晋级 |
| Stage15–20、22–23 入口/出口 | 显式选择的同版本收据、实际运行状态、输入/输出哈希、来源标签、全部冻结检查、指标有限值/范围、有效样本、基线与判决规则 | PAUSED；`--auto-approve`、可选 PRM、注册表 ablation 和从中途恢复均不能替代此门 |
| Stage20/22/23 论文真实性 | 每一个可识别的十进制数字绑定精确位置及原始 JSON Pointer；无默认常数白名单；原文与绑定 SHA256 一致 | 不授予可信交付状态，保留草稿以修正 |
| 独立性与论文就绪 | 新颖性审查来源、审核者、中文范围解释、独立复核工件、测试集曝光历史 | 曝光/未知只作探索结果，不能冒充独立确认 |

真实 Stage13 优化内部可修改代码并调用远程模型，无法逐子任务冻结。v0.6.1 起它不再让
流水线卡在 PAUSED：未授权时直接跳过（写 `stage-13/exploration_skipped.json`，状态 DONE）；
`authorization.allow_exploration: true` 时作为**探索**运行，记录写入 `evidence/explorations/`，
永远不被当作科学证据。要采用优化后的代码，用 `--seal --new-version` 冻结新版本后重跑 Stage12。Docker factory 原有自动回退本机路径未被本轮重构，故新门
也对 Docker/SSH/Colab/领域 Agent 保持 HOLD。原始 Python 组件和兼容 import
仍可使用，但直接调用私有 stage 函数/底层 sandbox 绕过的是统一控制器，不能把这种
执行称为 v0.6 门禁认证。模拟 Stage12 仍可用于软件演示，不能获得真实收据或科学晋级。

## 本地最小运行与恢复

```text
python scripts/evidence_smoke.py --output artifacts/evidence-smoke
ranchoresearch evidence artifacts/evidence-smoke/first
ranchoresearch evidence artifacts/evidence-smoke/first --json
ranchoresearch evidence RUN_DIR --paper relative/paper.md
```

Windows 可使用 `python -X utf8` 保持重定向报告的中文编码。所有输出目录必须是新目录；
真实输出位于忽略的 `artifacts/`，不要加入公共仓库。smoke 使用现有 Stage12
及实际子进程，明确 SYNTHETIC 固定算术对象，无模型服务和 GPU。
研究价值是验证工程证据链，而非发现新科学。两个独立工作目录获得一致确定性结果
只证明这个受控任务可复跑，不证明领域科研普遍可复现。

每个 run 的 `research_evidence.json` 是显式请求，字段包括：

- `schema_version: "0.6.0"`。
- `claim`：稳定 `claim_id`（claim_ 前缀）、正整数 `claim_version`、definition、scope、research_value、known_work、falsification、protocol 的相对 path/SHA256。版本>1 还须 `revision_reason`；可选 parent 指向已存在的另一主张版本。
- `inputs`：code、data、configuration 的非空工件列表；`data_origin` 为 REAL/SYNTHETIC/NOT_APPLICABLE。不适用的数据也提供解释工件，不能用空字段模糊处理。
- `authorization`：actor、reason、allowed_modes、max_time_budget_sec。它是本地执行授权记录，不能替代外部账户授权、费用授权、操作系统隔离或审批身份认证。
- `provenance`：model、parameters、seed、api_cost、gpu_cost。未填写的值报告 NOT_RECORDED；明确不适用时用 `NOT_APPLICABLE: 理由`。申请额度绝不作为实际消耗。
- `receipt`：本次明确选用的 `evidence/receipts/*.json` 相对路径。执行结果的 evidence_refs 返回此路径；调用者需显式选用，禁止自动选指标最优的历史尝试。
- `review`：novelty 标签、reviewer、explanation_zh、source 工件；EXACT_COLLISION 还需 collision_scope。独立复核 PASSED 必须附 independent_source。未核验填 UNKNOWN。
- `test_exposure`：EXPOSED/UNEXPOSED/UNKNOWN/NOT_APPLICABLE；NOT_APPLICABLE 的领域理由应写入审核工件。
- `papers`：各论文的相对 path/SHA256 与 bindings。

完整可执行样例由 `scripts/evidence_smoke.py:prepare_run` 创建；不是把真实研究档案复制进测试。

冻结协议 JSON 包括主张身份、science/calibration 目的、execution_config、measurement_method、
data_contract、origin_source、checks、metrics、sample_count、正整数 min_samples、baselines 和 decision_rule。
checks 的每一项明确 name/path/pointer/op/expected，支持严格类型 eq、有限数 ge/le；
metrics 明确 path/pointer，可带 min/max。所有科学字段只接受本轮实际输出，不能从
预写的输入/漂亮报告读取；数据来源标签必须与冻结输入一致。
拷贝进 sandbox 的冻结输入也不能因路径位于输出目录就获得测量资格；
与任一冻结输入字节完全相同的工件保守地排除出科学测量来源。

`finite_computation` 规则仅接受 `fixed_finite_population`、严格 minimize/maximize、
明确候选与已声明简单基线指标、正的 min_effect；用实际配对增量判定固定范围。
`interval` 规则需上下界来源与 contrast_definition，按冻结的增量区间判定；
区间构造、统计假设、独立样本单位及测量语义仍需领域审查，代码不会证明它们正确。
理论证明/未支持的协议类型保持 HOLD，不伪装为通用科学裁判。

每个判决输出五轴及中文解释。测量错误、资源失败或缺证据不会产生科学 KILL。
有效负结果保留 CONTRADICTED_IN_SCOPE，并用 KILL 表示仅此版本/作用域的停止建议。
校准通过仍是 NOT_TESTED。无基线不能用总收益宣称新机制。
有效科学判决可进入后续审查，不等于原创性成立或论文可交付。

## 工件、版本与论文绑定

`evidence/claims/claim_ID/vN.json` 首次排他写入，同版本内容改变会拒绝。
新版本必须保留上一版及修改/撤销理由；parent 可形成不同主张分支。
`evidence/decisions` 保存每次门禁结果；`receipts` 保存每次实际执行（包括失败）。
`blobs` 保存输入字节；`attempts/随机ID` 保存原始输出字节。重跑前把旧 Stage12
目录移到 `unbound_prior` 保存，不给预写/旧输出盖本次真实运行章，也不删除资料。
收据记录代码提交、实际代码/数据/config/protocol 指纹、环境、起止时间、实测墙钟、
授权和输出映射。API/GPU 账单没有观测时为 NOT_RECORDED，不能填零或推算。
长期权威证据是这些工件与主张快照；可能裁剪的通用检索 MemoryStore 不是权威账本。

论文绑定格式示意：

```json
{"path":"paper.md","sha256":"实际文件哈希","bindings":[
  {"start":12,"token":"16","source":{"path":"stage-12/runs/result.json","pointer":"/n"}}
]}
```

start 是 Python 字符索引，token 必须与该位置的 tokenizer 匹配结果一致。
source 可指原始输出；方法参数/年份等非实验数字可指冻结输入 JSON 字段，不能靠常数白名单。
scale/decimals 显式定义转换及舍入，转换后必须精确匹配；所有匹配位置须恰好绑定一次。
生成/修改论文后需要重新建立绑定，Stage22 新生成的最终稿/LaTeX 和 Stage23 标注稿也重新核验。
拒绝 NaN/Inf/Infinity。文献里的数字需要本地可追溯来源工件；不能将引文数字偷称本次实验。

这是保守的数字真实性检查，会要求为常见数字补来源。ASCII 十进制 tokenizer
不覆盖中文数词、图片内文字及所有数学表达；数值同源也不能证明句子的机制归因正确。
人工仍需检查上下文、图表和语义。本轮没有可信 PDF 数字/图像 OCR 全覆盖。

## 兼容与迁移

保留 ranchoresearch/researchclaw 两 CLI 及 Python namespace；状态 v0.1/schema 不改写。
旧档可继续只读 validate/status/graph，不自动赋五轴或换结论。新证据为 additive sidecar，
需要新冻结版本及真实执行收据；不能把旧摘要回填成新门已观察到的实验。
原有 checkpoint 可恢复阶段，入口重新审核该主张版本；历史失败/撤销记录不消失。
新增 schema 的包内资源仅为安装布局修复，权威源仍是原 schemas 文件。

## 仍需人审或未覆盖

哈希保证比对字节，不能证明科学测量逻辑正确；本地 reviewer/independent 标注不具签名认证。
有权改写整个 run_dir 的主体能够伪造本地记录。冻结协议由人/代理编写，若其遗漏关键混杂、
生成代码仅打印伪指标、数据来源声明不诚实，本门不能自动理解并证伪；需可信评估器和独立重跑。
本机 sandbox 为原有子进程执行，不是恶意代码隔离边界，继承环境和网络能力；
新增 gate 不应被解释为容器/网络防火墙或通用安全审计。
当前授权仅限制记录中的模式和单次配置时间，并非全项目累计 CPU/API 花费硬配额。
新颖性完整检索、因果识别、样本独立性、区间算法、真实性语义、外部发布审批均未自动证明。
所有这些限制保持 UNKNOWN/HOLD，不以测试通过升级为科学 GO。


## v0.6.1 工作流补充

修复前，真实（非 simulated）模式的流水线必定停在 Stage13，看起来像"一直 HOLD"，实际是死路。现在：

```text
ranchoresearch evidence RUN_DIR --init                 # 写入证据包/协议模板（不覆盖）
# 填写全部 TODO：主张、协议、指标指针、授权人；inputs.code 保持 "auto"
ranchoresearch evidence RUN_DIR --seal                 # 自动计算哈希，绑定引擎实际选中的实验代码
ranchoresearch run ... --from-stage EXPERIMENT_RUN     # 执行并继续 13→14→15…
ranchoresearch evidence RUN_DIR --seal --new-version "原因"   # 改了代码/协议时新建版本
ranchoresearch evidence RUN_DIR --select-receipt evidence/receipts/X.json  # 多个收据时显式选择
```

- 某主张版本**只有一个**执行收据时自动选用（没有可挑选的空间）；多个时仍须显式选择。
- 原创性审核者 `review.reviewer` 与独立复核者 `review.independent_reviewer` 都不能与
  `authorization.actor` 相同；独立复核 PASSED 必须写明 independent_reviewer。这是标签比对，
  不是签名：它挡住"同一 Agent 自审"，不能防止有意伪造身份。多 Agent 自动化时，
  建议执行、查新、复现、审稿使用不同身份（不同模型/进程）。
- 运行遥测：`events.jsonl`（阶段事件）、`cost_summary.json`（token 用量；仅在设置
  `RANCHO_PRICE_INPUT_PER_MTOK`/`RANCHO_PRICE_OUTPUT_PER_MTOK` 时计算美元，否则为 UNKNOWN，
  美元预算无法强制）。ExperimentMemory 现在写入 `config.memory.store_dir`，仅记录 Stage12
  实际写出的有限指标，属于启发式记忆而非证据；**召回注入到提示词尚未接线**。
- 删除了 runner 中引用不存在模块（experiment_spec、pitfall_detector）的死代码，它们此前从未运行。

## v0.6.2 由 Agent 起草主张与协议（Stage11→12）

在配置中设置 `experiment.protocol_author`：

| 取值 | 行为 |
|---|---|
| `manual`（默认） | 与 v0.6.1 相同，人工 `--init` / `--seal` |
| `agent` | 起草 LLM 写主张与协议 → 静态检查 → 审核 LLM 按 7 项清单审核 → 通过则自动封存并执行；否则暂停 |
| `agent_with_human_review` | 起草 LLM 写草稿 → 静态检查 → 暂停，等人审 |

```text
ranchoresearch evidence RUN_DIR --approve-draft -c config.yaml --actor 你的名字
# 也可指定草稿目录：--approve-draft evidence/drafts/<时间戳>
```

- 草稿和审核意见保存在 `evidence/drafts/<时间戳>/`（draft.json、meta.json），被拒的草稿也保留。
- **LLM 只决定科学内容**（主张、候选/基线条件、指标、方向、最小效应、样本数），
  指标 JSON 指针由程序按固定约定生成：`/metrics/<条件>/<指标>`、`/data_origin`、
  `/n_samples`、`/valid`。为此，sandbox 模式下 Stage10 代码生成会附加"证据输出约定"，
  要求 results.json 含这四个顶层字段。
- 静态检查会拦截以下草稿：条件名或指标名在代码中找不到、方向非法、最小效应 ≤ 0、
  候选与基线相同，以及代码不符合输出约定。**约定之前生成的旧课题需要重新生成 Stage10 才能用 agent 模式**；
  否则只能走 manual。
- `protocol_reviewer_model` 用于为审核方指定不同模型。留空时审核方与起草方同一模型，
  `authorization.actor` 会标为 `protocol-reviewer(same-model):…`，独立性较弱，可在记录中看出。
- 已存在的证据包不会被覆盖；改协议仍需 `--seal --new-version`。
- 自动审核只检查主张是否可证伪、是否有基线稻草人等逻辑问题，**不等于科学 GO**；
  Stage15 以后的五轴裁决与独立复核规则不变。
