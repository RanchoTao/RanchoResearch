# Public repository scope and archival policy

The default branch is for reusable research-automation software, not an archive of individual research projects.

## Include

- Installable Python source and stable entry points
- Generic example configuration (never a real API credential)
- Generic tests, public benchmark harnesses when explicitly attributed
- Research-state schemas and software architecture documentation
- Upstream licenses and third-party notices

## Exclude

- Submissions, manuscript drafts, author-specific files and scientific source bundles
- Frozen research run histories, task ledgers, personal notes, historical experiment folders
- Model weights/checkpoints, dataset caches, analysis plots, raw experiment traces
- Scratch directories and local environment diagnostics
- Files containing a local username, home directory path, token, password or personal credential

## Preservation vs. visibility

Removing files from the default branch is a **distribution boundary**, not secure erasure.
Old Git objects and existing release branches remain accessible unless a separate,
reviewed history rewrite and hosting/cache remediation is completed. Do not claim that
identifying information has been eradicated from public history.

The existing cached-display publication release depends on a 1,759-entry legacy
manifest; it is intentionally **not** moved into this stripped-down software tree.
Preserve that historical verification boundary in its original repository
revision. Do not weaken its hash checks to make cleanup pass.

Prior to any history rewrite, independently preserve all required scientific
inputs and audit logs, verify owner rights, and assess effects on open pull requests,
signed references and anyone with existing clones. No history rewrite is performed
by this release cleanup.

## Incoming contribution gate

Before merging, check for:
1. Machine-local filesystem paths, credentials and sensitive metadata
2. Manuscript-specific names, submission IDs and previously private runs
3. License notices for copied or modified third-party code
4. Changes to actual functionality or reproduction guarantees
5. Tests and complete, truthful evidence of what was run
