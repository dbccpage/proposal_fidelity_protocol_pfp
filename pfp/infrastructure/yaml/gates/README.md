# Proposal Fidelity Protocol (PFP) Gates Directory

**AuthorityEffect:** None.  
**Scope:** `documentation/030_the_symbol_game_proposal_fidelity_protocol_pfp/gates/`

---

## 1. Directory Structure

- [`01_cold_syntax.yaml`](01_cold_syntax.yaml) through [`22_hardware_constraint.yaml`](22_hardware_constraint.yaml): The 22 Primary Panel Verification Gates matching Adversary's panel.
- [`intergates/`](intergates/README.md): Exhaustive 10-element Intergate transition register governing cognitive vectors (Flow, Surprise, Anti-Sycophancy, Reversible Play, Anti-Urgency, De-escalation, Independent Witnessing).
- [`empirical/`](empirical/README.md): Quantitative Empirical Benchmark Gates (`PFP-EMP-GATE-*`) evaluating token amortization, injection containment, and e-graph preservation assertions.

---

## 2. Claim Hygiene Summary

1. **What it supports**: Formal index of primary gates, intergate transition dynamics, and empirical benchmark gates for the PFP / Adversary Swarm.
2. **What it does not support**: Does not replace compiled Rust verification binary gates (`core_certifiers`).
3. **Narrowest defensible claim**: Declarative YAML gate contracts define the operational and empirical boundaries verified by executable test suites and checker receipts.

## Typed Contracts

- [`gate_types.py`](gate_types.py): Typed gate register: `PrimaryGate` (22), `Intergate` (10), `EmpiricalGate` (3), `ComparisonOperator`, `GateRegister`.
- [`gate_register.yaml`](gate_register.yaml): Register data matching the Pydantic model.
