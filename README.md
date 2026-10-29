# RanchoResearch

**Research-automation software with explicit evidence, review, and reproducibility boundaries.**

RanchoResearch organizes literature review, hypothesis development, experiment orchestration, analysis, and research-state tracking. It is a maintained software derivative of [AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw), with additional research-state and experiment-workflow work. The current engine retains the `researchclaw` Python namespace for compatibility. This is **not** a claim of clean-room authorship of the upstream engine.

> Status: public-source cleanup and software packaging. Individual research projects, manuscript drafts, ICLR handoffs, local experiment artifacts, and personal workspace files are not part of this distribution. A successful pipeline run is not independent scientific verification.

## Quick start

Requires Python 3.11 or newer.

```bash
git clone https://github.com/RanchoTao/RanchoResearch.git
cd RanchoResearch
python -m venv .venv
# Activate .venv for your shell, then:
python -m pip install -e .
ranchoresearch --help
ranchoresearch init
```

The `init` command creates a local configuration from `config.researchclaw.example.yaml`. Set a provider and credentials in environment variables or untracked local configuration. To inspect the runtime:

```bash
ranchoresearch doctor
```

After configuring a real provider and reviewing execution controls:

```bash
ranchoresearch run --config config.arc.yaml --topic "Your research question"
```

The older `researchclaw` command remains available as a compatibility alias. It uses the same implementation. **Do not enable automatic approval or external publishing without reviewing the relevant gates and costs.**

## Repository map

| Path | Purpose |
| --- | --- |
| `researchclaw/` | Underlying Python pipeline and adapters; compatibility import namespace |
| `autoresearch_state/`, `schemas/` | Structured project decisions, evidence and state validation |
| `experiments/arc_bench/` | Optional upstream ARC-Bench evaluation materials (not personal ARC research tasks) |
| `external/agents/` | Optional upstream-provided agent assets; additional provenance review may be needed |
| `tests/` | Automated software checks |
| `docs/` | Architecture, state schema, release scope and migration policy |

## Research and safety boundaries

- Generated hypotheses, citations, code, results and paper drafts require independent checking.
- Synthetic/simulated outputs must never be presented as real experiments.
- Evidence and source provenance must be recorded; failed and invalidated results must not be silently promoted.
- API keys and local paths must stay in ignored local files or environment variables.
- Personal research archives and unpublished work belong outside this public software tree.
- Removing a file from `main` does **not** remove it from older Git history.

See [architecture](docs/ARCHITECTURE.md) and [public release scope](docs/RELEASE_SCOPE.md).

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest tests/test_public_release_contract.py -q
python -m pytest tests/ -q
```

The full test suite includes optional integrations and can require more dependencies or external services; the published release-check workflow is intentionally a narrower packaging/CLI smoke test. No claim of an end-to-end scientific re-run follows from passing it.

## Licensing and origin

The root [Apache-2.0 license](LICENSE) applies to this project's own contribution terms. Parts of the codebase derive from **AutoResearchClaw by Aiming Lab**, licensed under MIT; the original upstream MIT notice is reproduced in [LICENSES/AutoResearchClaw-MIT.txt](LICENSES/AutoResearchClaw-MIT.txt). Its requirements remain in force for inherited code. See [third-party notices](THIRD_PARTY_NOTICES.md). The original framework and its paper are not represented as RanchoResearch's own work.

---

## 中文说明

RanchoResearch 是一个科研自动化软件项目，现阶段仍以 AutoResearchClaw 的 Python 引擎为基础，保留原有 `researchclaw` 导入接口，并增加 `ranchoresearch` 命令入口。仓库的公开主线只保留通用软件、测试及明确标注来源的基准材料，个人论文、ICLR 实验与历史科研档案不再混入软件发行版。

这次分离不会清除旧 Git 历史，也不构成科研结果已复现或独立验证的声明。完整边界见 [发布范围说明](docs/RELEASE_SCOPE.md)。
