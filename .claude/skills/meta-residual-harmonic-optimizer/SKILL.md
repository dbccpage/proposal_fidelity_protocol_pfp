---
name: meta-residual-harmonic-optimizer
description: "Derive persistent residual invariants across multi-trial hypothesis optimization loops."
status: canonical
operad_source_colours: ["Ledger", "Audit"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
families: [meta, operad]
---

# meta-residual-harmonic-optimizer

`AuthorityEffect: None.`

## Operad Functor Semantics

This metaskill implements the colored operad morphism:

$$\mathcal{O}(Ledger, Audit) \longrightarrow Receipt$$

Under operad composition laws, this operation may be composed with any downstream morphism whose input slot carries color `Receipt`. The operation is contractive when the measured invariant residual decreases strictly ($R_\text{after} < R_\text{before}$) or maintains exact zero defect ($R_\text{after} = R_\text{before} = 0$).

## Input Artifacts

- Source Colors: `Ledger, Audit`
- Target Color: `Receipt`

Each input artifact must strictly conform to its declared operad color contract as specified in [`meta-operad-verifier`](../meta-operad-verifier/SKILL.md).

## Operational Transformation Workflow

1. **Type & Color Check:** Assert that all supplied input artifacts exist and match declared source colors `Ledger, Audit`.
2. **Deterministic Evaluation:** Execute the domain-specific transformation or verification logic under `operads.application.ddc_execution.meta_operad_engine`.
3. **Residual Measurement:** Measure pre-execution residual $R_\text{before}$ and post-execution residual $R_\text{after}$.
4. **Output Emission:** Emit the target artifact of color `Receipt` to the designated output path.
5. **Evidence Trace Recording:** Append the run record (input/output hashes, timestamps, residual delta) to `evidence_trace.json`.

## Executable Verification CLI

Run this metaskill directly using its executable script:

```bash
python operads/skills/meta-residual-harmonic-optimizer/scripts/execute.py
```

Or invoke via the unified operad engine:

```bash
python -m operads.frontend.cli.meta_operad_cli meta-residual-harmonic-optimizer
```

## Residual Contract & Evidence Recording

All executions record an entry into `evidence_trace.json`. Per the repository residual-evidence bar, claiming an admitted contractive residual invariant requires **3 observed contractive runs** recorded with cryptographic digests. Absent 3 observed runs, the honest residual remains `unknown`.
