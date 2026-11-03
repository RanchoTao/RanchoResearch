# Run the Jev / System-One First GO/KILL Round

## Inputs

Use:
- `RESEARCH_MAP.md`
- `HYPOTHESES.md`
- `COLLISION_MATRIX.md`
- `GO_KILL_PROTOCOL.md`
- `FIRST_PASS_VERDICT.md`
- `RESEARCH_BRIEF.md`
- `config.arc.yaml`

## PowerShell

From the AutoResearchClaw repository root:

```powershell
cd C:\Users\RanchoTao\Desktop\RanchoAutoResearch\AutoResearchClaw
.\.venv\Scripts\Activate.ps1

researchclaw doctor --config run_inputs/jev-system-one-20260921/config.arc.yaml

researchclaw run `
  --config run_inputs/jev-system-one-20260921/config.arc.yaml `
  --topic "Typed Probabilistic System-One Decision Models: Calibration, Invariance, Composition, and Adaptive Routing"
```

Do **not** add `--auto-approve`.

This first run is intentionally configured as a literature/collision/design pass. It must stop before live Jev benchmarking, model training, or a large paid experiment. Stage 9 remains a human gate.

## Expected decision

The run should independently decide **GO / PIVOT / KILL** for the project and for H01-H20. It should not treat `FIRST_PASS_VERDICT.md` as ground truth; use it as a hostile starting prior to attack and revise.