# Jev / System-One Research Map v0.1

> Snapshot: 2026-09-21  
> Scope: public evidence only. Vendor claims, independent reproductions, community benchmarks, and peer-reviewed literature are separated explicitly.  
> Research standard: find a falsifiable scientific question, not a Jev leaderboard.

## 0. Executive map

Jev is TypeSafe AI's first public "System One" model. The public interface is deliberately narrow:

- input: unstructured/structured `state`;
- questions: `Choice`, `Score`, and `Noul`;
- output: typed decisions plus probability distributions; `Choice` and `Score` also expose a scalar confidence;
- multiple questions can be submitted in one call and are claimed to be evaluated in parallel and independently;
- Jev does not generate free-form strings.

The strongest research opportunity is **not** "does Jev beat model X on dataset Y?". The scientifically interesting object is the **typed probabilistic decision primitive** and the claim that a model specialized for bounded decisions can create a different accuracy/calibration/latency/cost frontier from:

1. autoregressive LLMs forced through structured output;
2. token-logprob / prefill-only decision wrappers;
3. conventional discriminative classifiers;
4. reward/judge models;
5. learned routers;
6. deterministic or retrieval-first systems.

A credible paper should isolate *why* and *when* this primitive helps, identify its failure boundaries, or derive a statistically principled routing/defer mechanism around it.

---

## 1. What is publicly known vs not known

### Publicly documented

TypeSafe's current public docs and launch material state that:

- Jev is the flagship System One model.
- The three primitives are:
  - **Choice**: select one among a fixed set; returns choice, probabilities, confidence.
  - **Score**: ordered rubric with 2-10 levels; returns expected score, level probabilities, confidence.
  - **Noul**: yes/no proposition; returns p(yes).
- Choice supports up to 255 options.
- Questions in one request are intended to be evaluated independently against the same state.
- TypeSafe recommends atomic questions composed in ordinary code rather than long monolithic prompts.
- TypeSafe positions confidence as a routing/deferral signal rather than merely a display value.
- The launch post names a "new model architecture", a parallel sampler, and **Reinforcement Learning for Calibrated Decisions (RLCD)**.
- Vendor-listed price at launch: $0.042 per million input tokens; output tokens are free.
- Vendor-listed end-to-end latency range: roughly 70-500 ms, depending on request/service conditions.
- TypeSafe's official workflow evals use four workflows: Security Incidents, Agent Trace Observability, Invoice Processing, and Customer Service.

Primary sources:
- https://typesafe.ai/blog/introducing-system-one-models-and-jev
- https://docs.typesafe.ai/
- https://docs.typesafe.ai/llms.txt
- https://evals.typesafe.ai/
- https://github.com/typesafe-ai/system-one-adapter-python

### Important unknowns

As of this snapshot, no public primary source located in this audit gives enough detail to reconstruct:

- the Jev architecture;
- the parallel sampler algorithm;
- the RLCD objective/training algorithm;
- training corpus composition;
- train/eval contamination controls;
- public pretraining/post-training ablations;
- a vendor-run standard public benchmark suite with gold labels.

Therefore **do not treat architecture or RLCD explanations inferred by community replicas as facts about Jev**.

The launch post's strongest speed/cost/intelligence claims are vendor measurements. TypeSafe itself notes that the workflow tasks were created by its model-capabilities team and that the evaluation reference is the average of two external frontier models rather than human gold labels. Treat these as motivating evidence, not independent scientific validation.

---

## 2. Official technical surface

### Documentation index

The official `llms.txt` index is the best discovery root. Relevant groups:

- foundations: System One, State, primitives, confidence;
- patterns: speculative fan-out, confidence-gated routing, composite scoring, intent routing;
- SDKs/API: Python, JavaScript, HTTP API, retries, model cards;
- model jaggedness: Jev 1.13 known failure modes;
- cookbooks: self-consistency, parallel questions, reranking, search, function calling, guardrails, hierarchical classification, RAG filtering, citation checking, structured-data cascades, feature discovery, confidence-aware classification.

### Known Jev 1.13 jagged edges

TypeSafe's own page, last reviewed 2026-09-17, lists:

1. literal reading / sensitivity to underspecified wording;
2. weak arithmetic and counting;
3. weak numeric representations;
4. weak date/time comparison;
5. degradation with indirection / multi-hop reasoning;
6. degradation from large amounts of irrelevant state;
7. susceptibility to adversarial content in state;
8. contradictions between instructions and criteria;
9. no guarantee of intuitive structural invariants across primitives or negated questions;
10. no free-form generation.

This page is unusually valuable for research because several items are directly measurable and can be turned into controlled causal experiments.

Primary source:
- https://docs.typesafe.ai/model-jaggedness/jev-1.13

### Official internal claims worth independent replication

The official parallel-questions cookbook reports, on one 13-question GDPR example:

- batched vs single-question answers were effectively unchanged over five repeats;
- one batched request was reported 12.2x cheaper and 10.0x faster than 13 sequential single-question requests.

This is a **single vendor-authored cookbook**, not a general theorem. It motivates controlled scaling experiments in number of questions, state length, question heterogeneity, and concurrency.

Primary source:
- https://docs.typesafe.ai/cookbooks/parallel_questions

---

## 3. Public benchmark / evaluation landscape

### A. TypeSafe workflow evals (official, vendor-authored)

Four production-shaped workflows:
- Security Incidents
- Agent Trace Observability
- Invoice Processing
- Customer Service

Protocol:
- same decomposed workflow for all models;
- Noul / Choice / Score primitives;
- reference probabilities are the average of high-thinking GPT-6 Astra and Claude Fable 5.1;
- vendor reports a strong cost/time/accuracy Pareto position for Jev.

Research use:
- useful as a *workflow design template*;
- weak as definitive ground truth because labels are model-consensus and tasks are vendor-created.

Source:
- https://evals.typesafe.ai/

### B. JevBench — typed decision benchmark

Repository:
- https://github.com/fstandhartinger/jevbench

Useful properties:
- explicit typed-decision task families;
- public + held-out + imported cohorts;
- dimensions include capability, calibration/reliability, speed, cost, openness;
- systems include Jev and several open Jev-shaped replicas;
- task families include routing, answer adequacy, policy yes/no, intent classification, ordinal severity, and enum extraction.

Important methodological lesson:
- composite leaderboard scores should **not** be the primary scientific endpoint;
- decompose into accuracy, Brier/NLL/ECE, risk-coverage, invariance, latency and cost.

### C. Zero-shot classification: Jev vs GLiNER2.5

Repository:
- https://github.com/AbdelStark/jev-benchmarks

Pilot:
- AG News: 4 labels
- Banking77 / BTZSC: 72 candidates plus out-of-scope rows
- DAIR Emotion: 6 labels
- deterministic 100-example samples per dataset

Reported result is mixed:
- Jev substantially stronger on AG News and Banking77 in this pilot;
- Emotion accuracy is unresolved;
- Jev calibration on Emotion is poor, including zero mass on the true label for a non-trivial fraction.

This is strong motivation for **task-dependent calibration and OOD/selective-risk studies**.

### D. Retrieval / reranking

Repository:
- https://github.com/anessbelbati/jev-rerank-bench

Coverage:
- eight English datasets, 1,617 scored questions;
- five BRIGHT subsets;
- NevIR negation;
- MIRACL French;
- BM25 candidate generation;
- Jev variants, Cohere Rerank, ZeroEntropy and an open Qwen control.

Reported aggregate nDCG@10 for Jev and Cohere Pro is nearly tied, while latency/cost differ. This suggests reranking is already a competitive application benchmark; novelty must come from calibration, batching, order effects, abstention, or systems tradeoffs, not another raw nDCG table.

### E. Security

Repository:
- https://github.com/Gaurav-Gosain/jev-sec-bench

Datasets:
- `deepset/prompt-injections`: 662 labelled messages;
- 200 matched vulnerable-code pairs from `CyberNative/Code_Vulnerability_Security_DPO`.

Jev run was recorded against `jev-1.13.0` on 2026-09-16 with raw per-sample outputs. Useful for:
- binary Noul calibration;
- adversarial-state robustness;
- threshold/risk studies.

### F. Agent failure attribution

Repository:
- https://github.com/TokenTrim/jev-agent-failure-benchmark

Dataset:
- Who&When Pro, text subset, 6,257 traces;
- source: `Leoxx/whowhen_pro`.

Tasks:
- responsible agent;
- decisive step;
- error type.

Critical comparability warning:
- Jev gets constrained choices for "Who" and "When" while the paper LLM baselines free-generate;
- the error-type taxonomy is closer to like-for-like.

Use this dataset only after rebuilding **matched interfaces** for all baselines.

### G. Chess / NPC addressee

Repository:
- https://github.com/wondertwins/jev-benchmark

Purpose:
- chess deliberately probes outside Jev's intended lane;
- NPC addressee detection probes a natural fast bounded decision.

Main scientific value:
- demonstrates that state representation/precomputation can dominate outcome;
- useful for testing "code computes exact features, System One judges semantics".

### H. Ecosystem directories

Discovery only; do not cite individual performance claims without opening the source:
- https://awesomejev.com/
- https://github.com/hellogumbo/awesome-jev
- https://github.com/JohnDotOwl/awesome-jev
- https://github.com/ozers/jevsome-projects

The ecosystem grew extremely quickly after the 2026-09-15 launch. These indexes are useful for collision discovery but are noisy and contain demos, promotional projects and duplicated entries.

---

## 4. Open Jev-shaped / System-One-like implementations

These are essential baselines because they test whether the useful behavior comes from a proprietary architecture/training method or from the decision interface itself.

### openjev-sglang

- repo: https://github.com/ekzhang/openjev-sglang
- backend: Qwen3.6-35B-A3B on SGLang;
- Jev-compatible API;
- prefill-only selected-token log-probability approach;
- explicitly states that its probabilities are conditioned on supplied options and **are not calibrated correctness probabilities**;
- confidence is normalized entropy.

Research role:
- strongest "maybe the gain is just no autoregressive generation" baseline.

### open-jev-deberta-v3-large / typed-decisions

- model: https://huggingface.co/com-kotobalabs/open-jev-deberta-v3-large
- code family: https://github.com/kotoba-lang/typed-decisions
- DeBERTa-v3-large based;
- one state + multiple typed questions;
- no text generation;
- trained/evaluated on Banking77, SST-5, BoolQ;
- Apache-2.0.

Research role:
- discriminative / encoder-style Jev-shaped baseline;
- useful for static low-latency classification and OOD studies.

### Other replicas to collision-check

JevBench currently references:
- `system-one-open`
- `open-alternative-jev`
- other open rebuilds exposed through TypeSafe-like endpoints.

Do not assume any of them reproduce Jev's hidden architecture or RLCD. Treat them as competing implementations of the **interface/behavioral contract**.

---

## 5. Dataset map

### Typed classification / routing

High priority:
- AG News
- Banking77 / BTZSC
- CLINC150 including out-of-scope examples
- DAIR Emotion
- SST-5
- BoolQ
- TREC / fine-grained question classification
- selected intent-routing datasets already packaged in JevBench

Best uses:
- choice-cardinality scaling;
- semantic label overlap;
- paraphrase / order robustness;
- OOD and abstention;
- calibration.

### Retrieval / reranking

- Jev rerank benchmark's eight English datasets
- BRIGHT
- NevIR
- MIRACL
- optionally BEIR subsets with frozen BM25 candidates

Best uses:
- parallel many-candidate judgments;
- "none relevant" detection;
- ranking calibration;
- order sensitivity;
- latency/cost at fixed nDCG.

### Security / guardrails

- deepset/prompt-injections
- CyberNative/Code_Vulnerability_Security_DPO
- Jigsaw / toxicity or hate-speech sets for calibrated binary decisions
- SafeRLHF subsets when labels map cleanly to bounded decisions

Best uses:
- Noul calibration;
- adversarial state injection;
- risk-controlled selective automation.

### Agent traces

- Who&When Pro text subset
- τ²-Bench traces/tasks where a bounded routing/verification decision can be defined

Best uses:
- failure attribution;
- verifier / escalation decisions;
- System-One/System-Two handoff.

### LLM routing

- RouterBench: >405k recorded LLM inference outcomes
- LLMRouterBench: 400k+ instances, 21+ datasets, 33 models, 10 routing algorithms

LLMRouterBench covers math, code, logic, knowledge, affect, instruction following and tool use, including AIME, LiveMathBench, LiveCodeBench, SWE-Bench, BBH, KORBench, HLE, SimpleQA, EmoryNLP/MELD, ArenaHard and τ²-Bench.

Best use:
- evaluate Jev as a router against established routing algorithms under fixed quality/cost constraints.

### Judge / reward

- RewardBench
- RewardBench 2

Best uses:
- bounded preference selection;
- judge confidence;
- abstention and calibration;
- compare decision models with reward models and LLM-as-a-judge.

### Vendor cookbook replication seeds

Not standalone gold benchmarks, but useful controlled fixtures:
- GDPR 13-question batching example;
- CLERC legal reranking;
- SEC 75-industry confidence-aware classification;
- hierarchical classification examples;
- citation checking / RAG passage filtering;
- skill suggestion / function calling.

---

## 6. Baseline matrix

Every experiment must use the smallest relevant subset, but the baseline pool should include:

| Class | Baseline | What it isolates |
|---|---|---|
| Proprietary System One | Jev, pin exact returned model version | target |
| Structured generative LLM | TypeSafe `system-one-adapter-python` + strong frontier LLM | interface held fixed, generation retained |
| Cheap generative LLM | same adapter + fast/cheap LLM | cost-quality comparator |
| Prefill/token-logprob | `openjev-sglang` | removes generation without hidden Jev training |
| Encoder decision model | open-jev-deberta-v3-large | classic discriminative architecture |
| Zero-shot classifier | GLiNER2.5 or task-appropriate encoder | specialized classification baseline |
| Reranker | Cohere Rerank / zerank where licensed/available | dedicated retrieval baseline |
| Router | HybridLLM / FrugalGPT / RouteLLM / GraphRouter + trivial router | established LLM routing |
| Reward model | RewardBench-supported RM / PairRM class | preference/judge baseline |
| Calibration | raw + temperature scaling + Platt/isotonic where valid | separates model from post-hoc calibration |
| Selective prediction | max-probability threshold, entropy threshold, conformal risk control | tests native confidence value |
| Trivial | majority/random/BM25/simple embedding similarity | sanity floor |

Rules:
- hold the **decision schema** fixed whenever possible;
- distinguish native probabilities, token-derived probabilities, and verbalized probabilities;
- report failed/malformed calls in the denominator;
- pin prompts, schemas, candidate order and model versions.

---

## 7. Paper neighborhood

### Calibration and selective prediction

1. Guo et al., **On Calibration of Modern Neural Networks**, ICML 2017.
2. Geifman & El-Yaniv, **Selective Classification for Deep Neural Networks**, 2017.
3. Geifman & El-Yaniv, **SelectiveNet**, ICML 2019.
4. Kadavath et al., **Language Models (Mostly) Know What They Know**, 2022.
5. Tian et al., **Just Ask for Calibration**, EMNLP 2023.
6. Wang et al., **Calibrating Verbalized Probabilities for Large Language Models**, 2024.
7. Farquhar et al., **Detecting hallucinations in LLMs using semantic entropy**, Nature 2024.
8. Angelopoulos et al., **Conformal Risk Control**, 2022/2024 line of work.

Collision implication:
"Jev has probabilities" is not novelty. The gap must concern **native typed-decision calibration, transfer, risk-coverage, composition, or cost**.

### Choice / judge robustness

9. Zheng et al., **Large Language Models Are Not Robust Multiple Choice Selectors**, ICLR 2024.
10. Shi et al., **Judging the Judges: A Systematic Study of Position Bias in LLM-as-a-Judge**, 2025.
11. Lambert et al., **RewardBench**, NAACL Findings 2025 / arXiv 2024.
12. Malik et al., **RewardBench 2**, 2025.

Collision implication:
position/order bias and judge unreliability are established phenomena; a Jev paper needs to show whether a typed decision model changes the phenomenon or enables a stronger mitigation.

### LLM routing / cost-quality systems

13. Chen et al., **FrugalGPT**, TMLR 2024.
14. Ding et al., **Hybrid LLM**, ICLR 2024.
15. Hu et al., **RouterBench**, 2024.
16. Ong et al., **RouteLLM**, ICLR 2025.
17. Feng et al., **GraphRouter**, ICLR 2025.
18. LLMRouterBench, Findings ACL 2026.

Collision implication:
"route cheap vs expensive model" is crowded. A Jev routing paper must exploit a distinctive property such as calibrated bounded decisions, near-constant multi-question latency, cross-model generalization, or risk guarantees.

### Statistical judge reliability

19. **Noisy but Valid: Robust Statistical Evaluation of LLMs with Imperfect Judges**, ICLR 2026.
20. 2026 work on judge calibration/bias and uncertainty should be included in a targeted search before any judge-focused claim.

---

## 8. Collision matrix

| Candidate claim | Existing collision | Status before new experiments |
|---|---|---|
| Jev is faster/cheaper than a chat LLM on typed workflows | TypeSafe official eval + many community demos | KILL as standalone paper |
| Batching many questions is faster/cheaper | official parallel-questions cookbook | KILL as standalone; GO only for scaling law/interference analysis |
| Jev can classify/rerank well | multiple public benchmarks already | KILL as standalone leaderboard |
| Jev is calibrated | calibration literature + mixed independent results | OPEN; requires rigorous multi-domain/OOD comparison |
| Confidence can gate fallback | classic selective prediction + TypeSafe docs | OPEN only if System-One gives a new risk/cost frontier or guarantee |
| Jev can route LLMs | crowded routing literature + community routers | OPEN only under matched RouterBench/LLMRouterBench protocol |
| Jev avoids option-order bias | MCQ position bias is known; open alternatives show sensitivity | OPEN and highly falsifiable |
| Questions in one call are independent | explicit vendor claim; one cookbook | OPEN for broad independent falsification |
| Jev handles high-cardinality Choice well | 255-option limit + 2-stage vendor note | OPEN; likely strong systems/scaling question |
| Jev handles irrelevant context poorly | vendor jaggedness explicitly admits it | OPEN only if quantified law/mitigation/general principle |
| Jev is robust to adversarial state | vendor explicitly says current model can be steered | KILL any strong robustness claim; OPEN for mitigation/characterization |
| Jev probabilities compose correctly across workflow nodes | no public validation found | OPEN, high value |
| Proprietary architecture/RLCD is necessary | architecture/training details hidden | cannot prove directly; compare behavior against open counterfactuals |
| Decision decomposition improves LLM workflows | TypeSafe claims + general modular systems intuition | OPEN for independent, gold-labelled reproduction |
| Fast System-One + slow System-Two cascade beats either alone | adjacent to routing/selective prediction | OPEN if formulated as calibrated defer policy and tested broadly |

---

## 9. Evaluation metrics

Never collapse the project into one composite score.

### Predictive quality
- accuracy / macro-F1;
- nDCG@k / MRR for ranking;
- AUROC/AUPRC for binary detection;
- task-specific utility when appropriate.

### Calibration
- Brier score;
- NLL / log loss;
- ECE plus reliability diagrams;
- classwise calibration where imbalance matters;
- calibration slope/intercept;
- OOD calibration gap.

### Selective prediction
- risk-coverage curve;
- AURC / excess AURC;
- coverage at fixed error budget;
- error at fixed coverage;
- cost at fixed target risk.

### Robustness / invariance
- prediction flip rate;
- total variation / Jensen-Shannon distance between probability vectors;
- rank correlation;
- probability shift under paraphrase/order/state perturbations.

### Systems
- end-to-end latency p50/p95/p99;
- provider/model-reported and wall-clock latency separately;
- input/output tokens;
- dollar cost per 1k decisions;
- throughput;
- failures/timeouts/schema violations.

### Statistics
- paired bootstrap or paired permutation where samples are shared;
- confidence intervals on differences;
- preregister primary metric and direction;
- freeze dataset revision, model version and order seeds.

---

## 10. Research posture

The best paper is likely one of these shapes:

1. **Behavioral science of typed decision models**  
   Controlled invariance, interference, cardinality and context studies, with open replicas separating interface effects from Jev-specific effects.

2. **Calibration + selective automation**  
   Native decision probabilities evaluated under OOD shift, then used to build risk-controlled System-One/System-Two cascades.

3. **System-One routing primitive**  
   Jev as a low-latency router on RouterBench/LLMRouterBench, compared fairly against established learned routers.

4. **Compositional decision workflows**  
   Study whether individually calibrated node probabilities remain reliable when composed into multi-node workflow decisions; derive or test a correction.

A publishable project should contain at least one general conclusion that survives removal of the Jev brand name.

---

## 11. Evidence tiers

Use this hierarchy during AutoResearch:

- **Tier A — primary peer-reviewed / official technical source:** conference paper, official docs, official code.
- **Tier B — independent reproducible benchmark:** public protocol + raw outputs + pinned versions.
- **Tier C — community reproduction:** code available, methodology partially documented.
- **Tier D — directory / social / promotional claim:** discovery only.

A GO decision cannot rest primarily on Tier D evidence.



---

## 12. Late-discovery addendum: benchmark and open-baseline bar moved up

Two public resources found in the final collision pass materially raise the novelty bar and are **mandatory** in the first AutoResearch audit.

### Typed Decision Bench v0.3.0 (Blobfish AI)

Public report:
- https://blobfish.ai/leaderboard/reports/typed-decision-bench-v03-20260919
- https://blobfish.ai/benchmarks/typed-decision-bench/tasks

Current v0.3.0 scope:
- 5,387 frozen items;
- 25 typed-decision tasks;
- five use-case-family suites;
- public-dataset ground truth;
- the same System One wire format across systems;
- proper scoring of returned probability distributions plus top-pick accuracy;
- no LLM judge;
- per-system raw/request/answer grading artifacts are exposed for an audited sample, with leaderboard scoring over the full roster.

Systems shown include Jev and multiple open alternatives such as decider-2b, OpenJev, NanoJev, System One Scorer, and JevFish.

Research implication:
- a generic "build a better Jev benchmark" paper now has **high collision risk**;
- use this benchmark as a frozen common test bed, but primary paper claims should be about invariance, calibration transfer, compositional risk, causal decomposition, or another mechanism not captured by one aggregate DecisionScore;
- contamination must be treated explicitly because closed-model training data are unknown.

### Mapika/decider

Repository:
- https://github.com/Mapika/decider
- weights: https://huggingface.co/Mapika/decider-2b

Key properties:
- open Apache-2.0 reproduction of the typed System-One interface;
- Qwen3.5-2B-Base backbone;
- one-pass typed decisions without free-form decoding;
- Choice / Score / Noul-compatible behavior;
- explicit calibration evaluation (NLL/Brier/ECE/AURC);
- roughly 95 public datasets in its training/evaluation registry;
- full training/evaluation code and released weights;
- a TypeSafe-compatible wire endpoint;
- explicit question-independence and isolated-score-level implementations.

Most important collision:
the project reports that **packed multi-question prompts can show order interference**: reversing question order changes up to 12% of answers on seven multi-question tasks. Its independent-scoring design eliminates that dependence by construction while keeping accuracy close on those tasks.

Research implication:
- H02 cannot be pitched merely as "multi-question packing might interfere"; an open implementation has already observed this phenomenon and proposed a construction that removes it;
- H02 must instead ask whether **Jev's claimed independence is empirically stronger than packed autoregressive/open baselines**, quantify its failure envelope, or compare architectural/interface strategies under matched state reuse and systems cost;
- H18 becomes stronger: decider is an additional counterfactual separating "typed one-pass interface" from proprietary Jev training;
- H06/H19 also gain a serious open baseline because decider publishes high-cardinality and long-state results.

### Revised minimum open-baseline set

For any core claim about the model class, the default shortlist is now:

1. Jev (pin exact returned version);
2. Mapika/decider-2b;
3. openjev-sglang;
4. open-jev-deberta-v3-large or a task-specialized encoder;
5. System One Adapter + a generative LLM when the question concerns generation-vs-decision effects.

A paper may use fewer only when a baseline is scientifically irrelevant to that specific hypothesis.
