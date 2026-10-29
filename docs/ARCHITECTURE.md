# RanchoResearch architecture

RanchoResearch is a maintained derivative of [AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw), not an independent clean-room implementation.

## Current implementation boundaries

- `researchclaw/`: existing Python execution engine (research stages, tools, adapters, LLM clients, CLI). The import namespace `researchclaw` is maintained for compatibility.
- `autoresearch_state/` and `schemas/`: structured state representation and validation.
- `experiments/arc_bench/`: optional upstream ARC-Bench evaluation fixtures. **ARC-Bench is a framework benchmark, not a private ICLR experiment or the project's own ARC-00x research logs.**
- `external/agents/`: optional agent assets inherited from the upstream distribution. Provenance and redistribution rights for individual vendored assets require separate verification.
- `tests/`: executable checks, including release-boundary checks. They do not demonstrate scientific validity of generated work.

`ranchoresearch` is a CLI alias for the same engine as `researchclaw`. The Python package import path is not renamed in this cleanup to avoid breaking existing integrations.

## What is not in this release

Individual manuscript drafts, historical ICLR research handoffs, model checkpoints, run output, personal workspace paths, and cached publication reproduction assets are outside the default software release.

This separation does not rewrite Git history, establish a complete source-attribution audit, or imply those records are now inaccessible through old commits. The pre-cleanup commit is preserved in repository history; see the pull request for its precise identity.

## Execution semantics

The documented pipeline has literature, hypothesis, experiment and paper-production stages, but successful generation is **not** proof of novelty, correctness, publication readiness, or independent replication. Human review and source integrity remain necessary. Experimental/simulated execution must be labeled accurately.

## Software verification

Run:

```bash
python -m pip install -e ".[dev]"
python -m pytest tests/test_public_release_contract.py
ranchoresearch --help
researchclaw --help
```

For broader regression coverage, run `python -m pytest tests/` in a compatible environment. Full integration, remote provider, GPU, and scientific reproducibility validation are separate activities.

For rights and upstream provenance see [third-party notices](../THIRD_PARTY_NOTICES.md).
