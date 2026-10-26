# 02. Surviving Ideas Ledger: PFP & CEC

**AuthorityEffect:** `None`  
**Estate:** `omega_engine_education/documentation/004_oepfp/docs/` (historically `ow/omega_engine_pfp_v0.2/04_pfp_cec/`, which no longer exists)  
**Parent Document:** [`README.md`](README.md)  
**Status:** Canonical Filtration Ledger  

> **Source check (2026-10-20, pin `c419cc6beb`).** This ledger records dispositions of ideas. A disposition is not a machine gate: no code reads these entries, and an `ADMIT` row does not mean the idea is implemented. Current status of the implementation claims below:
>
> | Entry | Claim in the ledger | What source shows at the pin |
> | --- | --- | --- |
> | A-1 | SymSys-36 surface codec | No code names SymSys-36. The current minimal wire alphabet in [01](01_digest_and_canonical_serialization.md) has 38 glyphs (`a-z`, `0-9`, `<`, `>`). The round-trip parser test is still a next test. |
> | B-1 | "Directly implemented in sovereign Rust solvers" | A finite cochain carrier exists: `PromptCellComplex` and `to_exact_complex` in [cochain.rs](../../../../omega_engine/crates_rs/omega_symbol_game_runtime/src/cochain.rs) (lines 44-176), over exact `BigRational`. No contraction benchmark was found. |
> | B-2 | 10,000-complex property test | Not found; still a next test. |
> | B-3 | Admitted as `GTFOC-CHECK-01` | The identifier appears only in this ledger and in a skill reference index (`panep-math-and-physics-prof/references/spine_index.md`); no checker carries it. |
> | C-1 | Four-field kernel `packet_id`, `contract_digest`, `task_digest`, `payload` | The current [packet_envelope_v2.schema.yaml](../../../../omega_engine_pfp/infrastructure/yaml/schemas/packet_envelope_v2.schema.yaml) requires 18 fields and has no `contract_digest` or `task_digest`. Read C-1 as a historical design, not the current schema. |
> | D-2 | 2-colored operad toy fixture in Lean 4 | Not checked in this pass. |

---

## 1. Purpose & Revision-Open Posture

This ledger tracks research ideas, architectural proposals, and mathematical analogies evaluated under the **Fail-Closed Filtration Gate**. Ideas that clear admission criteria survive here with explicit hedges, corpus links, and next test obligations. Ideas that fail are refused with typed reasons.

### Standing Principle: Nothing Is Fixed For Life
The Symbol Game and Context Extension Calculus (CEC) were invented before the full mathematical spine was completed. They remain **revision-open**:
* **Grammar & Packets:** Can be redesigned if a cleaner discrete carrier yields smaller residuals.
* **MSS-$k$ Hierarchy:** Can be rebuilt from the reconstruction spine and genesis foundations.
* **Pipeline Gates:** Can be reshaped if a cleaner monadic or cochain structure fits.
* **External Analogies (operads, sheaves, physics):** Treated strictly as **heuristics and research programs**, never as automatic claim promotions.

---

## 2. Surviving Ideas Catalog

Below is the structured ledger of research ideas across five core technical zones.

---

### Zone A: Surface Codecs & Minimal Symbol Systems (SymSys / MSS)

#### Entry A-1: `SymSys-36 Surface Codec`
* **Classification:** `USEFUL BUT UNSAFE SOURCE NOTE`
* **Core Idea:** A 36-token surface alphabet combining delimiters, operators, and state indices.
* **Evaluation:** Useful as an experimental wire representation, but prose conflated surface token count with context depth.
* **Disposition:** Admitted as a concrete candidate codec under Axis 1 only. Strictly barred from claiming higher context depth ($d(C)$).
* **Next Test:** Bounded parser test asserting round-trip fidelity over valid expressions.

#### Entry A-2: `GDP-0 Genesis Difference Presentation`
* **Classification:** `ADMIT (Research Programme)`
* **Core Idea:** The minimal presentation regime that can register and preserve one witnessed, non-self-resolving difference without importing uncontracted object-language syntax.
* **Evaluation:** Clears all 5 criteria. Essential ground-state definition ($L_0$).
* **Disposition:** Admitted as canonical foundation.
* **Next Test:** Lean 4 formalization of nullary difference non-entailment.

#### Entry A-3: `MSS-k Expressivity Tower`
* **Classification:** `ADMIT (Research Programme)`
* **Core Idea:** Staged hierarchy of symbolic systems where level $k+1$ is reached only after level $k$ is certified exhausted.
* **Evaluation:** Formulates OESOS Rule 2 in discrete symbol systems.
* **Disposition:** Admitted. Requires explicit conservative extension proofs between stages.
* **Next Test:** Constructing finite exhaustion certificates for $k=0 \to k=1$.

---

### Zone B: Quotient Obstruction Calculus & Cohomology

#### Entry B-1: `Discrete Cochain Complex (C^0 -> C^1 -> C^2)`
* **Classification:** `ADMIT (Research Programme)`
* **Core Idea:** Mapping symbolic discrepancies to 1-cochains, repairs to 0-coboundaries, and integrability defects to 2-cochains.
* **Evaluation:** Clears all criteria. Directly implemented in sovereign Rust solvers.
* **Disposition:** Admitted as core mathematical foundation.
* **Next Test:** Exact rational matrix contraction benchmarks in `omega_symbol_game_runtime`.

#### Entry B-2: `LP Duality for L1 Residual Minimization`
* **Classification:** `ADMIT (Research Programme)`
* **Core Idea:** Using linear programming duality to certify that a proposed repair attains the global minimum $L_1$ residual norm via zero duality gap.
* **Evaluation:** Mathematically sound, fully decidable over $\mathbb{Q}$.
* **Disposition:** Admitted. Governed by Theorem ENC-0114.
* **Next Test:** Property-based testing of dual feasibility witnesses across 10,000 random complexes.

#### Entry B-3: `Čech Contextual Obstruction Gate`
* **Classification:** `ADMIT (Research Programme)`
* **Core Idea:** Gluing local agent observations across overlapping contexts using Čech 1-cohomology.
* **Evaluation:** Provides rigorous multi-agent consensus without heuristic voting.
* **Disposition:** Admitted as `GTFOC-CHECK-01`.
* **Next Test:** Multi-agent patch reconciliation fixture in `omega_engine_operations`.

---

### Zone C: Packetization & Wire Protocols

#### Entry C-1: `Four-Field Packet Kernel`
* **Classification:** `ADMIT (Research Programme)`
* **Core Idea:** Binding every transmission to `packet_id`, `contract_digest`, `task_digest`, and `payload`.
* **Evaluation:** Eliminates uncontracted conversational drift; enforces strict hash-chain provenance.
* **Disposition:** Admitted as the SGPP v2 design of its time. Superseded: the current envelope schema does not carry `contract_digest` or `task_digest` (see the source check above).
* **Next Test:** JSON schema validation gate integration in CLI runners.

#### Entry C-2: `Unrestricted Natural Language Packet Wrapper`
* **Classification:** `REFUSE`
* **Core Idea:** Wrapping unconstrained free-form conversational chat in JSON envelopes and claiming it constitutes a formal calculus.
* **Refusal Reason:** **Semantic Laundering**. Putting JSON braces around unparsed natural language does not make it mathematically verifiable.
* **Next Test:** None. Blocked fail-closed.

---

### Zone D: Higher Mathematics & Type Theory

#### Entry D-1: `HoTT Identity Paths for Claim Equality`
* **Classification:** `ADMIT (Research Programme)`
* **Core Idea:** Treating claim equivalence between agent proposals as identity types (paths in a homotopy space), requiring a verified 2-cell deformation.
* **Evaluation:** Mathematically rigorous; prevents surface string matching from claiming semantic identity.
* **Disposition:** Admitted as advanced theoretical lens.
* **Next Test:** Prototype path-checker for candidate AST rewrites.

#### Entry D-2: `Higher Operad Algebra for Skill Composition`
* **Classification:** `HOLD`
* **Core Idea:** Modeling agent skill invocation as arrows in a colored operad.
* **Status:** Highly promising, but current implementations lack mechanized associativity proofs.
* **Disposition:** Held in research quarantine until toy proof kernel is provided.
* **Next Test:** 2-colored operad toy fixture in Lean 4.

---

### Zone E: Physical & Biological Analogies (Quarantined)

#### Entry E-1: `Higgs Mechanism Analogy for Mass Acquisition`
* **Classification:** `USEFUL BUT UNSAFE SOURCE NOTE`
* **Core Idea:** Analogizing obstruction mass $\Phi_1 > 0$ to gauge symmetry breaking and the Higgs mechanism.
* **Disposition:** Quarantined. May be used as an intuitive pedagogical metaphor in informal discussions, but strictly forbidden from entering formal theorem statements or paper claim ledgers.

#### Entry E-2: `Friston Markov Blankets for Agent Boundaries`
* **Classification:** `HOLD`
* **Core Idea:** Using active/sensory states to formalize agent epistemic boundaries.
* **Disposition:** Held pending mathematical definition of discrete variational free energy over finite cochain spaces.
