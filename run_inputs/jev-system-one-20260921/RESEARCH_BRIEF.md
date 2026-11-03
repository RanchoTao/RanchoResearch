# Jev / System-One Research Selection Run

## Purpose

This is a new pre-experiment AutoResearch run for deciding whether a CCF-A-caliber project exists around TypeSafe Jev and the broader idea of **typed probabilistic System-One decision models**.

Optimize for discovering whether a defensible scientific project exists, not for proving Jev is impressive.

The project-level final recommendation must be exactly **GO**, **PIVOT**, or **KILL**.

Companion frozen inputs in this directory are authoritative starting context:

- `RESEARCH_MAP.md`
- `HYPOTHESES.md`
- `COLLISION_MATRIX.md`
- `GO_KILL_PROTOCOL.md`

Read all four before Stage 1 synthesis.

## Core framing

Do **not** frame the project as "benchmark Jev".

The object of study is the typed probabilistic decision primitive:

> state + bounded typed questions -> probabilities / confidence -> programmatic action

Ask whether this interface/model class has general measurable properties that differ from:

- autoregressive LLMs with structured output;
- token-logprob / prefill-only decision wrappers;
- encoder/discriminative classifiers;
- reward/judge models;
- learned LLM routers;
- deterministic retrieval/rule systems.

A paper-quality result should survive removal of the brand name "Jev".

## Evidence discipline

Use five labels consistently:

- **CONFIRMED** — primary paper, official API behavior, or independently reproduced evidence with artifacts.
- **VENDOR CLAIM** — TypeSafe-authored benchmark/performance claim.
- **COMMUNITY RESULT** — third-party result with public protocol/artifacts.
- **INFERENCE** — reasoning from evidence, not directly observed.
- **UNKNOWN** — not public or not verified.

Critical unknowns include Jev architecture details, RLCD implementation/objective, training data composition, and contamination controls. Do not invent them.

Do not treat open Jev-like replicas as evidence of Jev internals.

## Phase 1 — Freeze current public state

Create a dated snapshot of:

1. official TypeSafe docs and `llms.txt`;
2. launch post and workflow eval methodology;
3. Jev 1.13 jaggedness;
4. official System One Adapter;
5. major independent benchmark repositories;
6. open Jev-shaped implementations;
7. ecosystem indexes only as discovery sources.

Verify all time-sensitive claims. Prefer exact model/version, date, commit/revision and raw artifacts.

## Phase 2 — Literature map

Build a 20-40 item literature map across:

- calibration;
- selective prediction / reject option;
- conformal risk control;
- LLM uncertainty and verbalized confidence;
- multiple-choice / option-position robustness;
- LLM-as-a-judge and reward models;
- LLM routing and model cascades;
- RouterBench / LLMRouterBench;
- non-autoregressive / prefill-only classification;
- structured output;
- context distraction/robustness;
- probability composition / dependent errors.

Prioritize peer-reviewed ICLR, ICML, NeurIPS, ACL/EMNLP/NAACL and PMLR work plus indispensable arXiv papers.

For the final three candidate arcs, identify the five closest prior works each and state exact collision risk.

## Phase 3 — Public project / benchmark map

At minimum audit:

- TypeSafe workflow evals;
- fstandhartinger/jevbench;
- AbdelStark/jev-benchmarks;
- anessbelbati/jev-rerank-bench;
- Gaurav-Gosain/jev-sec-bench;
- TokenTrim/jev-agent-failure-benchmark;
- wondertwins/jev-benchmark;
- ekzhang/openjev-sglang;
- com-kotobalabs/open-jev-deberta-v3-large / kotoba-lang/typed-decisions;
- TypeSafe system-one-adapter-python;
- RouterBench;
- LLMRouterBench;
- RewardBench / RewardBench 2.

For each, extract:
- task;
- dataset;
- model versions;
- interface constraints;
- metrics;
- raw-artifact availability;
- strongest result;
- caveats;
- which hypotheses it kills or threatens.

## Phase 4 — Triage the 20 frozen hypotheses

Use `HYPOTHESES.md` as the starting pool.

For each H01-H20 return:

- **GO / PIVOT / KILL**;
- nearest collision;
- what remains open;
- strongest falsifier;
- smallest decisive experiment;
- baseline requirements;
- estimated cost/compute;
- primary reviewer objection.

Do not keep more than 6 hypotheses alive after this stage.

## Phase 5 — Synthesize at most three paper arcs

A good arc may combine several hypotheses, but must have one central scientific question.

For each finalist provide:

1. one-sentence claim;
2. null/falsifier;
3. why existing papers/repositories do not already answer it;
4. one decisive minimal pilot;
5. three or more fair baselines;
6. primary + secondary metrics;
7. exact success and kill criteria;
8. version-robust contribution;
9. path from pilot to full paper;
10. five hostile reviewer objections and required rebuttal evidence.

Prefer mechanism/characterization papers over product leaderboards.

## Phase 6 — Minimal pilot design only

Design but **do not execute** one smallest pilot per finalist.

Constraints:

- public data;
- preferably <1 hour wall-clock for a first pilot;
- API budget target <= USD 5 per finalist;
- at most one local GPU if necessary;
- no new model pretraining;
- no large-scale fine-tuning;
- no private datasets;
- no dependence on hidden Jev architecture.

Save exact proposed schemas/prompts, perturbation seeds and metrics.

## Strong baseline requirement

Depending on the arc, include a scientifically appropriate subset of:

- Jev pinned exact model version;
- System One Adapter + one strong structured-output LLM;
- System One Adapter + one cheap/fast LLM;
- openjev-sglang;
- open-jev-deberta-v3-large;
- Mapika/decider-2b;
- GLiNER2.5 / appropriate trained classifier;
- task-specific reranker;
- HybridLLM / FrugalGPT / RouteLLM / GraphRouter;
- RewardBench-compatible reward model;
- raw + temperature/Platt/isotonic calibration;
- confidence/entropy selective baseline;
- conformal risk control;
- trivial majority/random/BM25/embedding baseline.

Never compare constrained-choice Jev against unconstrained free generation and call it fair.

## Metrics

No composite leaderboard as primary metric.

Use appropriate decomposed measures:
- accuracy / macro-F1 / nDCG / AUROC;
- Brier / NLL / ECE / calibration slope;
- risk-coverage / AURC / coverage at fixed risk;
- probability JS/TV distance and flip rate;
- p50/p95/p99 latency;
- cost per 1k decisions;
- failures/timeouts/schema errors;
- paired confidence intervals.

## Mandatory hostile checks

Explicitly test whether a proposed contribution collapses to:

- classic selective prediction;
- classic confidence calibration;
- ordinary LLM routing;
- standard multiple-choice position bias;
- "structured output is faster than generation";
- an interface-confounded benchmark;
- a vendor-specific benchmark that will age out with the next Jev version.

If yes, PIVOT or KILL.

## Final decision standard

A project-level **GO** requires:

- a real, verified literature/repository gap;
- a narrow falsifiable question;
- an informative negative result;
- >=3 fair baselines;
- public/reproducible data;
- conclusion robust to Jev version churn;
- a minimal pilot feasible within hours;
- a plausible path to a CCF-A paper.

Otherwise return PIVOT or KILL.

## Mandatory stop

Stop after the literature/project audit, hypothesis triage, finalist arcs, pilot designs, reviewer attacks and project-level GO/PIVOT/KILL.

Do not run paid Jev calls, download large models, train, or execute experiments in this first round.
