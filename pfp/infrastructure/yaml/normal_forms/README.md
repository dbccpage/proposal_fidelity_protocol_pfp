---
documentation_contract: symbol-game-documentation/v1
title: "Normal Forms & Canonical Form Contracts â€” The Symbol Game â€” Proposal Fidelity Protocol (PFP)"
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
canonical_source: omega_engine_education/documentation/13_normal_forms/contracts_normal_forms/
last_verified: 2026-09-29
---

# Normal Forms & Canonical Form Contracts â€” The Symbol Game PFP

**AuthorityEffect:** None.  
**Canonical Source:** [`omega_engine_education/documentation/13_normal_forms/contracts_normal_forms/`](../../13_normal_forms/contracts_normal_forms)

---

## Architectural Taxonomy: True Normal Forms vs. Extended Form Contracts

In accordance with [`normal_form_foundational_definitions.md`](../../13_normal_forms/contracts_normal_forms/normal_form_foundational_definitions.md) and [`standard.yaml`](../../13_normal_forms/contracts_normal_forms/standard.yaml), contracts in the Symbol Game / PFP runtime domain are evaluated against the four foundational pillars of normalization:

1. **True Normal Forms (`qualifies_as_true_normal_form: true`):**
   - Strictly satisfy relational project-join decomposition or functional/multivalued dependency preservation theorems (1NFâ€“6NF, BCNF, ETNF).
   - Decompositions must guarantee lossless natural join reconstruction without spurious tuples.

2. **Extended / Canonical Form Contracts (`qualifies_as_extended_form: true`, `qualifies_as_true_normal_form: false`):**
   - Provide concrete domain normalization: **anomaly exclusion**, **canonicalization**, **invariant preservation**, and **typed terminal routing decisions**.
   - Model cochain boundary quotients (GBQNF), query alternation budgets (QANF), bracket-string compilation (CPNF), envelope security fibrations (EFNF), and claim hygiene quotients (EQNF) where reconstruction is defined via compilation passes, proof witnesses, or boundary maps rather than flat relational project-join theorems.
   - The contracts listed below declare `qualifies_as_true_normal_form: false`; they operate as robust extended form contracts.

---

## Contracts in This Domain

| ID | Name | Short | Form Category | Family | Relevance & Invariant |
|---|---|---|---|---|---|
| [`nf.pfp.pfnf`](./nf.pfp.pfnf.yaml) | Proposal Fidelity Normal Form | PFNF | Extended Form Contract | coda | Central PFP contract: proposal $(u, r, \delta)$ enforces base retraction identity $r \circ u = \operatorname{id}_B$, bounded defect evolution $\Phi_1(P) \le \Phi_1(B) + \text{budget}$, and non-authoritative disposition. |
| [`nf.coda.eqnf`](./nf.coda.eqnf.yaml) | Epistemic Quotient Normal Form | EQNF | Extended Form Contract | epistemic | The Symbol Game's 4-point claim hygiene quad (supports / does not support / narrowest claim / next test). Excludes over-claiming and proof hype. |
| [`nf.coda.gbqnf`](./nf.coda.gbqnf.yaml) | Generalized Boundary-Quotient Normal Form | GBQNF | Extended Form Contract | change | Symbol Game runtime cochain defect tracking: $\omega$ exact iff repairable; tracks closed and open residual classes. |
| [`nf.compilation.cpnf`](./nf.compilation.cpnf.yaml) | Compilation Normal Form | CpNF | Extended Form Contract | compilation | Symbol Game bracket-string compilation pipeline: deterministic lowering from AST to bytecode. |
| [`nf.representation.tbnf`](./nf.representation.tbnf.yaml) | Token-Bounded Normal Form | TBNF | Extended Form Contract | representation | Tree-bracket encoding for the 38-character Symbol Game alphabet: $\{a..z, 0..9, <, >\}$. |
| [`nf.security.efnf`](./nf.security.efnf.yaml) | Epistemic-Fibration Normal Form | EFNF | Extended Form Contract | security | Envelope firewall for Symbol Game packet validation and dialect tag separation. |
| [`nf.evidence.certificate`](./nf.evidence.certificate.yaml) | Certificate Form | CertF | Extended Form Contract | evidence | Certificate normal form for Symbol Game verification receipts and receipt hash commitments. |
| [`nf.evidence.loss_ledger`](./nf.evidence.loss_ledger.yaml) | Loss Ledger Form | LLF | Extended Form Contract | evidence | Loss ledger normal form for tracking explicit structure loss across representation projections. |
| [`nf.logic.qanf`](./nf.logic.qanf.yaml) | Quantifier Alternation Normal Form | QANF | Extended Form Contract | experimental | Query-answer normal form for bounded quantifier alternation and induction budgets. |

| [`nf.experimental.qm_classical`](./nf.experimental.qm_classical.yaml) | Quantum-Classical Experiment Normal Form | QCNF | Extended Form Contract | experimental | Retains complete report, Bell or purification experiments with exact native replay and explicit carrier premises. |

---

## Domain-Specific Rationale

### `nf.pfp.pfnf` â€” Proposal Fidelity Normal Form
The load-bearing protocol contract of the Symbol Game. Eliminates counterfeit proposals, silent base state mutations, and unbudgeted defect inflation. Enforces base retraction invariance $r(u(b)) = b$ and receipt-bound disposition.

### `nf.coda.eqnf` â€” Epistemic Quotient Normal Form
The Symbol Game's 4-point claim hygiene quad (supports / does not support / narrowest defensible claim / next test needed). Excludes over-claiming, un-hedged proof language, and unauthorized authority assertions.

### `nf.coda.gbqnf` â€” Generalized Boundary-Quotient Normal Form
The Symbol Game runtime cochain defect tracking: $\omega$ is exact iff repairable. Partitions defects into exact gradients, closed residual obstructions, and open boundary violations.

### `nf.compilation.cpnf` â€” Compilation Normal Form
Symbol Game bracket-string compilation pipeline: validates deterministic syntax lowering without character loss or AST mangling.

### `nf.representation.tbnf` â€” Token-Bounded Normal Form
Tree-bracket encoding for the 38-character Symbol Game alphabet $\{a..z, 0..9, <, >\}$. Forbids un-escaped whitespace or out-of-alphabet tokens.

### `nf.security.efnf` â€” Epistemic-Fibration Normal Form
Envelope firewall for Symbol Game packet validation, maintaining strict boundary fences between nested sub-dialects.

### `nf.evidence.certificate` â€” Certificate Form
Certificate normal form for Symbol Game verification receipts, enforcing non-authority and independent replayability.

### `nf.evidence.loss_ledger` â€” Loss Ledger Form
Loss ledger normal form for tracking information-loss projections, requiring an explicit ledger whenever a schema conversion discards attributes.

### `nf.logic.qanf` â€” Quantifier Alternation Normal Form
Query-answer normal form bounding quantifier alternations ($\Sigma_k^0 / \Pi_k^0$) under an explicit induction budget.

---

## Claim Hygiene Quadrant

1. **What these contracts support:**
   - Rigorous anomaly exclusion, deterministic token-bounded serialization, and typed terminal routing across Symbol Game PFP runtime pipelines.
2. **What they do not support:**
   - Do not claim relational project-join decomposition theorems (`qualifies_as_true_normal_form: false`).
   - Do not mint operational execution authority (`AuthorityEffect: None`).
3. **The narrowest defensible claim:**
   - Each extended form contract isolates a specific structural anomaly and verifies data invariants relative to explicitly declared parameters (such as `induction_budget`, `38_token_alphabet`, or `defect_boundary`).
4. **Next test needed:**
   - Execute runtime pipeline tests against the PFP test suite to ensure evaluator compatibility with these contracts.

## Typed Contracts

- [`nf_domain_index.py`](../../../domain/normal_forms/nf_domain_index.py): Typed ten-contract index, including QCNF: `NfIndexEntry` (extended form, never a true normal form), `NfDomainIndex`, and the 38-character TBNF alphabet check. Missing, duplicated or unknown replacement contract identifiers are rejected.
- [`nf_domain_index.yaml`](nf_domain_index.yaml): Register data matching the Pydantic model.
