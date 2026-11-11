# v0.6 最小证据对照方案

当前科研基准状态：**NOT_RUN**。本文件与 `evidence_comparison.py` 交付可执行的离线计划校验、空记录模板和统计器。单元测试使用合成审核记录，只能证明统计与拒绝规则的软件行为；没有证明 RanchoResearch 的科研效果优于任何竞品。

## 复用边界与公平性

保留现有 `config/*/manifests`、`config/*/rubrics`、`scripts/run_baseline.py`、`scripts/run_bench.py`。新增工具只读这些输入，不加载凭据、配置中的发布开关或模型客户端，不调用 runner，不启动子进程、网络、GPU 或付费 API；`freeze`、`dry-run`、`summarize` 都只有本地文件操作。

旧 `scripts/evaluate.py` 使用 `manifests/T*.yaml`，与当前输入目录不一致；缺少 `overall_score` 时默认零，并提供基于结果事后选择的 `rc_copilot_guarded`。本工具不使用该聚合路径或其取优分数，也不改变旧 API。新增模块解决的具体问题是计划和记录的可比较性，未替代科学证据运行门禁。

必须固定三个系统：

| system_id | 版本身份 |
|---|---|
| `autoresearchclaw` | aiming-lab/AutoResearchClaw 的实际完整提交与可选补丁 SHA256 |
| `rancho_baseline` | RanchoTao/RanchoResearch 升级前实际提交与可选补丁 SHA256 |
| `rancho_upgraded` | 升级后实际提交，或基线提交加本轮完整补丁 SHA256 |

完整补丁应包含测试时全部运行相关改动，包括未跟踪的新模块；仅 `git diff` 不含未跟踪文件，不能单独用它冒充完整工作树身份。工具验证指纹格式和绑定，**不证明远程提交或补丁内容真实存在**；执行前由审查者核对源树、依赖和实际环境。干净提交的 `patch_sha256` 明确为 `null`。基线与升级版身份相同会被拒绝，不接受短提交或零占位值。

共享模型身份包括 provider、model_id、settings；所有阶段须使用冻结设置，包括裁判、feedback、embedding 等额外调用的预算。当前协议采用独立人工审核，若改用 LLM 裁判须定义新的协议版本及独立费用，不能悄悄替换。共享预算包括每运行墙钟、API 调用次数、输出 token、美元成本、GPU 秒数和内存上限；本最小方案 GPU 秒为零。声明预算不会强制现有 runner 限流：实际运行仍需由被审查的执行器落实权限、预算和停止条件。统计器会标记耗时、API 次数、输出 token、成本、GPU 用量缺失或超限；内存仅为计划约束，当前尚无峰值内存收据检查。

建议先固定三个 CPU 任务、每系统两次独立运行（共 18 单元），顺序执行；优先使用依赖已安装、数据可获得的任务。若 manifest 要求五种子或更多独立单位，代理内的实验应满足该要求，不能把“两个代理运行”当成科学样本数。统计器支持更小 smoke 输入，但不自动删减 manifest 条件。所有公开题均标记 `EXPLORATORY_PUBLIC_TASKS`，不得把已见题重新称为独立科学确认。

## 本地操作

首先创建 `comparison-settings.json`，以下为**待填写配置**，提交占位符会被工具拒绝；它不是已冻结的成功实验：

```json
{
  "systems": {
    "autoresearchclaw": {"repository":"https://github.com/aiming-lab/AutoResearchClaw","commit":"REPLACE_WITH_ACTUAL_40_HEX_COMMIT","patch_sha256":null},
    "rancho_baseline": {"repository":"https://github.com/RanchoTao/RanchoResearch","commit":"REPLACE_WITH_ACTUAL_BASELINE_COMMIT","patch_sha256":null},
    "rancho_upgraded": {"repository":"https://github.com/RanchoTao/RanchoResearch","commit":"REPLACE_WITH_ACTUAL_BASELINE_COMMIT","patch_sha256":"REPLACE_WITH_COMPLETE_PATCH_SHA256"}
  },
  "model": {"provider":"REPLACE_WITH_PROVIDER","model_id":"REPLACE_WITH_ACTUAL_MODEL","settings":{"temperature":0}},
  "budget": {"wall_time_sec":600,"max_api_calls":10,"max_output_tokens":20000,"max_cost_usd":0,"max_gpu_seconds":0,"max_memory_mb":4096},
  "task_ids": ["ML01"],
  "seeds": [0,1]
}
```

`max_cost_usd: 0` 表示未授权产生费用，不代表实际费用为零；没有免费可用模型时保持 NOT_RUN。示例预算未保证足以完成 ML01，不得据预算耗尽否定其科学主张。实际运行前应冻结适合任务的协议并取得需要的计算授权。

在仓库根目录执行：

```text
python experiments/arc_bench/evidence_comparison.py freeze --settings comparison-settings.json --output comparison-plan.json
python experiments/arc_bench/evidence_comparison.py dry-run --plan comparison-plan.json --output comparison-not-run.json
python experiments/arc_bench/evidence_comparison.py summarize --plan comparison-plan.json --records comparison-not-run.json --output comparison-summary.json
```

这些命令只会生成本地 JSON。输出文件必须不存在，避免静默覆盖冻结计划或收据。计划 SHA256 绑定三系统、共享模型/参数、预算、任务 manifest/rubric 哈希、种子、评分协议与指标定义。后续修改任何内容，或输入文件发生变化，都需要新计划，不能沿用旧记录。

获准并完成真实执行后，在**新文件**填写逐运行 JSON 数组；保留空模板。每条记录包括 `system_id/task_id/seed`、计划与系统哈希、`status`、`actual_model`、`audit_refs`、`observations`。审核工件引用格式为 `{"path":"relative/path.json","sha256":"实际64位sha256"}`，路径相对于仓库根或 `summarize --evidence-root` 指定目录。引用内容与哈希必须匹配，目录外路径被拒绝。原始工件、解释和复现材料都留在本地，避免把私人数据、凭据或实验输出加入公共仓库。

`observations` 的每个字段必须为明确实测值或 `null`；缺字段会拒绝。布尔字段只接受 bool/null；计数只接受非负整数/null；测量只接受非负有限数/null，NaN/Inf 被拒绝。未运行记录不可填入实测值；未完成运行不能宣称任务、证据或独立复现成功。审核引用可为空以保留失败资料，但已尝试运行缺少审核来源时总体标记 `INCOMPARABLE`。哈希只验证工件未改变，不能验证审核者诚实、原始实验真实性或科学结论正确；这些仍需核心门禁与独立人工审查。

## 指标与 UNKNOWN

输出保留每个系统 `planned_n/recorded_n/status_counts`、全部逐运行记录、指标分子/分母/未知数量及不可比原因。不挑选“最新一次”或表现最好的一次；重复单元被拒绝。缺运行会补为 NOT_RUN，不能从计划分母消失。资源故障属于 BLOCKED/FAILED，科学真假仍交由五轴状态解释。

| 指标 | 冻结定义 |
|---|---|
| completion_rate | 有效任务完成数 / 全部计划运行数；资源失败计未完成，未运行或未审核则总体 UNKNOWN |
| false_promotion_rate | false_promotions / audited_promotions；审核覆盖不足必须保留 null，不能把未审核项填零 |
| false_rejection_rate | false_rejections / audited_unresolved_claims；衡量把未决主张误判否定的误杀 |
| invalid_detection_rate | invalid_detected / invalid_results；真实标注无效结果为分母 |
| evidence_completeness_rate | evidence_complete / 已完成运行数；任何未运行单元保留 UNKNOWN |
| independent_reproduction_rate | 独立复现成功数 / 全部计划运行数；预选全部单元，资源失败也留在分母 |
| negative_retention_rate | negative_preserved / valid_negative_results；必须是有效且有作用域的负结果 |
| mean_cost_usd 等 | 实际总量 / 全部已尝试运行数，包含失败运行；任一缺失则该均值 UNKNOWN |

`wall_time_sec/cpu_seconds/gpu_seconds/api_calls/output_tokens` 分别报告均值，成本不把申请额度当消耗。`human_review_minutes/human_interventions` 记录人工审核负担，不推算未计时的劳动。无适用负结果或无被晋级主张时率为 `NOT_APPLICABLE`，不报 0% 或 100%。缺失值导致 `value: null`；`sum_recorded` 只是已记录小计，不是完整总成本。资源失败的完成率下降不等于科学 KILL。源记录只是声明，不会自动晋级可信科学状态。

全未运行输出 `NOT_RUN`，不产生性能结果。记录不完整、模型或预算不一致、来源缺失时输出 `INCOMPARABLE`。全部检查通过也只输出 `DESCRIPTIVE_ONLY`：小样本、公开题和自报审核记录不能支持广泛优越性。工具没有显著性或置信区间推断；真实评测报告还需逐任务不确定性、失败类型和审核覆盖率，不可仅报平均数。

## 外部项目核验与选择

以下为 2026-11-01 查询的一手公开页面，未运行这些系统。集成前应固定具体提交并复核许可证漂移；软件许可不自动覆盖所有科学数据、模型或依赖。

| 对象 | 来源、执行条件与决定 |
|---|---|
| AutoResearchClaw | [Aiming Lab MIT 许可](https://github.com/aiming-lab/AutoResearchClaw/blob/main/LICENSE)、[官方项目](https://github.com/aiming-lab/AutoResearchClaw)。保留上游核心与版权，固定原版做对照，官方自报成绩不当本轮成绩。 |
| InternAgent 1.5 | [Apache-2.0](https://github.com/InternScience/InternAgent/blob/main/LICENSE)、[README](https://github.com/InternScience/InternAgent)。Python 3.11，模型与 memory/embedding 凭据，任务环境不一；AutoDebug 是 setup toy。暂缓整套接入，后续独立适配。 |
| AI Scientist v2 | [当前 LICENSE](https://github.com/SakanaAI/AI-Scientist-v2/blob/main/LICENSE) 为 2025-12 自定义 The AI Scientist Source Code License，含用途和论文/报告 AI 披露限制；不能称 Apache-2.0。[README](https://github.com/SakanaAI/AI-Scientist-v2) 面向 Linux/NVIDIA CUDA/PyTorch。暂缓源码集成，独立评测也需固定版本、隔离执行及许可核对。 |
| AIDE ML | [官方项目](https://github.com/WecoAI/aideml) 标 MIT；[README](https://github.com/WecoAI/aideml/blob/main/README.md) 支持代码/feedback 模型配置和本地接口，但所有阶段都要固定。仅考虑以后局部优化适配，不以优化分数等同科学新颖性。 |
| ARC-Bench | [官方数据卡](https://huggingface.co/datasets/AIMING-Lab-UNC/ARC-Bench/blob/main/README.md) 标 MIT、55 题/五领域；ML/量子/统计开放问题、物理图复现、生物约束建模，rubric 不等价。优先复用本地输入，逐题检查数据和依赖。 |
| ResearchClawBench | [MIT](https://github.com/InternScience/ResearchClawBench/blob/main/LICENSE)、[官方项目](https://github.com/InternScience/ResearchClawBench)：40 基础任务/10 学科，LLM 多模态评分需裁判凭据。其 ResearchClaw 适配指 ymx10086/ResearchClaw，不能推断对 AutoResearchClaw/RanchoResearch 已兼容。暂缓外部基准执行，先核查原始数据许可。 |
| ScienceAgentBench | [README](https://github.com/OSU-NLP-Group/ScienceAgentBench) 于 2026-04-30 发布 verified split/benchmark_verified.zip 修正误杀；102 任务。代码 MIT、多数任务 CC-BY-4.0、部分保留原许可；禁止在线重发解压数据。Docker 推荐，图像评分可能调用 GPT-4o。后续必须固定 verified 版。 |
| AstaBench | [框架 Apache-2.0](https://github.com/allenai/asta-bench/blob/main/LICENSE)、[README](https://github.com/allenai/asta-bench/blob/main/README.md)：基于 InspectAI，2,400+ 样例/11 基准；数据 gated 需接受许可和 HF_TOKEN，评分/检索另需凭据，部分 coding 任务 20–30GB RAM。暂缓全套接入；arithmetic_demo 不算科研成功。 |

本轮没有引入第三方源码或新增依赖，没有重写引擎，没有发布结果或提交排行榜。MLflow、LangGraph、Prefect 等大型运行依赖不解决已确认的离线比较缺口，因此本模块不引入它们。若后续考虑外部组件，须另做与现有实现的局部对照、许可证核验和可退出适配。

## 验收

```text
python -m pytest tests/test_evidence_comparison.py -q
```

覆盖计划/输入防篡改、三系统身份、共享预算、未运行模板不执行外部工作、缺指标 UNKNOWN、资源失败分母、重复记录、非有限数、实际模型偏差、费用/API 超限、审核文件变更、无适用事件。通过这些测试说明离线框架可用；科研表现、真实成本、独立复现率和竞品提升均仍 UNKNOWN。
