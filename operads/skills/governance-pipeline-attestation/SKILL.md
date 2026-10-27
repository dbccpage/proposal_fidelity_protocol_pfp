---
name: governance-pipeline-attestation
description: "Gate for operational pipeline attestation, exact pseudometric separation, probe firewall and receipt replay."
status: canonical
operad_source_colours: ["Code", "Contract"]
operad_target_colour: "Audit"
operad_arity: 2
operad_residual: "unknown"
families: [governance, pipeline-attestation, exact-math]
---

# governance-pipeline-attestation

`AuthorityEffect: None.`

## The Single Rule

> Verification pipelines must strictly separate operational execution traces from policy evaluations over caller attestations, maintain exact metric/pseudometric separation bounds, enforce a fail-closed firewall on probe defects, and verify cryptographic producer provenance upon receipt validation.

## Consolidated Invariants

1. **Operational Pipeline Attestation**: Policy evaluators over caller-supplied booleans (`GuardAttestations`) must never be conflated with operational pipeline runs that produced a terminal outcome. Residual mass guards ($g_3$) reject positive numerical float tolerances; candidate exhaustiveness ($g_5$) requires set bijections rather than count inequalities (`goo-operational-pipeline-attestation-gate`).
2. **Pseudometric Separation Discipline**: Distance bounds asserting $\operatorname{dist}(q(x), q(y)) \le 2\varepsilon$ at $\varepsilon=0$ cannot be promoted to point equality $q(x) = q(y)$ in pseudometric spaces where metric separation fails. The metric separation axiom must be declared, or claims must be strictly scoped to the metric quotient $Y/{\sim_0}$ (`goo-pseudometric-separation-claim-gate`).
3. **Probe Defect Firewall**: A malformed apparatus probe must raise an explicit exception immediately; it may never enter computational trichotomies as `STUCK` or be laundered into a valid result (`goo-probe-defect-firewall`, `goo-simulation-probe-error-defect-firewall`).
4. **Producer Hash Provenance**: Receipt validation must compare current on-disk producer script hashes against provenance recorded at generation time, preventing silent rebinding of modified producers without execution replay (`goo-producer-hash-provenance-gate`, `goo-receipt-replayability-gate`).
5. **Exact Rational Folding**: Discrete Hamiltonian and constraint solvers must execute rational sums by exact stepwise GCD-reduced folding rather than floating-point comparisons (`goo-exact-rational-fold-gate`, `goo-exact-rational-hamiltonian-solver-gate`).

## Verification Requirements

Run the consolidated pipeline attestation check:

```bash
python operads/skills/governance-pipeline-attestation/scripts/check_pipeline_attestation.py
```
