# Jev / System-One Collision Matrix v0.1

> Purpose: prevent AutoResearch from rediscovering demos and calling them papers.

| ID | Candidate | Closest public collision | What is already known | What must remain genuinely open | Initial disposition |
|---|---|---|---|---|---|
| H01 | multi-question scaling | TypeSafe parallel-questions cookbook | one 13-question vendor example reports large batching gains | general scaling law, heterogeneity/state-length boundary, cross-system comparison | PIVOT-to-mechanism |
| H02 | batched-question independence | official docs + cookbook | vendor claims questions are isolated; one example shows no batching effect | broad independent interference test, adversarial batch composition, empirical bounds | GO-audit |
| H03 | option-order invariance | Zheng et al. ICLR 2024; JevBench/open replicas | LLM option-position bias is established | whether Jev-native decisions materially change the bias and why | GO-audit |
| H04 | paraphrase invariance | broad prompt robustness literature | prompt wording sensitivity is known | typed-schema-specific invariance and comparison to open replicas | PIVOT-risk |
| H05 | cross-primitive consistency | TypeSafe jaggedness page | Noul/Choice arithmetic identities are explicitly not guaranteed | transferable reconciliation/calibration law | GO only with correction |
| H06 | cardinality scaling | Choice docs; 255 limit; vendor notes 2-stage high-cardinality behavior | API limit and qualitative behavior known | quantitative phase diagram, distractor hardness, calibration/latency transition | GO-audit |
| H07 | context-rot law | TypeSafe jaggedness | irrelevant detail hurts | causal role of length vs semantic distractor density + mitigation | GO-audit |
| H08 | adversarial state | TypeSafe jaggedness; prompt-injection literature | adversarial content can steer current Jev | attack-surface comparison / bounded-decision defense | PIVOT-to-defense |
| H09 | OOD calibration | classic calibration + Jev public mixed results | calibration is not uniformly good | matched OOD transfer vs verbalized/token/encoder baselines | GO-audit |
| H10 | cross-task calibration transfer | LM calibration literature | task shift often breaks calibration | whether native decision probabilities transfer unusually well | GO-audit |
| H11 | risk-controlled automation | selective prediction + conformal risk control | confidence thresholding is old | coverage-at-risk advantage and finite-sample System-One cascade | GO-audit |
| H12 | workflow probability composition | probabilistic graphical modeling broadly; no direct Jev validation found | node confidence alone does not imply joint independence in general | empirical dependence structure + correction for typed workflows | GO-audit |
| H13 | Jev LLM router | HybridLLM, FrugalGPT, RouteLLM, GraphRouter, RouterBench, LLMRouterBench | routing is heavily studied | distinctive low-latency/calibrated/OOD regime | PIVOT-risk |
| H14 | uncertainty-triggered decomposition | hierarchical classification, adaptive computation, vendor patterns | adaptive routing/decomposition exists broadly | simple transferable policy leveraging typed probabilities | PIVOT-risk |
| H15 | decomposition causal gain | TypeSafe official workflow eval | vendor reports workflow > prompt | independent gold-label reproduction with compute/granularity controls | GO-audit |
| H16 | reranking mechanism | jev-rerank-bench | extensive Jev reranking variants already run | a general batching/abstention principle, not another nDCG table | HIGH collision |
| H17 | fair agent-failure comparison | jev-agent-failure-benchmark | current comparison has interface asymmetry on Who/When | matched-interface conclusion and evaluation lesson | GO as audit paper component |
| H18 | prefill-only explanation | openjev-sglang + many open replicas | Jev-shaped API can be approximated without generation | isolate sampling/interface effect vs residual calibration/capability | GO-audit |
| H19 | classifier crossover | Jev-vs-GLiNER pilot; encoder replicas | isolated comparisons exist | predictive crossover frontier across K/data/OOD/overlap | GO-audit |
| H20 | latency-sensitive closed loop | many fast-agent demos | demos suggest value of low latency | controlled wall-clock causal phase diagram | later round |

## Automatic KILL rules

Kill a candidate as a paper core if any of the following is true:

1. The novelty reduces to "Jev is faster/cheaper" or "Jev gets higher accuracy on benchmark X".
2. The exact claim is already established by an official or independent reproducible source and the proposed work only adds more samples.
3. The experiment cannot distinguish:
   - decision interface effect,
   - non-autoregressive/prefill effect,
   - model capability,
   - calibration method.
4. The primary conclusion depends on hidden Jev architecture/training details that cannot be observed or falsified.
5. A task-specific classifier/reranker/router baseline is omitted where it is the obvious alternative.
6. The result would become meaningless if `jev-latest` changed next month.
7. The evaluation compares constrained Jev outputs to unconstrained LLM generation without an interface-matched control.

## GO conditions for a paper core

A candidate can receive GO only if:

- the open question is stated without brand marketing language;
- at least three strong baselines exist and are runnable;
- a primary falsifier is specified before the experiment;
- the minimal experiment can settle the sign/direction of the claim;
- the expected contribution survives a negative Jev result;
- model/version and dataset contamination risks can be frozen/audited;
- there is a plausible path from pilot to a multi-domain general result.

## Evidence labels

- **CONFIRMED**: primary paper/official API behavior or independently reproduced result with artifacts.
- **VENDOR CLAIM**: TypeSafe-authored benchmark/marketing claim.
- **COMMUNITY RESULT**: third-party result with code/raw outputs.
- **INFERENCE**: our hypothesis or interpretation.
- **UNKNOWN**: not public / not verified.

AutoResearch must use these labels in every synthesis table.


## Final collision-pass updates

Two discoveries materially change the triage:

### Typed Decision Bench v0.3.0
- 5,387 frozen items / 25 tasks / five suites;
- public-dataset ground truth;
- proper probability scoring and top-pick accuracy;
- same typed wire interface across six systems.

**Effect:** any generic "new Jev benchmark / leaderboard / aggregate DecisionScore" arc is now **KILL** unless it measures a scientifically distinct property that the benchmark does not address.

### Mapika/decider
- open Qwen3.5-2B typed-decision model with released weights/training/eval code;
- publishes NLL/Brier/ECE/AURC, high-cardinality tests, long-state tests, and explicit independence probes;
- reports up to 12% answer changes from reversing packed-question order on seven multi-question tasks; independent per-question scoring removes the dependence by construction.

**Effect on hypotheses:**
- **H02:** PIVOT from "discover batching interference" to "test Jev's empirical independence claim and characterize the accuracy/latency cost of achieving independence across implementations."
- **H06:** stronger baseline; keep GO-audit only if cardinality law exceeds existing decider high-cardinality tables.
- **H09/H10/H11:** stronger calibration/selective baseline; Jev must beat or differ from a trained open calibrated decision model, not only chat LLMs.
- **H18:** strengthened; now compare at least two open counterfactual mechanisms (prefill-logit and trained one-pass typed model).
- **H19:** raised novelty bar; crossover study must explain/predict regimes, not merely compare accuracy.

### Revised paper-core shortlist after public collision pass

- **GO-audit:** H03, H09, H11, H12, H18.
- **PIVOT-audit:** H02, H05, H06, H07, H10, H15, H19.
- **KILL as standalone core:** H01, H04, H08, H13, H14, H16, H17, H20.
- **H17 remains useful as a methodology/confound section**, not the main paper claim.
- H13 can re-enter only as a downstream application of H09/H11, not as "Jev is a router."

This is a **pre-experiment** disposition, not a final scientific verdict. AutoResearch must still verify the literature and repositories independently.
