---
name: research-evidence-gate
description: Review scientific contribution, novelty, experiment validity, baselines, evidence-backed GO/HOLD/KILL decisions, and the preflight of multi-topic research launches in RanchoResearch. Use before launching studies and when interpreting or closing results.
---

# RanchoResearch 科研证据与贡献审查

本仓库的正式、可复用审查流程位于：

researchclaw/skills/builtin/experiment/research-evidence-gate/SKILL.md

**开始选题筛选、实验设计、批量启动、论文贡献裁决或研究终止审查时，先读取该文件全文并执行对应步骤。** 这是同一套规则的 Codex 仓库入口，不应另建一个有冲突的版本。

最重要的五条规则：

1. 预想实验阳性时，也要证明相对最近邻文献存在科学信息增量，而不只是新的实验组合。
2. 数据、测量、冻结规则与实际执行代码不一致时，先判 INVALID/UNKNOWN，不能把工程或测量失败称为科学证伪。
3. 比较最简单的合理基线及真正增量，避免由强总体收益推断不存在的复杂机制。
4. 科学状态、测量有效性、原创性、执行资源和论文就绪分成五轴；所有判决绑定主张版本、范围及底层证据。
5. 全线启动须先逐题做低成本预检，按授权与资源上限安排计算；Skill 的存在不等于调度器已强制执行，也不自动授权公开发表。

若正式 Skill 不可读取，停止把本次审查宣称为“已通过 Skill 校验”，明确报告缺失；不要自行编造同等审查已完成。原始研究档案和未发表实验不得复制进公共软件仓库。
