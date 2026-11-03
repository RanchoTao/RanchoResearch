# Jev / System-One Falsifiable Hypothesis Pool v0.1

> Snapshot: 2026-09-21  
> Goal: feed AutoResearch a deliberately broad pool, then aggressively GO/PIVOT/KILL.  
> Rule: every hypothesis must survive a literature/repository collision audit before any paid run.

## Common experimental discipline

For every live Jev experiment:

- record requested model and returned exact model version;
- timestamp every run;
- save full request/response, wall-clock latency, token usage, retry/failure metadata;
- freeze dataset revision/hash, prompt/schema, label order and random seed;
- do not silently retry failures out of the denominator;
- distinguish **native Jev probabilities**, **token-derived probabilities**, and **verbalized LLM probabilities**;
- use matched decision interfaces for comparisons wherever possible.

---

## H01 — Multi-question amortization has a stable scaling law

**Claim.** For a fixed state, Jev's marginal latency per additional independent question grows far more slowly than autoregressive structured-output baselines, without a corresponding accuracy/calibration loss.

**Why falsifiable.** Sweep question count while holding state and task distribution fixed.

**Minimal test.**
- N = 1, 2, 4, 8, 16, 32, 64 questions;
- mix Noul/Choice/Score and repeat with homogeneous question types;
- compare Jev, System One Adapter + one fast LLM, openjev-sglang, and open-jev-deberta where applicable;
- measure latency p50/p95, cost, answer drift, Brier/NLL.

**Falsifier.** Jev's latency/cost scales similarly to the best non-generative baseline, or batching materially changes predictions.

**GO signal.** A reproducible scaling regime plus a mechanistic systems explanation that generalizes across state lengths and question types.

**Collision risk.** Official parallel-questions cookbook already demonstrates one 13-question case. A paper needs the *scaling law and boundary*, not the existence of batching.

---

## H02 — Batched questions are behaviorally independent

**Claim.** Adding semantically unrelated questions to the same call does not materially perturb the answer distribution of an existing question.

**Minimal test.**
- choose 100-500 frozen decisions;
- query target alone;
- append 1/4/16/64 irrelevant questions, relevant-but-independent questions, and adversarially worded unrelated questions;
- compare total variation / JS distance and flip rate.

**Falsifier.** Systematic probability shifts exceed run-to-run noise or grow with batch composition.

**GO signal.** Either strong invariance with tight empirical bounds, or a reproducible interference effect with a simple predictor/mitigation.

**Collision risk.** Vendor explicitly claims independence and has one cookbook. Independent broad falsification remains open.

---

## H03 — Choice is robust to option permutation

**Claim.** Jev's probability assigned to semantic options is approximately invariant to reordering of the option list.

**Minimal test.**
- AG News, Banking77, JevBench public decisions;
- 10-30 random permutations/item;
- compare Jev vs structured LLM, openjev-sglang, open alternatives;
- track semantic probability variance and answer flip rate.

**Falsifier.** Jev exhibits position effects comparable to ordinary LLM multiple-choice selection.

**GO signal.** A statistically strong difference in position sensitivity, or a discovered order-bias failure mode with a correction.

**Closest paper.** Zheng et al., ICLR 2024, establishes option-position bias in LLMs.

---

## H04 — Semantically equivalent label descriptions preserve decisions

**Claim.** Jev is more invariant than generative baselines to meaning-preserving paraphrases of instructions and option descriptions.

**Minimal test.**
- generate or hand-curate 5 paraphrases per schema;
- preserve label semantics and state;
- measure probability-vector drift and calibration.

**Falsifier.** Paraphrase variance is not lower than matched baselines or dominates ordinary sampling variance.

**GO signal.** A robust invariance result across domains, or a taxonomy of wording sensitivity that predicts failure.

---

## H05 — Primitive representations are not interchangeable, but their mismatch is predictable

**Claim.** Asking the same semantic proposition as Noul, 2-way Choice, and ordered Score produces systematically different probability semantics; a simple transformation or calibration layer can predictably reconcile them.

**Motivation.** TypeSafe's own jaggedness page warns that intuitive identities do not hold across primitives.

**Minimal test.**
- convert binary tasks to equivalent Noul and Choice forms;
- optionally embed into 3-level Score;
- measure probability correspondence, calibration and threshold transfer.

**Falsifier.** No stable relationship exists across tasks, or post-hoc reconciliation offers no held-out benefit.

**GO signal.** A simple cross-primitive calibration law validated on held-out domains.

**Collision risk.** Purely documenting mismatch is already partly known; novelty requires generalization or correction.

---

## H06 — Choice cardinality creates a measurable phase transition

**Claim.** Accuracy, calibration and latency exhibit distinct regimes as the number of options grows; the transition is not explained only by random-choice difficulty.

**Minimal test.**
- construct nested candidate sets K = 2, 4, 8, 16, 32, 64, 128, 255;
- add controlled hard vs easy distractors;
- use Banking77/BTZSC plus synthetic or retrieval candidate sets;
- compare Jev, openjev-sglang and encoder baselines.

**Falsifier.** Degradation follows ordinary statistical difficulty with no distinctive regime or systems effect.

**GO signal.** Reproducible cardinality × distractor-hardness law, especially around the vendor's documented high-cardinality two-stage behavior.

---

## H07 — Context rot follows distractor density, not just token length

**Claim.** Jev degradation from long state is driven primarily by semantically competing irrelevant evidence rather than raw context length.

**Minimal test.**
Create matched state expansions:
1. repeated neutral padding;
2. topically unrelated prose;
3. topically related but decision-irrelevant distractors;
4. adversarial distractors.

Keep target evidence fixed and sweep added tokens.

**Falsifier.** Performance depends only on length or effects are inconsistent.

**GO signal.** A clean causal curve and mitigation via retrieval/filtering that transfers across datasets/models.

**Motivation.** TypeSafe explicitly documents degradation with irrelevant detail.

---

## H08 — Adversarial state can steer bounded decisions despite type safety

**Claim.** Schema validity does not imply semantic robustness: adversarial instructions embedded in state can shift Jev probabilities and decisions.

**Minimal test.**
- prompt-injection dataset;
- matched benign/adversarial pairs;
- vary instruction/criteria specificity;
- compare Jev, structured LLM and open decision models.

**Falsifier.** No meaningful attack effect under realistic state injection.

**GO signal.** A reproducible attack/defense curve and evidence that bounded decision interfaces change attack surface relative to chat models.

**Note.** "Jev is adversarially robust" is already contradicted by TypeSafe's jaggedness documentation; study mitigation, not denial.

---

## H09 — Native Jev probabilities are better calibrated under distribution shift

**Claim.** After matching task accuracy, Jev's native probabilities degrade less under domain/OOD shift than verbalized LLM probabilities and token-derived/open-decision probabilities.

**Minimal test.**
- Banking77 in-domain vs OOS;
- CLINC150 in-domain vs OOS;
- one sentiment/emotion domain shift;
- one security shift;
- raw and post-hoc calibrated baselines.

**Metrics.**
Brier, NLL, ECE, calibration slope, OOD gap, risk-coverage.

**Falsifier.** Jev loses its advantage after simple temperature/Platt/isotonic calibration, or calibration collapses similarly under OOD.

**GO signal.** Consistent held-out/OOD advantage after fair calibration, or a clear map of where native calibration fails.

---

## H10 — A calibration map transfers across task families

**Claim.** A small global calibration correction learned on some System-One tasks transfers better to unseen tasks for Jev than for verbalized or token-derived baselines.

**Minimal test.**
- fit calibration on 2-3 datasets;
- evaluate without refit on held-out datasets and primitive types;
- compare identity, temperature, vector/Dirichlet calibration where statistically justified.

**Falsifier.** Cross-task calibration transfer is no better than baselines.

**GO signal.** Strong zero-shot calibration transfer, suggesting a model-level uncertainty property rather than task-local tuning.

---

## H11 — Conformal/selective wrappers turn System-One probabilities into explicit risk control

**Claim.** A small calibration set plus conformal/selective risk control yields higher automation coverage at a fixed error bound for Jev than for matched LLM or encoder baselines.

**Minimal test.**
- 3 classification domains;
- split calibration/test;
- target risks 1%, 2%, 5%, 10%;
- compare confidence threshold, entropy, temperature-scaled confidence, conformal risk control.

**Falsifier.** Jev has no coverage advantage at matched risk, or formal wrappers erase any native-confidence benefit.

**GO signal.** Better coverage-cost frontier with finite-sample guarantees.

**Nearest literature.** Selective classification, SelectiveNet, Conformal Risk Control.

---

## H12 — Node-wise calibration does not imply workflow-level calibration

**Claim.** Multiplying/combining apparently calibrated node probabilities in a decision workflow can produce miscalibrated final actions because errors are correlated; explicit dependence correction improves final risk.

**Minimal test.**
- build a small 3-8 node gold-labelled workflow from public data;
- estimate node calibration and pairwise error dependence;
- compare naive independence composition vs empirical/logistic/copula-style correction;
- evaluate final action calibration.

**Falsifier.** Naive composition is already calibrated within uncertainty, or corrections do not transfer.

**GO signal.** A general compositional failure law plus lightweight correction.

**Why valuable.** This targets the core "probabilities composed in code" paradigm rather than Jev accuracy alone.

---

## H13 — Jev improves System-One/System-Two routing at fixed quality

**Claim.** A Jev router can reduce expensive-model calls at a fixed target quality relative to simple confidence/embedding routers and remain competitive with learned routing baselines.

**Minimal test.**
- use RouterBench or LLMRouterBench frozen model outcomes;
- phrase routing as bounded choices over model tiers or fallback;
- compare random/trivial, HybridLLM, RouteLLM/GraphRouter where feasible, and simple classifier;
- measure quality-cost Pareto and router latency.

**Falsifier.** Router compute/cost removes the savings, or established routers dominate quality-cost.

**GO signal.** Distinct low-latency regime, strong OOD transfer, or calibrated abstention advantage.

**Collision warning.** Routing is crowded; "Jev can route" alone is not a contribution.

---

## H14 — Uncertainty-triggered decomposition beats fixed decomposition

**Claim.** A workflow that starts with coarse cheap decisions and only expands into finer questions when uncertainty is high achieves a better cost-risk frontier than always-ask-all or one-shot policies.

**Minimal test.**
- hierarchical intent or document classification;
- fixed full decomposition vs greedy top-1 vs beam search vs uncertainty-triggered expansion;
- same underlying model(s).

**Falsifier.** Dynamic expansion adds complexity without Pareto improvement.

**GO signal.** A simple policy with broad gains and an interpretable stopping rule.

---

## H15 — Decision decomposition itself is a causal source of quality gain

**Claim.** For the same underlying LLM, decomposing a policy into atomic typed questions + deterministic code improves reliability versus one-shot structured prompting, beyond extra token/compute effects.

**Minimal test.**
- choose one public gold-labelled workflow;
- same model, same information;
- one-shot policy prompt vs fixed decomposed workflow;
- equalize or report compute;
- ablate decomposition granularity.

**Falsifier.** Gain vanishes after controlling compute/prompt detail, or decomposition harms accuracy.

**GO signal.** A robust decomposition effect with a boundary condition and causal ablation.

**Motivation.** TypeSafe's official workflow eval reports this direction but uses vendor-created workflows and model-consensus labels.

---

## H16 — Jev's reranking advantage, if any, comes from batched absolute judgments rather than pairwise ranking

**Claim.** Batched per-passage absolute relevance judgments can match dedicated rerankers while offering a different latency/cost/abstention tradeoff; tournament/pairwise schemes are not the source of performance.

**Minimal test.**
- reuse jev-rerank-bench frozen candidates;
- compare batched Score/Noul, one Choice, pairwise, tournament;
- dedicated rerankers and open Qwen baseline;
- add calibration of "nothing relevant".

**Falsifier.** Dedicated rerankers dominate or results are dataset-specific.

**GO signal.** A general batching/abstention principle beyond the existing benchmark.

**Collision risk.** Existing repo already compares several variants; novelty bar is high.

---

## H17 — Fairly constrained agent-failure attribution changes the apparent ranking

**Claim.** When Jev and LLM baselines receive exactly the same candidate set/output constraints, differences on Who&When Pro shrink or change compared with free-generation-vs-choice comparisons.

**Minimal test.**
- rebuild Who, When and What with identical choices for all systems;
- use same traces and scorer;
- compare accuracy/F1, calibration, latency and cost.

**Falsifier.** Existing conclusions remain unchanged and no new mechanism emerges.

**GO signal.** Interface constraint is shown to be a major confound, yielding a general evaluation lesson for typed decision models.

---

## H18 — Most System-One gains can/cannot be explained by prefill-only decision extraction

**Claim.** A substantial fraction of latency/structure gains attributed to a specialized System-One model can be reproduced by taking an open LLM and reading selected-label logits without autoregressive generation; any residual Jev advantage is concentrated in calibration or task competence.

**Minimal test.**
- Jev vs openjev-sglang vs ordinary structured generation from a comparable open model;
- same datasets, schemas, candidate orders;
- quality, calibration, latency, throughput.

**Falsifier.** Prefill-only baseline is either clearly noncompetitive or already explains nearly everything with no scientifically interesting residual.

**GO signal.** A clean decomposition of gains into interface/sampling vs learned-calibration/capability effects.

**Importance.** This is one of the strongest anti-hype hypotheses: it can falsify the need for a new model class or identify the part that truly requires one.

---

## H19 — There is a predictable crossover frontier between System-One models and conventional classifiers

**Claim.** Jev-like models dominate when label semantics/task descriptions must generalize zero-shot or cardinality is large, while trained/specialized classifiers dominate stable low-cardinality domains; the crossover can be predicted from task statistics.

**Minimal test.**
Sweep:
- number of labels;
- train examples per label;
- semantic overlap;
- domain shift;
- state length.

Compare Jev, DeBERTa/GLiNER/classifier and open decision models.

**Falsifier.** No stable crossover pattern exists.

**GO signal.** A simple decision rule for "use a classifier vs System-One model" validated across datasets.

---

## H20 — Latency changes optimal agent policy in closed-loop tasks

**Claim.** On tasks where decisions are made repeatedly under a wall-clock budget, a faster bounded decision model can outperform a more accurate slow model in total task utility because it closes more control loops.

**Minimal test.**
- deterministic simulator or replayable browser/game environment;
- impose identical wall-clock budget;
- compare fast bounded controller, slow high-quality controller, hybrid fallback;
- report task utility vs decision latency.

**Falsifier.** Per-step quality dominates and faster decisions provide no end-to-end utility.

**GO signal.** A reproducible latency-quality phase diagram.

**Priority.** Later round only; higher engineering confound than H01-H15.

---

# Suggested first-pass pruning order

AutoResearch should collision-audit all 20, but spend deepest effort first on:

- H02 batched-question interference;
- H03 option-order invariance;
- H06 cardinality scaling;
- H09 OOD calibration;
- H11 risk-controlled selective automation;
- H12 workflow probability composition;
- H13 System-One/System-Two routing;
- H18 prefill-only explanation.

These have the clearest falsifiers, strongest connection to the claimed model class, and a path to conclusions that remain meaningful if Jev itself changes version.

