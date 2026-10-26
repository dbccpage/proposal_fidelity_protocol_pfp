---
documentation_contract: symbol-game-documentation/v1
title: "Normal Forms & Canonical Form Contracts — Prompt Civilization & Lamarckian Evolution"
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

# Normal Forms & Canonical Form Contracts — Prompt Civilization & Lamarckian Evolution

**AuthorityEffect:** None.\
**Canonical Source:** [`omega_engine_education/documentation/014_normal_forms/contracts_normal_forms/`](../../014_normal_forms/contracts_normal_forms)

---

## Architectural Taxonomy: True Normal Forms vs. Extended Form Contracts

In accordance with [`normal_form_foundational_definitions.md`](../../014_normal_forms/contracts_normal_forms/normal_form_foundational_definitions.md) and [`standard.yaml`](../../014_normal_forms/contracts_normal_forms/standard.yaml), contracts in the Prompt Civilization and Lamarckian Evolution domain are evaluated against the four foundational pillars of normalization:

1. **Relational Database Normal Forms (`qualifies_as_true_normal_form: true`):**
   - Strictly satisfy relational project-join decomposition or functional/multivalued dependency preservation theorems (1NF–6NF, BCNF, ETNF).
   - Decompositions must demonstrate lossless natural join reconstruction without spurious tuples.

2. **Extended / Canonical Form Contracts (`qualifies_as_extended_form: true`, `qualifies_as_true_normal_form: false`):**
   - Provide concrete domain normalization: **anomaly exclusion**, **canonicalization**, **invariant preservation**, and **typed terminal routing decisions**.
   - Model prompt lineage DAGs, Lamarckian genotype/phenotype updates, and evolutionary fitness ranking where reconstruction is defined via replay, mutation lineage folds, or Pareto dominance rather than flat relational project-join theorems.
   - All contracts in this module operate as robust extended form contracts.

---

## Contracts in This Domain

| ID | Name | Short | Form Category | Family | Relevance & Invariant |
|---|---|---|---|---|---|
| [`nf.derivation.pdnf`](./nf.derivation.pdnf.yaml) | Primitive Difference Normal Form | PDNF | Extended Form Contract | derivation | Mutation operator distinctness: every mutated prompt genotype must exhibit a witnessed difference relative to parent templates ($a \neq b$). |
| [`nf.derivation.rpnf`](./nf.derivation.rpnf.yaml) | Replay Provenance Normal Form | RPNF | Extended Form Contract | derivation | Prompt civilization lineage replay: $\text{generation}_{k} = \operatorname{fold}(\text{ancestor}, \text{mutations})$. Validates deterministic lineage replay from root prompts. |
| [`nf.derivation.scnf`](./nf.derivation.scnf.yaml) | Separation Cost Normal Form | SCNF | Extended Form Contract | derivation | Multi-objective Pareto selection: fitness minimizers and crowding distances require explicit cost measures without silent tie-breaking. |
| [`nf.derivation.sernf`](./nf.derivation.sernf.yaml) | Split Extension-Retraction Normal Form | SERNF | Extended Form Contract | derivation | Lamarckian retro-inheritance: phenotype feedback lift $u$ and genotype retraction $r$ satisfy split consistency $r(u(x)) = x$ on baseline specifications. |
| [`nf.evidence.provenance`](./nf.evidence.provenance.yaml) | Provenance Normal Form | PvNF | Extended Form Contract | evidence | Lineage taint and cryptographic hash chains: verifies causal ancestry and quarantine boundaries for defective or tainted generations. |

---

## Level-to-Contract Governance Mapping

| Level | Topic | Key Invariant & Mechanism | Governing Extended Form Contract |
| :--- | :--- | :--- | :--- |
| **Level 00** | Substrate & Packaging | Typed carrier schemas for genotypes, phenotypes, and individuals | [`nf.derivation.rpnf`](./nf.derivation.rpnf.yaml) (Quiescent root anchor) |
| **Level 01** | Lineage DAG & Causal Descent | Acyclic graph topology and causal ancestry verification | [`nf.evidence.provenance`](./nf.evidence.provenance.yaml) (Causal ancestry chain) |
| **Level 02** | Mutation Operators & Forge | Non-vacuous variation with positive witness count | [`nf.derivation.pdnf`](./nf.derivation.pdnf.yaml) (Witnessed irreflexive difference) |
| **Level 03** | Lamarckian Retro-Inheritance | Phenotype runtime reflection projected back to prompt text | [`nf.derivation.sernf`](./nf.derivation.sernf.yaml) (Split Retraction Invariant) |
| **Level 04** | Pareto Selection & Fitness | Non-dominated sorting over multi-objective cost metrics | [`nf.derivation.scnf`](./nf.derivation.scnf.yaml) (Explicit Separation Cost) |
| **Level 05** | Inverse Lineage PageRank | Downstream survival credit attribution without self-loops | [`nf.derivation.rpnf`](./nf.derivation.rpnf.yaml) & [`nf.derivation.scnf`](./nf.derivation.scnf.yaml) |
| **Level 06** | Precedent Retrieval & Evaporation | Pheromone decay and memory retrieval filters | [`nf.derivation.scnf`](./nf.derivation.scnf.yaml) (Distance metric calibration) |
| **Level 07** | Ecological Reserves & Population | Carrying capacity $K$ and niche preservation | [`nf.derivation.scnf`](./nf.derivation.scnf.yaml) (Crowding distance sorting) |
| **Level 08** | Lineage Taint & Invalidation | Fail-closed quarantine of descendant trees upon defect detection | [`nf.evidence.provenance`](./nf.evidence.provenance.yaml) (Taint propagation fence) |
| **Level 09** | Durable Event Log & Persistence | Append-only event ledger with SHA-256 hash chaining | [`nf.evidence.provenance`](./nf.evidence.provenance.yaml) & [`nf.derivation.rpnf`](./nf.derivation.rpnf.yaml) |
| **Level 10** | Open Horizons & Island Ecology | Multi-island migration and genetic drift boundaries | [`nf.derivation.sernf`](./nf.derivation.sernf.yaml) & [`nf.derivation.pdnf`](./nf.derivation.pdnf.yaml) |

---

## Claim Hygiene Quadrant

1. **What these contracts support:**
   - Formal anomaly exclusion, replay-certified prompt lineage descent, and typed terminal routing across Lamarckian evolutionary cycles.
2. **What they do not support:**
   - Do not claim relational project-join decomposition (`qualifies_as_true_normal_form: false`).
   - Do not grant operational execution authority (`AuthorityEffect: None`).
3. **The narrowest defensible claim:**
   - Each extended form contract isolates a specific structural mutation or ancestry anomaly and validates data invariants relative to declared prompt lineage parameters.
4. **Next test needed:**
   - Run targeted property tests validating AST conformance between `prompt_civilization_core.py` and these contract specifications.
