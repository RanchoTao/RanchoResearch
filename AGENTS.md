# RanchoResearch repository guidance

## Scope
This repository distributes reusable research-automation software. It must not double as a personal manuscript, ICLR handoff, experiment checkpoint, or agent scratch workspace.

## Before edits
- Identify the affected module and preserve CLI/Python compatibility unless a migration is explicitly planned.
- Confirm third-party provenance and preserve original notices. Do not claim upstream code as independently authored.
- Keep changes modular and testable; distinguish software correctness from scientific validity.
- Never generate or commit real provider credentials, local username paths or sensitive transcripts.
- Keep simulated experiments explicitly labeled and require evidence for scientific claims.

## Development
- Install: `python -m pip install -e ".[dev]"`
- Smoke checks: `python -m pytest tests/test_public_release_contract.py -q`, `ranchoresearch --help`
- Broad tests: `python -m pytest tests/` (may require optional integrations)
- Both `ranchoresearch` and `researchclaw` map to the existing `researchclaw.cli:main`.

## Guard rails
- Do not add individual researcher documents, author-identifying filenames, data dumps, model weights or cached publication runs to the public default branch.
- Do not rewrite the Git history, force push or delete historical scientific evidence as part of routine code cleanup.
- If a scientific archive must be relocated, validate it separately with its pinned hashes and original reproduction semantics.
- Do not silently expand automation permissions, skip human gates or enable public publication.

See `docs/ARCHITECTURE.md`, `docs/RELEASE_SCOPE.md` and `THIRD_PARTY_NOTICES.md`.
