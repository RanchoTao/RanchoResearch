# Contributing to RanchoResearch

RanchoResearch is a maintained derivative of AutoResearchClaw. See [upstream and licensing notices](THIRD_PARTY_NOTICES.md).

## Setup

```bash
python -m venv .venv
# Activate your environment
python -m pip install -e ".[dev]"
ranchoresearch --help
python -m pytest tests/test_public_release_contract.py -q
```

For broader regression coverage run `python -m pytest tests/ -q`. Some integrations need external services or optional extras and should be explicitly identified as not run when unavailable.

## Pull requests

- Make one coherent change per PR and explain which executable checks you actually ran.
- Preserve existing `researchclaw` imports and command compatibility unless the change includes a tested migration.
- Keep personal scientific projects, manuscript drafts, large weights, local paths, cached logs and secrets out of the public distribution.
- Clearly distinguish observed experiment measurements from simulated outputs and proposed work.
- Preserve copyright/license notices for inherited code and third-party assets.
- Changes to scientific reproduction boundaries or Git history require separate review.

## Reporting security issues

Do not paste keys, internal paths, private research, or exploit details into public issues. Use GitHub's private vulnerability reporting when available, or contact the repository owner through an appropriate private channel.
