# Jev / System-One Research Map v0.1 — First-Pass Verdict

> Date: 2026-09-21
> Status: manual pre-triage after public-source collision audit.
> This does **not** replace the AutoResearch literature stage; it defines what deserves deeper audit.

# Project-level verdict: GO — but only after reframing

**GO** for the broader scientific object:

> typed probabilistic decision models as a fast bounded-decision layer, studied through calibration, invariance, probability composition, and open counterfactuals.

**KILL** the weaker project:

> "Jev is fast / cheap / accurate, so benchmark it on several datasets."

The public ecosystem already contains:
- official TypeSafe workflow evaluations and batching examples;
- several Jev-specific benchmarks;
- a 5,387-item / 25-task Typed Decision Bench;
- open Jev-shaped systems;
- dedicated reranking, security, classification, and agent-failure evaluations;
- Mapika/decider, an open trained one-pass typed-decision model with calibration and independence probes.

A credible CCF-A project now needs a claim that remains meaningful even if Jev changes version or disappears.

---

## H01-H20 pre-triage

| ID | Verdict | Reason |
|---|---|---|
| H01 multi-question amortization | **KILL standalone / PIVOT** | vendor already demonstrates batching; open systems expose their own throughput mechanisms. Keep only as a systems axis inside another study. |
| H02 batched-question independence | **PIVOT** | Mapika/decider already documents packed-question order interference and an independent-scoring construction. New question must test Jev's explicit independence claim and the accuracy/latency cost of achieving independence. |
| H03 option-order invariance | **GO** | strong falsifier, established LLM collision is clear, direct typed-model comparison remains useful. Must compare semantic probabilities, not only top-1. |
| H04 paraphrase invariance | **KILL standalone** | prompt robustness is too broad/crowded. Can be a robustness axis in H03/H07. |
| H05 cross-primitive consistency | **PIVOT** | TypeSafe already admits intuitive identities do not hold. Worth doing only if a transferable reconciliation/calibration law emerges. |
| H06 cardinality scaling | **PIVOT** | decider already reports high-cardinality behavior; a simple sweep is no longer enough. Needs a predictive phase law or a principled mechanism. |
| H07 distractor-density context rot | **PIVOT / possible GO** | vendor admits irrelevant-state degradation, but controlled causal separation of length vs semantic competition may still be general. |
| H08 adversarial state | **KILL standalone** | vendor already states adversarial state can steer Jev; prompt-injection literature is crowded. Re-enter only with a novel bounded-decision defense. |
| H09 OOD calibration | **GO** | independent Jev results are mixed; native probabilities vs trained open decision models vs verbalized/token probabilities under shift remains scientifically sharp. |
| H10 cross-task calibration transfer | **PIVOT / possible GO** | high novelty if true, but demanding; first test as an extension of H09 rather than a core claim. |
| H11 risk-controlled selective automation | **GO as H09 extension** | classic selective prediction is old, but the coverage-risk-cost frontier across typed decision models can be valuable if matched baselines and formal calibration wrappers are used. |
| H12 workflow probability composition | **GO** | strongest brand-independent question: node-wise calibration does not imply calibrated composed decisions when errors are dependent. Direct public Jev-specific answer not found in this audit. |
| H13 Jev router | **KILL standalone** | routing literature is crowded: FrugalGPT, HybridLLM, RouteLLM, GraphRouter, RouterBench, LLMRouterBench. Re-enter only as an application of H09/H11. |
| H14 uncertainty-triggered decomposition | **KILL standalone / PIVOT** | close to adaptive computation/cascades/hierarchical classification. Needs a theorem or distinctive typed-probability property. |
| H15 decomposition causes quality gain | **PIVOT** | TypeSafe already reports workflow-vs-policy-prompt gains; independent gold-label replication is useful but weak alone. Pair with H12. |
| H16 reranking mechanism | **KILL standalone** | an extensive Jev reranking benchmark already exists. |
| H17 fair agent-failure comparison | **KILL as paper core** | useful methodological correction/confound study, not enough alone for a CCF-A paper. |
| H18 prefill-only explanation | **GO** | now especially strong because openjev-sglang and Mapika/decider provide two distinct open counterfactuals. Can separate interface/sampling/training/calibration effects behaviorally. |
| H19 classifier crossover | **PIVOT** | open typed classifiers and large public task registries raise the bar. Needs a predictive crossover model, not a comparison table. |
| H20 latency-sensitive closed loop | **KILL first round** | potentially interesting but engineering-confounded and downstream; revisit only after a cleaner model property is established. |

Survivors for deep AutoResearch audit: **H03, H09, H11, H12, H18**, with H07/H10/H15 as conditional extensions.

---

# Three finalist paper arcs

## Arc A — Compositional Calibration of Typed Decision Workflows

### Central question
When individually probabilistic decision nodes are composed in code, how do correlated judgment errors affect the calibration of the final workflow action?

### Core hypothesis
Even if each node is locally calibrated, naive workflow composition assuming independent errors becomes miscalibrated; a lightweight dependence-aware correction improves held-out final-action calibration.

### Why this is promising
- directly studies the central "probabilities + ordinary code" paradigm;
- brand-independent;
- informative if Jev is better, equal, or worse;
- not reducible to "Jev benchmark";
- can use Jev plus open typed systems;
- negative result is useful.

### Minimal pilot
- construct one small gold-labelled 3-8-node workflow from public data;
- systems: Jev, Mapika/decider, one structured-output LLM adapter;
- estimate local Brier/NLL/calibration and residual error correlations;
- compare naive composition vs empirical dependence-aware correction;
- primary: final-action Brier/NLL;
- secondary: ECE, risk-coverage, dependence estimates.

### Kill criterion
No reproducible workflow-level calibration gap after paired uncertainty analysis, or existing literature already contains the same typed-workflow result and correction.

### Reviewer risk
Could collapse into standard probabilistic graphical modeling. The paper must show why learned language-judgment nodes create a practically important dependence structure not handled by the naive System-One workflow abstraction.

**Pre-triage: GO.**

---

## Arc B — Native Decision Probabilities under Shift and Selective Escalation

### Central question
Do native probabilities from typed decision models provide a better *held-out risk signal* than token-derived or verbalized probabilities, especially under distribution shift?

### Core hypothesis
At matched predictive quality, calibrated typed decision models achieve a better coverage-at-fixed-risk / total-cost frontier for System-One -> System-Two escalation.

### Minimal pilot
- datasets: Banking77/CLINC OOS + one unrelated held-out domain;
- systems: Jev, Mapika/decider, openjev-sglang, structured-output LLM;
- evaluate raw probabilities and the same post-hoc calibration families;
- primary: coverage at fixed target risk or AURC;
- secondary: Brier, NLL, ECE, total cascade cost;
- explicitly test in-domain and OOD.

### Kill criterion
Any Jev/native advantage disappears after simple post-hoc calibration, does not transfer across domains, or is dominated by decider/ordinary classifiers.

### Reviewer risk
"Selective prediction and calibration are old." The contribution must be a new empirical/general result about **probability source and transfer under bounded semantic decisions**, not thresholding itself.

**Pre-triage: GO, but novelty audit is mandatory.**

---

## Arc C — What Is Actually New in a System-One Decision Model?

### Central question
Which observed gains come from eliminating autoregressive generation, which from training a model specifically for typed decisions, and which from proprietary Jev behavior?

### Core hypothesis
The System-One performance envelope decomposes into at least three behaviorally separable factors:
1. interface/sampling: bounded outputs and no free-form decoding;
2. task specialization: training for typed semantic decisions;
3. probability quality: calibration/selective reliability.

### Minimal pilot
Use the same frozen schemas and data across:
- Jev;
- openjev-sglang (prefill/token-logprob);
- Mapika/decider (trained one-pass typed model);
- open-jev-deberta or task classifier;
- one structured-output generative LLM.

Sweep:
- option cardinality;
- number of simultaneous questions;
- state length / distractor density.

Measure:
- accuracy;
- Brier/NLL/ECE;
- probability invariance;
- latency/throughput.

### Kill criterion
Observed differences are entirely explained by raw model scale/capability or provider latency and cannot be separated under controlled interfaces.

### Reviewer risk
Could look like a systems benchmarking paper. It needs a compact causal decomposition and predictive claim, not a leaderboard.

**Pre-triage: GO.**

---

# Which pilot should run first after AutoResearch approves?

**Arc A should be audited first for novelty**, because it is the least Jev-brand-dependent and most likely to yield a general scientific object.

If Arc A collides heavily with existing compositional-calibration literature, run the smallest Arc B pilot next. Arc C is the strongest anti-hype/control arc and should remain in the study even if it becomes a supporting section rather than the paper title.

This priority is provisional and must be reversed if the literature stage finds a direct nearest-neighbor collision.

---

# Mandatory first-round AutoResearch output

Before any paid API experiment, AutoResearch should produce:

1. 20-40 paper literature map;
2. audited public-project table;
3. H01-H20 GO/PIVOT/KILL table;
4. five nearest neighbors for Arc A/B/C;
5. exact novelty threats;
6. one frozen minimal pilot for each surviving arc;
7. hostile reviewer simulation;
8. final project-level GO/PIVOT/KILL.

Do not proceed merely because this pre-triage says GO.
