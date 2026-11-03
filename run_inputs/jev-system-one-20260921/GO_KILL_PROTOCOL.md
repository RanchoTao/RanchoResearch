# First-Round GO / PIVOT / KILL Protocol

## Objective

Run a **pre-experiment research selection round** over the Jev/System-One hypothesis pool. The goal is not to prove Jev is good. The goal is to identify at most **three** CCF-A-caliber scientific arcs with the cleanest falsifiers and lowest collision risk.

Final output must be exactly one project-level recommendation:

- **GO** — at least one arc has a defensible gap and a decisive minimal experiment;
- **PIVOT** — the area is promising but all current arcs collide, depend on inaccessible evidence, or need reframing;
- **KILL** — no sufficiently novel/testable arc remains after hostile audit.

Individual hypotheses should also receive GO / PIVOT / KILL.

## Stage A — Freeze the object

Record:
- snapshot date;
- current Jev model name/version from public docs and any returned API metadata;
- pricing and documented limits, explicitly marked time-sensitive;
- what is known vs unknown about architecture/RLCD/training;
- exact public benchmark/repo versions used for collision checking.

Do not infer hidden architecture from open replicas.

## Stage B — Search and collision audit

Search at minimum:

### Keywords
- typed decision model
- probabilistic decision model
- calibrated classifier language model
- selective prediction language model
- reject option / abstention
- conformal risk control
- LLM confidence calibration
- verbalized probabilities
- multiple-choice position bias
- LLM-as-a-judge calibration
- reward model benchmark
- LLM routing / model router
- adaptive model cascade
- query routing cost quality
- multi-question batching language model
- non-autoregressive classification LLM
- prefill classification / label token logits
- structured output LLM
- context distractor robustness
- compositional calibration / correlated classifier errors

### Sources
- OpenAlex
- arXiv
- ICLR / ICML / NeurIPS proceedings
- ACL Anthology
- PMLR
- GitHub for Jev/System-One/open replicas and benchmark artifacts

### Mandatory nearest-neighbor check
For each surviving hypothesis identify 3-5 nearest papers/repos and answer:
1. Did they already ask the same question?
2. Did they use the same mechanism?
3. Did they evaluate the same property?
4. Is the remaining gap scientific or merely Jev-specific?
5. Would a skeptical reviewer call this "benchmarking a new API"?

If the answer to #5 is yes, PIVOT or KILL.

## Stage C — Rank hypotheses by scientific shape

Use qualitative reasoning, not a fake numerical leaderboard. Prefer hypotheses that:

- isolate a property of typed probabilistic decision models;
- can produce an informative negative result;
- have open baselines and public data;
- require little proprietary access;
- survive model-version churn;
- connect to calibration, selective prediction, routing, robustness, or systems theory.

Do not select more than three arcs.

## Stage D — Build one decisive pilot per surviving arc

Each pilot must specify:

- exact scientific question;
- exact hypothesis and null;
- dataset + pinned revision;
- target model version;
- minimum 3 baselines;
- transformations/perturbations;
- primary metric;
- secondary metrics;
- paired statistical test / CI;
- success condition;
- kill condition;
- estimated API cost;
- estimated GPU/CPU requirement;
- saved artifacts;
- main confounds.

No pilot may use a custom composite score as its primary endpoint.

## Stage E — Hostile reviewer test

For every finalist, write the five strongest rejection arguments, including:

- "This is just a benchmark of a proprietary API."
- "The claimed novelty is already selective prediction/routing/calibration."
- "The open baseline explains the result without a new model class."
- "The benchmark is contaminated or easy."
- "The result will disappear when Jev version changes."
- "The latency comparison is provider/network specific."
- "The probability semantics are not comparable across models."

Specify the evidence needed to neutralize each objection.

## Stage F — Final verdict

A project-level **GO** requires all of:

1. one narrow claim that does not depend on TypeSafe marketing terminology;
2. verified nearest-neighbor gap;
3. one minimal experiment whose negative result is still informative;
4. at least three fair baselines;
5. a version-robust conclusion;
6. plausible extension to 3+ domains;
7. no need to know hidden architecture/RLCD internals;
8. first pilot feasible in hours and under a small API budget.

Otherwise PIVOT or KILL.

## Candidate arcs to test first

Do not assume these survive audit.

### Arc A — Invariance and interference of typed decision primitives
Combine H02/H03/H05/H06.

Possible thesis:
> Bounded probabilistic decision APIs expose measurable invariance and interference properties that differ systematically from autoregressive structured-output LLMs.

Decisive pilot:
- Banking77 + JevBench public subset;
- option permutation + irrelevant-question batching;
- Jev / system-one-adapter LLM / openjev-sglang / DeBERTa typed-decisions;
- flip rate + probability JS distance + calibration.

### Arc B — Calibrated selective System-One/System-Two cascade
Combine H09/H11/H13.

Possible thesis:
> Native bounded-decision probabilities enable higher coverage at fixed risk and a better total cost-quality frontier for adaptive escalation.

Decisive pilot:
- Banking77/CLINC OOS plus one RouterBench slice;
- risk-coverage + total cost;
- raw confidence, post-hoc calibration, conformal wrapper;
- fair LLM/router baselines.

### Arc C — Probability composition in structured workflows
Combine H12/H15.

Possible thesis:
> Node-level calibration is insufficient for reliable workflow-level decisions because judgment errors are dependent; explicit dependence correction improves final calibration.

Decisive pilot:
- construct one public, gold-labelled multi-node workflow;
- measure node and final-action calibration;
- compare naive independent composition vs learned/empirical correction;
- repeat with Jev and at least one non-Jev decision model.

### Arc D — What part of "System One" is actually new?
Combine H01/H18/H19.

Possible thesis:
> The performance envelope of typed decision systems decomposes into non-autoregressive sampling, zero-shot semantic capability, and calibration; open counterfactuals can identify which factor creates each gain.

Decisive pilot:
- same schemas across Jev, prefill Qwen, encoder decision model, structured generation;
- sweep K and number of questions;
- decompose accuracy/calibration/latency.

## Stop rule

This first round **must not** launch a large benchmark, train a new model, or spend significant API/GPU budget.

Stop after:
- literature map;
- public-resource map;
- collision audit;
- 20-hypothesis triage;
- 2-3 finalist arcs;
- one minimal pilot per finalist;
- hostile reviewer simulation;
- project-level GO/PIVOT/KILL.

Human approval is required before live experiments.
