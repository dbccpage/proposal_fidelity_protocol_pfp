---
documentation_contract: symbol-game-documentation/v1
title: "0_symbol_game_foundations: Foundations, Core Invariants & Architecture"
kind: grammar-reference
audience:
  - researchers
  - engineers
  - coding-agents
status: active
maturity: draft
claim_status: specified
authority_effect: "None"
source_paths:
  - education/documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/_archive/records/source_inputs_2026_09_25/monograph_direct/readme.md  # not found at source pin c419cc6beb (2026-10-20)
  - education/documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/_archive/records/source_inputs_2026_09_25/monograph_direct/core_invariants.md  # not found at source pin c419cc6beb (2026-10-20)
  - education/documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/_archive/records/source_inputs_2026_09_25/monograph_direct/oesos_symbol_game_lab_provenance.md  # not found at source pin c419cc6beb (2026-10-20)
  - education/documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/_archive/records/source_inputs_2026_09_25/monograph_direct/symbol_game_monograph.md  # not found at source pin c419cc6beb (2026-10-20)
prerequisites:
  - ../../../../atlas/coda_atlas/F004_papers/001_finite_obstruction_calculus/000_pre_genesis_to_mssn/paper.md
  - ../../001_oegen/genesis.md
aliases:
  - 0_symbol_game.md
  - 0_symbol_game
related:
  - ./meta_01_symbol_game_historical_curriculum.md
  - ./meta_02_symbol_game_pfp.md
  - ./meta_03_symbol_game_proof_ledger.md
  - ./README.md
last_verified: 2026-09-29
---

# 0_symbol_game_foundations: Foundations, Core Invariants & Architecture

**AuthorityEffect:** None.  
**Scope:** Canonical foundations, core boundary laws, two-object identity, and laboratory provenance for the Symbol Game and Proposal Fidelity Protocol (PFP).

---

## 1. Overview & Document Suite Structure

This monograph sequence condenses the Symbol Game and Paper 043 research estate into four direct, simple, and terse reference modules:

- **[`meta_00_symbol_game_foundations.md`](./meta_00_symbol_game_foundations.md) (This Document):** Foundations, the Two-Object Identity, the Four Disjoint Domains, the Tripartite Law, and provenance.
- **[`meta_01_symbol_game_historical_curriculum.md`](./meta_01_symbol_game_historical_curriculum.md):** The 22-Level Curriculum (Levels 0–21) spanning primitive distinction, discrete cochain complexes, weak LP duality, survivor zeta, and Regge metric deficits.
- **[`meta_02_symbol_game_pfp.md`](./meta_02_symbol_game_pfp.md):** Proposal Fidelity Protocol (PFP), packet envelopes, stealth cochains, $L_1$ projection, and execution chains.
- **[`meta_03_symbol_game_proof_ledger.md`](./meta_03_symbol_game_proof_ledger.md):** Formal Verification & Proof Ledger for all 50 Lean 4 theorem declarations in `Paper043.lean`.

---

## 2. The Two-Object Identity: Object A vs. Object B

Historical ambiguity arose from using the single moniker "The Symbol Game" for two differently scoped structures:

```text
+==================================================================================================+
|                                    THE TWO-OBJECT IDENTITY                                       |
|  OBJECT A: The Proposal Fidelity Protocol (PFP / Runtime Engine)                                |
|  - A verifier-relative software and protocol harness.                                            |
|  - Manages untrusted neural proposals, packetization, syntax validation, and local replay.       |
|  - Preserves declared fidelity fields while identifying semantically distinct source states      |
|    under the declared finite representation; the residual ledger records what the selected       |
|    representation does not preserve.                                                             |
|  - Emits residual loss ledgers and bounded laboratory evidence. Mints zero authority.           |
+--------------------------------------------------------------------------------------------------+
|  OBJECT B: The Minimal Symbol System (MSS-N / Mathematical Monograph)                            |
|  - A finite mathematical tower of progressive presentations (MSS-0 through MSS-100).            |
|  - Studies cochains C⁰ → C¹ → C², quotient obstructions Q¹, survivor zeta functions, and        |
|    exact discrete optimization over rational fields Q.                                           |
|  - Independent of machine learning models or runtime prompt engineering.                         |
+==================================================================================================+
```

---

## 3. The Four Non-Overlapping Domains

To prevent architectural bleed and category errors, all system components are partitioned into four disjoint domains:

| Domain | Primary Scope & Responsibilities | Governing Boundaries |
|---|---|---|
| **A. Symbol Game (PFP / SGPP)** | Proposal fidelity, packet envelopes, family syntax, AST replay, local check gates, detector adequacy, and typed refusal routing. | Runs inside runtime; identifies distinct states under representation; emits residuals. |
| **B. Minimal Symbol System (MSS-N)** | Finite mathematical tower of progressive presentations (MSS-0 through MSS-100): cochain complexes $C^0 \to C^1 \to C^2$, quotient obstruction $Q^1$, survivor homology $H^1$, lift contracts $\Lambda_n$, and naming pressure $\mathrm{NP}(n)$. | Pure discrete mathematics; exact rational arithmetic; zero opcodes. |
| **C. Context Extension Calculus (CEC)** | Protocol for proposing and auditing presentation transitions after scoped exhaustion. | Operates outside runtime; audits the 12 extension conditions. |
| **D. Authority / Omega** | Authority tokens, promotion fences, terminal/refusal taxonomies, and external verification gates. | Sovereign gate; local receipts never confer authority. |

### Canonical Naming & Namespace Invariant

The historical shorthand `CEC == MSS-N` is **permanently retired**, and naming pressure is designated $\mathrm{NP}(n)$ to prevent namespace collisions with the Genesis derivation:

$$\boxed{\text{Genesis } S(n) \;\neq\; \text{MSS-}N \;\neq\; \text{SG-}N}$$

The following identities are binding:
- $\boxed{\text{MSS-}N \equiv \text{The finite mathematical tower of progressive presentations}}$
- $\boxed{\mathrm{NP}(n) \equiv \text{The naming-pressure / level statistic of a declared tower segment}}$
- $\boxed{\text{SG-}N \equiv \text{The Proposal Fidelity Protocol game level}}$
- $\boxed{\text{CEC} \equiv \text{The Symbol Game context-extension governance workflow}}$

---

## 4. The Tripartite Non-Conflation Law

$$\boxed{\text{repair inside a frozen context} \;\neq\; \text{extend the representation} \;\neq\; \text{promote evidence or authorize action}}$$

1. **Repair ($\operatorname{EndRep}_{\mathcal{C}}$):** Same-level adjustment within the declared repair gauge $W = \operatorname{im}(d_0)$. Modifies slot values without altering the carrier set or cochain dimension.
2. **Extend ($\Lambda_n$):** Adjoining new carrier elements, cochain dimensions, or relations after exhausting same-level repair. Requires formal satisfaction of the 12 extension audit conditions.
3. **Promote / Authorize ($\Omega$):** Moving an object across the authority firewall. Model output, packet admission, local replay, and zero residuals never authorize external actions.

---

## 5. Epistemic Quarantine & The Exact/Certified Arithmetic Law

$$\boxed{\text{No uncertified floating-point authority}}$$

1. **Carrier Representation Honesty:** Verification carriers use explicitly declared exact or certified representations—e.g., integers, rationals $\mathbb{Q}$, finite fields $\mathbb{F}_p$, algebraic extensions ($\mathbb{Q}(i)$, $\mathbb{Q}(\sqrt{2})$), real algebraic-number encodings, or validated interval enclosures $[x_{\mathrm{lo}}, x_{\mathrm{hi}}]$.
2. **Exact/Certified Arithmetic Law:** Uncertified binary floating-point values (`f32`, `f64`) may not serve as authoritative proof witnesses. All referee decisions operate on declared exact representations or outward-rounded certified interval enclosures.
3. **Quarantine of Spectral Projections:** Spectral metrics, graph zeta functions, and continuum analogies remain encapsulated as diagnostic probes; they do not alter carrier states.
4. **Receipt Replayability:** Every terminal verdict requires an immutable, replayable receipt with code status, Lean status, and residual matrix.

---

## 6. Laboratory Provenance & Source Anchors

- **Author & Lineage:** Jeremy H. Carroll, 2026-07 through 2026-09, consolidating the Proposal Fidelity Protocol, Paper 043, and the MSS-N curricular sequence.
- **Sealed Anchor:** The foundational derivations cite the immutable commit tag `sealed-derivation-v1` (`3100c4e`, 2026-08-17).
- **Formal Core:** Lean 4 mechanization was recorded as residing in `Paper043.lean` (compiled under 2,974 Lake jobs with 50 public theorems, documented in [`meta_03_symbol_game_proof_ledger.md`](./meta_03_symbol_game_proof_ledger.md)). That is a historical record (last verified 2026-09-29). See the 2026-10-20 status in the proof ledger: no `Paper043.lean` exists at the source pin, and several of the Paper 043 Lean files do not elaborate.
- **Authority Directive:** AuthorityEffect is strictly `None` across all modules.

---

## 7. Claim Hygiene Quadrant

1. **What this supports:**
   - Formal architectural definition of the Proposal Fidelity Protocol (PFP), Two-Object Identity, and the Tripartite Non-Conflation Law.
   - Exact separation between the untrusted proposal runtime (Object A) and the operadic specification hierarchy (Object B).
2. **What this does not support:**
   - Does not establish physical continuum emergence or continuous field theories from discrete models.
   - Does not assert external operational authority for laboratory game verifications.
3. **The narrowest defensible claim:**
   - PFP specifies deterministic host verification of candidate turns against frozen boundary invariants. The numbered level referees are specifications; none is implemented at source pin `c419cc6beb` (2026-10-20).
4. **Next test needed:**
   - Verify invariant preservation across all 101 stage envelopes and test fixtures.
