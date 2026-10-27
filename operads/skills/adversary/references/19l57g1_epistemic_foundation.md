# 19L57G1 Epistemic Foundation & Verification Invariants

This reference document details the formal derivation architecture, mathematical invariants, and multi-layer verification protocols established by the [`dbccpage/19L57G1`](https://github.com/dbccpage/19L57G1) repository (*"Forcing a universe without observers from nowhere"*), citing the sealed derivation tag `sealed-derivation-v1` (`3100c4e`) and its second-derivation research extensions.

**Scope.** The strict axiom set `{propext, Quot.sound}` described below is the Genesis repository's own rule (19L57G1 and material pinned to it). Elsewhere in this repository Lean 4 work may also use `Classical.choice`.

---

## 1. Epistemic Genesis & The Opaque Seed

`19L57G1` operates as a closed, blind formal derivation system starting from an opaque seed under externally imposed challenges without external research, prior target theories, or ungrounded assumptions.

```text
                                 [OPAQUE SEED]
                                       │
                                       ▼
                     [Primitive Difference Distinction]
                                       │
                 ┌─────────────────────┴─────────────────────┐
                 ▼                                           ▼
      [Reading L (Lexical/Sequence)]            [Reading F (Functional/Graph)]
                 │                                           │
         3 Minima Classes                            5 Non-Isomorphic Minima
      + Countable Arity Ties                                 │
                 │                                           │
                 └─────────────────────┬─────────────────────┘
                                       ▼
                       [Cost-Two Minimum Floor: μ₁ = 2]
                                       │
                         [Pair-Separation Quotient]
```

### Core Genesis Invariants
1. **The Cost-Two Minimum Response Floor ($\mu_1 = 2$):**
   At the first challenge point where the system must respond, **the formal structure does not dictate a unique answer**. The minimum structural response costs two items in both surviving readings ($\mu_1 = 2$).
2. **Tied Minima Structure:**
   - **Reading L (Lexical / Sequence):** Three non-isomorphic classes within declared bounds, accompanied by a countably infinite tie family indexed by arity.
   - **Reading F (Functional / Relational Graph):** Exactly five non-isomorphic structural minima within declared bounds.
   - Selecting a single minimum requires declaring a further external measure; a declaration is not a derivation.
3. **Anti-Smuggling & Refused Outside Grid:**
   The derivation enforces strict vocabulary and structural firewalls. When outside classification grids (e.g. nine-slot letter grids) were offered, the author recorded an explicit refusal: the names of the primitive-difference inventory remain repository-native. Any claim of independent convergence with an external architecture's slot grid is rejected by construction.

---

## 2. Dual Interpretation Regimes (Reading L vs Reading F)

The derivation maintains two surviving readings of the seed challenge text without internal contradiction:

| Property | Reading L (Lexical / Sequence) | Reading F (Functional / Graph) |
| :--- | :--- | :--- |
| **Carrier Topology** | 1D linear ordered sequence carrier | Directed acyclic relational carrier (DAG) |
| **Minima Structure** | 3 non-isomorphic classes + arity tie family | Exactly 5 non-isomorphic structural minima |
| **Branching Behavior** | Combinatorial sequence augmentation | Morphism-preserving relational extensions |
| **Closure Policy** | Orbit-quotiented pair separation (`supply=False`) | Dual genesis DAG replay under graph isomorphism |
| **Symbol Game Analog** | Linear token stream / cochain sequence | Operadic network / DAG causal interaction web |

Neither regime can be discarded a priori without introducing external bias. Both are preserved under a unified pair-separation quotient.

---

## 3. Four-Layer Mutual Verification Architecture

To prevent epistemic circularity, self-deception, or silent regressions, no single layer is evaluated in isolation. Every layer produces deterministic artifacts audited by adjacent layers:

```text
  Python Core (code/) ──deterministic──▶ artifacts/*.json ──regeneration──▶ byte-identical?
          │                                      ▲
          │ implements                           │ cited by
          ▼                                      │
    Claim Ledger ◀────────names───────── Lean Theorems ──#print axioms──▶ Axiom Inventory
          │                                      │                               │
          │ every citation                       │ every module                  │ every report
          ▼                                      ▼                               ▼
  Resolution Gate                         Census Pin                      Whitelist Audit
```

1. **Layer 1: Computational Object Language (`code/`)**
   - 60 typed source files implementing primitives (`model.py`), observation contexts (`observe.py`), candidate deltas (`candidates.py`), graph isomorphism (`iso.py`), execution engine (`engine.py`), and deterministic serialization (`export.py`).
   - Strict determinism: zero unseeded floats, zero timestamps, and canonical key sorting.
2. **Layer 2: Deterministic JSON Artifacts (`artifacts/*.json`)**
   - 40 deterministic JSON exports plus 6 full gzipped trees (`.json.gz`).
   - Regenerated on every verification pass; `ci/compare_artifacts.py` catches drift in both directions (uncommitted generated data vs. unregenerated committed data).
3. **Layer 3: Mechanized Proof Kernel (`lean4/Derivation/`)**
   - 75 Lean 4 modules: 63 in `Derivation.lean`'s import closure, and 12 parked modules audited separately via `lean4/ParkedAudit.lean`.
   - **Axiom Whitelist Enforcement:** Every declaration resolves strictly within:
     $$\operatorname{Axioms} \subseteq \{\text{propext}, \text{Quot.sound}\}$$
   - Rejects ungrounded `sorry` placeholders, `admit`, `unsafe`, `partial`, and `Classical.choice`. All 1530 axiom reports are verified.
4. **Layer 4: Pinned Claim Ledger (`paper/paper_claim_ledger.md`)**
   - 140 stable `CL-*` claim headings mapping every claim to its Python artifact key, automated test name, Lean theorem, and empirical falsifier.

---

## 4. The Twelve Deterministic Gate Families

The repository enforces twelve formal gate families to prevent unverified drift:

| Gate | Name | Verification Action |
| :--- | :--- | :--- |
| **1** | **Prompt Byte-Identity** | `ci/check_prompt_hashes.py`: Verifies byte-level identity against frozen seed prompt hashes. |
| **2** | **Transport Citations** | `ci/check_transport_citations.py`: Ensures transport-document citations bind to Lean source declarations. |
| **3** | **Dual 95% Coverage Gate** | `ci/check_coverage.py`: Requires line coverage $\ge 95\%$ (measured $\ge 99.10\%$) and branch coverage $\ge 95\%$ (measured $\ge 96.71\%$) across 787 tests. |
| **4** | **Strict Typing (mypy)** | `python -m mypy`: Full strict-mode typing with zero untyped `Any` across Python source. |
| **5** | **Artifact Regeneration** | `ci/compare_artifacts.py`: Asserts 40 JSON exports regenerate byte-for-byte identically. |
| **6** | **Lean Build & Axiom Whitelist** | `ci/check_lean_audit.py` & `ci/check_declaration_axioms.py`: Confirms full Lake elaboration and axiom whitelist `{propext, Quot.sound}` across all compiled constants. |
| **7** | **Skill Hygiene** | `ci/check_skills.py`: Verifies skills are well formed and declare `AuthorityEffect: None`. |
| **8** | **Paper Cross-References** | `ci/check_paper_citations.py`: Verifies every referenced `paper/*.md` path resolves. |
| **9** | **Ledger Evidence Resolution** | `ci/check_ledger_evidence.py`: Verifies all 140 `CL-*` claim evidence bindings resolve. |
| **10** | **Parked-Module Census** | `ci/check_parked_audit.py`: Ensures every unimported module under `lean4/Derivation/` is audited in `ParkedAudit.lean`. |
| **11** | **Research Tree Custody & Rungs** | `ci/check_tree_custody.py`: Audits registered research trees and enforces the second-derivation rung contract. |
| **12** | **Prose Watchlist Census** | `ci/check_prose_watchlist.py`: Verifies prose digests match pinned snapshots. |

---

## 5. Research Trees & Second-Derivation Rung Architecture

Beyond the sealed first derivation, new theoretical investigations proceed under strict **Second-Derivation Rung Contracts**:

1. **Rung Scoping Boundary:**
   - A second-derivation rung is scoped to `research/second/SEED.md` and its dedicated directory `research/second_<rung>/`.
   - It hand-edits nothing outside its declared write root except its registration in the workflow `.github/workflows/verify.yml`.
2. **Generated View Synchronization:**
   - After committing its tree and workflow registration, a rung regenerates all generated views:
     - `ci/research_index.py --write`
     - `ci/lookup_indexes.py --write`
     - `ci/lean_build_order.py --write`
     - `ci/check_tree_custody.py --write`
3. **Bar on Self-Excused Failures:**
   - The tree custody pin (`ci/tree_custody_pin.json`) may record the new rung's passing verifier, but never an entry under `expected_failures`. A rung whose verifier fails is not registered until it passes.

---

## 6. Receipt-Before-Payload & Local Verification Invariant

1. **Receipts Do Not Establish Truth:**
   - Cryptographic hashes, test green-lights, and parser passes verify execution provenance under declared inputs; they do not establish mathematical validity or authorize unearned semantic claims.
2. **Rejection of Hosted CI:**
   - The estate relies exclusively on locally reproducible receipts. Hosted third-party CI is permanently barred to eliminate dependency on external opaque runners and prevent superficial green-wash passes.
3. **Adversary Operational Binding:**
   - Adversary refuses any candidate turn or proof claim that lacks an explicit, reproducible receipt envelope, demanding exact witness packages over $\mathbb{Q}$ and fresh SHA-256 evidence digests before issuing `PASS_TO_MASTER`.
