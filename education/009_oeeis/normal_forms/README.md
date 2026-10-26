---
documentation_contract: symbol-game-documentation/v1
title: "Normal Forms & Canonical Form Contracts — Epistemic Immune System (EIS)"
kind: normal-form-index
status: active
maturity: production
evidence_grades:
  named: true
  syntax: true
  computed: true
  Lean: false
  gated: true
authority_effect: "None"
canonical_source: omega_engine_education/documentation/014_normal_forms/contracts_normal_forms/
last_verified: 2026-10-05
---

# Normal Forms & Canonical Form Contracts — Epistemic Immune System (EIS)

**AuthorityEffect:** None.\
**Canonical Source:** [`omega_engine_education/documentation/014_normal_forms/contracts_normal_forms/`](../../014_normal_forms/contracts_normal_forms)

---

## Architectural Taxonomy: True Normal Forms vs. Extended Form Contracts

In accordance with [`normal_form_foundational_definitions.md`](../../014_normal_forms/contracts_normal_forms/normal_form_foundational_definitions.md) and [`standard.yaml`](../../014_normal_forms/contracts_normal_forms/standard.yaml), contracts in the Epistemic Immune System domain are evaluated against the four foundational pillars of normalization:

1. **Relational Database Normal Forms (`qualifies_as_true_normal_form: true`):**
   - Strictly satisfy relational project-join decomposition or functional/multivalued dependency preservation theorems (1NF–6NF, BCNF, ETNF).
   - Decompositions must demonstrate lossless natural join reconstruction without spurious tuples.

2. **Extended / Canonical Form Contracts (`qualifies_as_extended_form: true`, `qualifies_as_true_normal_form: false`):**
   - Provide concrete domain normalization: **anomaly exclusion**, **canonicalization**, **invariant preservation**, and **typed terminal routing decisions**.
   - Model antigen pattern matching, central tolerance negative selection, two-signal activation, and regulatory suppression where reconstruction is defined via firewall filtering, causal witness verification, and loss ledgers rather than flat relational project-join theorems.
   - All contracts in this module operate as robust extended form contracts.

---

## Contracts in This Domain

| ID | Name | Short | Form Category | Family | Relevance & Invariant |
|---|---|---|---|---|---|
| [`nf.epistemic.enf`](./nf.epistemic.enf.yaml) | Epistemic Normal Form | ENF | Extended Form Contract | epistemic | Epistemic purity: strictly verifies that assertions hold explicit ground evidence, separating verified facts from untrusted claims. |
| [`nf.evidence.cdc`](./nf.evidence.cdc.yaml) | Causal Derivation Certificate | CDC | Extended Form Contract | evidence | Witnessed derivation: requires explicit causal chain links from input stimulus to emitted response, preventing ungrounded hallucination. |
| [`nf.evidence.loss_ledger`](./nf.evidence.loss_ledger.yaml) | Evidence Loss Ledger | LLNF | Extended Form Contract | evidence | Residual tracking: accounts for any omitted, compressed, or abstracted semantic details across immune filters. |
| [`nf.epistemic.odnf`](./nf.epistemic.odnf.yaml) | Observation Derivation Normal Form | ODNF | Extended Form Contract | epistemic | Multi-channel observer separation: enforces independent observer testimony, rejecting self-attesting singleton confirmations. |
| [`nf.security.efnf`](./nf.security.efnf.yaml) | Epistemic Firewall Normal Form | EFNF | Extended Form Contract | security | Perimeter gate: fail-closed admission filter enforcing payload validation, token limits, and typed refusal receipts. |

---

## Level-to-Contract Governance Mapping

| Level | Topic | Key Invariant & Mechanism | Governing Extended Form Contract |
| :--- | :--- | :--- | :--- |
| **Level 00** | Innate Pharmacy Barriers | Hard perimeter fences, schema validation, rate limits | [`nf.security.efnf`](./nf.security.efnf.yaml) (Fail-closed admission) |
| **Level 01** | Component Role Partitioning | Strict separation of Proposer, Reviewer, and Verifier | [`nf.epistemic.odnf`](./nf.epistemic.odnf.yaml) (Independent observer roles) |
| **Level 02** | Fixture Polarity & Near-Misses | Dual polarity verification: positive test and negative boundary check | [`nf.evidence.cdc`](./nf.evidence.cdc.yaml) (Exact witness bounding) |
| **Level 03** | Central Tolerance & Thymus Gate | Negative selection against self-reactive antibodies | [`nf.epistemic.enf`](./nf.epistemic.enf.yaml) (Self-spec protection boundary) |
| **Level 04** | Learned Guard Two-Signal Activation | Primary pattern match + co-stimulatory danger signal | [`nf.evidence.cdc`](./nf.evidence.cdc.yaml) & [`nf.security.efnf`](./nf.security.efnf.yaml) |
| **Level 05** | Independent Observation Support Policy | $k$-independent witness quorum before policy promotion | [`nf.epistemic.odnf`](./nf.epistemic.odnf.yaml) (Quorum witness consensus) |
| **Level 06** | Provisional Custody & Review Queue | Quarantine stage and probationary evaluation window | [`nf.evidence.loss_ledger`](./nf.evidence.loss_ledger.yaml) (Probationary audit ledger) |
| **Level 07** | Clonal Selection & Affinity | Somatic hypermutation and binding affinity optimization | [`nf.epistemic.enf`](./nf.epistemic.enf.yaml) (Affinity metric normalization) |
| **Level 08** | Regulatory Supervision & Anergy | Treg-mediated suppression of hyperactive guards | [`nf.evidence.loss_ledger`](./nf.evidence.loss_ledger.yaml) (Anergy threshold logging) |
| **Level 09** | External Admission Boundary | Fail-closed external proposal firewall and typed refusal | [`nf.security.efnf`](./nf.security.efnf.yaml) (Typed refusal receipts) |
| **Level 10** | Antimorphism Polarity & Telemetry | Structured non-prose receipt emission and telemetry integrity | [`nf.evidence.cdc`](./nf.evidence.cdc.yaml) & [`nf.epistemic.enf`](./nf.epistemic.enf.yaml) |

---

## Claim Hygiene Quadrant

1. **What these contracts support:**
   - Formal anomaly exclusion, negative selection verification, and typed refusal routing across epistemic immune barriers.
2. **What they do not support:**
   - Do not claim relational project-join decomposition (`qualifies_as_true_normal_form: false`).
   - Do not grant operational execution authority (`AuthorityEffect: None`).
3. **The narrowest defensible claim:**
   - Each extended form contract isolates a specific adversarial vulnerability or epistemic leakage mode and verifies data invariants relative to declared immune policies.
4. **Next test needed:**
   - Run targeted property tests validating AST conformance between `eis_core.py` and these contract specifications.
