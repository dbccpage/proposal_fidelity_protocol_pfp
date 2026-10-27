# Mode 01: Hieroglyphics & Glyph Alphabets

**Mode ID:** 1  
**Cluster:** Cluster I: Carrier & Representation  
**AuthorityEffect:** None  

---

## 1. Overview & Operational Directive

Mode 01 enforces strict operational prose restriction: all prompt, state, and transition expressions must conform strictly to a declared glyph profile, grammar contract, or wire representation without supplementary explanatory prose. Alphabet restriction alone does not demonstrate the absence of semantic meaning; rather, it provides a machine-checked syntactic envelope and exact state transition trace.

Under Mode 01:
- Every turn emits exactly one valid glyph or sequence from the declared alphabet.
- Expressions must conform strictly to the selected glyph profile without conversational filler or natural-language commentary.
- Transitions must obey the declared finite state machine (such as the DDC eight-letter state machine: $\{E, R, C, I, \Lambda, D, M, T\}$).
- Verifiers operate fail-closed with exact glyph matching.

---

## 2. Canonical Contracts & Specifications in `003_minimal_symbol_system_n_mssn`

The authoritative contracts, wire representations, and grammar specifications for Mode 01 have been relocated to the normative Minimal Symbol System (MSS-N) documentation directory [`education/documentation/003_minimal_symbol_system_n_mssn/`](../../../../education/documentation/003_minimal_symbol_system_n_mssn/):

### Core Mode 01 Artifacts
- **Canonical Mode Contract:**  
  [`contracts/contract.yaml`](../../../../education/documentation/003_minimal_symbol_system_n_mssn/contracts/contract.yaml)  
  Defines the machine-checked contract schema for Mode 01, including entry preconditions, rules, failure modes (`Unregistered glyph emission`, `Syntax boundary breach`), winning condition, and fail-closed exact glyph matcher configuration.

- **Wire Representations & Dialect Inventory:**  
  [`wire_representations/wire_representations.md`](../../../../education/documentation/003_minimal_symbol_system_n_mssn/wire_representations/wire_representations.md)  
  Documents operational wire dialects, including:
  - **Tier H (Head-word notation):** Structured application signatures over extended alphabet $\Sigma_H = \Gamma_{38} \cup \{\text{whitespace}, \text{newline}, ',', '=', '+', '*', '-'\}$.
  - **Tier D (PFP Directives):** Directive assertions carrying formal role bindings over $\Sigma_D = \Gamma_{38} \cup \{\text{A-Z}, \text{whitespace}, '\_', '<', '>'\}$ with typed refusal tokens (`ERR_UNDECLARED_CARRIER`).
  - **The `mss-boundary-v1` Dialect:** Single-root pair-balanced boundary wire syntax with external codebook, slot bindings, and lossless source-byte recovery invariants.

---

## 3. Normative MSS-N Tower References

All symbolic representations, stage ladders, and rewriting engines referenced by Mode 01 are governed by the unified MSS-N documentation suite:

### Specifications & Reading Guides
- **Normative Specification Root:**  
  [`README.md`](../../../../education/documentation/003_minimal_symbol_system_n_mssn/README.md) — Unified normative specification for the Minimal Symbol System tower (MSS-0 through MSS-100), defining ontology, epistemic boundaries, and dual accounting.
- **Reading Guide & Retraction Fences:**  
  [`reading_guide.md`](../../../../education/documentation/003_minimal_symbol_system_n_mssn/reading_guide.md) — Architectural separation between grammar checks, evaluator evidence, licensed lifts, and execution permission.
- **Foundational Research Monograph:**  
  [From Pre-Genesis to MSS-N](../../../../../../atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_pre_genesis_to_mssn/paper.md) — Consolidated account of MSS-0 through MSS-100, conservative grammar growth, and simplicial cycle repair.

### Grammar & Rewriting
- **Formal BNF Grammar Specifications:**  
  [`grammar/`](../../../../education/documentation/003_minimal_symbol_system_n_mssn/grammar/) — Machine-verifiable grammar rules, and derivation prompt [`prompts/mssn_prompt.md`](../../../../education/documentation/003_minimal_symbol_system_n_mssn/prompts/mssn_prompt.md).
- **Rewriting Strategies & Notation Tiers:**  
  [`rewriting/rewriting_strategies_mssn_wire.md`](../../../../education/documentation/003_minimal_symbol_system_n_mssn/rewriting/rewriting_strategies_mssn_wire.md) — Conversion between natural language, AST, and wire representations.

### Stage Levels & Alphabet Ladders
- **Decomposed Stage Specifications:**  
  [`levels/`](../../../../education/documentation/003_minimal_symbol_system_n_mssn/levels/) — Detailed per-level stage specifications from ground level [`levels/level_00_ground.md`](../../../../education/documentation/003_minimal_symbol_system_n_mssn/levels/level_00_ground.md) through [`levels/level_100_open_horizon_and_release.md`](../../../../education/documentation/003_minimal_symbol_system_n_mssn/levels/level_100_open_horizon_and_release.md).
- **38-Symbol Ladder Insert:**  
  [`levels/level_insert_38_symbol_ladder_and_transfinite_forms.md`](../../../../education/documentation/003_minimal_symbol_system_n_mssn/levels/level_insert_38_symbol_ladder_and_transfinite_forms.md) — Alphabet ladder $\Gamma_{38}$ and transfinite symbolic forms.

### Normal Forms, Lean 4 Mechanization & Domains
- **Normal Forms Library:**  
  [`normal_forms/`](../../../../education/documentation/003_minimal_symbol_system_n_mssn/normal_forms/) — Normal form schemas including [`normal_forms/nf.mssn.yaml`](../../../../education/documentation/003_minimal_symbol_system_n_mssn/normal_forms/nf.mssn.yaml) and [`normal_forms/nf.representation.gnf.yaml`](../../../../education/documentation/003_minimal_symbol_system_n_mssn/normal_forms/nf.representation.gnf.yaml).
- **Lean 4 Proof Kernels:**  
  [`lean4/`](../../../../education/documentation/003_minimal_symbol_system_n_mssn/lean4/) — Formal Lean 4 mechanized proofs and carrier representations.
- **Domain Adaptations:**  
  [`domains/`](../../../../education/documentation/003_minimal_symbol_system_n_mssn/domains/) — Exploratory domain packages across physics, mathematics, computation, cosmology, ANSI SQL, and LLM boundary verification.
