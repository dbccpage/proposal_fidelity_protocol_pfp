---
name: auto-obstruction-hunter
description: "Scan code and monographs at levels from sentence to math spine for structural, schema and mathematical non-fits."
invocation: discipline
operad_source_colours: ["State", "Audit"]
operad_target_colour: "Receipt"
operad_arity: 2
operad_residual: "unknown"
families: [meta, obstruction, techne, panepistimion]
---

# auto-obstruction-hunter

**AuthorityEffect: None.** Obstruction scanning and diagnostic reporting engine for `auto-obstruction-hunter`. Detects where code, prose, schemas, or mathematical models do not fit. Triggers on "obstruction hunter", "find obstructions", "obstruction sweep", "where does it not fit".

---

## Multi-Scale 10-Level Abstraction Hierarchy

Scans across 10 granular levels of abstraction:

```text
[Level 0: Sentence / Character]      Uppercase file names, non-snake_case, syntax typos
[Level 1: Paragraph / Linter Block]  Claim ID bijection errors, markdown lint failures
[Level 2: Section / Docstring]       Smuggled observers, Genesis Bias, Primitive Difference defects
[Level 3: Paper / Monograph]         13-section skeleton gaps, claim ledger incompleteness
[Level 4: Code File / Module]        Import drift, contract layer firewall breaches
[Level 5: Class / Struct]            Pydantic v2 schema drift, Rust struct layout mismatch
[Level 6: Method / Function]         Signature mismatch, non-invertibility, unhandled error paths
[Level 7: Unit Test / Property]      Mock-only trivial tests, weak assertions, un-mutated failure paths
[Level 8: Research Program]          Domain drift, disconnected papers, missing cross-references
[Level 9: Mathematical Spine]        Algebra -> Geometry -> Calculus -> DiffEq -> Hamiltonians -> QM ->
                                     Feynman -> QCD -> M-Theory -> Category Theory -> Topos -> HoTT
```

---

## 1. Unified 4-Stage Obstruction Hunt Protocol

When invoked as `/auto-obstruction-hunter <target_path | scope | all> [--level 0..9]`, execute the following 4 stages:

```text
[Stage 1] Multi-Level Abstraction Scan
          │ Scans target locus across Levels 0 through 9 for structural, naming, and schema defects
          ▼
[Stage 2] Mathematical & Obstruction Spine Reconciliation
          │ Routes atlas reconciliation through governance-wdp & searches research library for missing math lifts
          │ Maps obstruction to PO-000..PO-009 (Projection Obstruction Theory)
          ▼
[Stage 3] Obstruction Diagnostic & Repair Proposal
          │ Generates detailed Obstruction Diagnostic Report showing exact non-fit locations
          ▼
[Stage 4] Lean 4 Obligation & Test Patch Emission
          │ Emits formal Lean 4 theorem obligations under lean4/ and Python test patches
```

---

## 2. Constituent Domain Skills

- [`panep-math-and-physics-prof`](../panep-math-and-physics-prof/SKILL.md) — Chair of Projection Obstruction Theory.
- [`governance-wdp`](../governance-wdp/SKILL.md) — Governance coverage for the existing Rust reconciliation engine `core_atlas_reconciliation`.
- [`auto-symmetry-hunter`](../auto-symmetry-hunter/SKILL.md) — Cross-skill & cross-agent invariant detector.
- [`lib-master-librarian`](../lib-master-librarian/SKILL.md) — O(1) FTS5 research library search engine.

---

## 3. Sovereign Governance Rules

- **Authority Ceiling:** `AuthorityEffect: None`. Detects obstructions, non-fits, and missing mathematical lifts; human promotion approves PROD changes.

## Mandatory De-Linting & Encoding Cleanliness (`RULE_MARKDOWN_DELINTING_001`)

Every file created or modified during the execution of this skill MUST be de-linted prior to turn completion. Run `/techne-docs-lint-hunter-killer` or `npx markdownlint-cli --fix` to verify **0 linter errors and 0 linter warnings**, and ensure no CP437/Windows-1252 Mojibake character artifacts remain (`RULE_UTF8_MOJIBAKE_CLEANLINESS_001`).
