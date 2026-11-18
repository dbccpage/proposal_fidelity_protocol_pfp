---
name: goo-operational-pipeline-attestation-gate
description: "Check pipeline outcomes come from real runs, not caller booleans; exact rational guards; certificates verified."
status: canonical
operad_source_colours: ["State", "Contract"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
families: [governance, gate]
---

# goo-operational-pipeline-attestation-gate

**AuthorityEffect:** None. This gate refuses. It does not mint, promote, or alter doctrine.

## The single rule

> Attestations must represent reproducible operational pipeline execution traces (`PipelineTrace`, `SealedPipeline`), never superficial caller-provided boolean flags (`GuardAttestations`).

## Invariants

1. **Operational Trace Verification**: Pipeline outcomes require an active, deterministic pipeline execution trace rather than external boolean parameter pass-throughs.
2. **Exact Rational Residual Mass**: Residual mass guards ($g_3$) must evaluate via exact rational arithmetic or integer bounds, forbidding positive float tolerances that mask non-zero defects.
3. **Candidate Set Exhaustiveness**: Candidate set completeness ($g_5$) must be certified via explicit finite set bijections, never loose arithmetic cardinality inequalities.
4. **Active External Certificate Validation**: External witnesses and certificates must be actively parsed and evaluated, never accepted on declaration alone.

## Verification

```bash
# Execute end-to-end pipeline attestation integration suite
pytest code/tests/test_fda_pipeline_integration.py
```
