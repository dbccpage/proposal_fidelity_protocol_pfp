---
documentation_contract: symbol-game-documentation/v1
title: "1_symbol_game_historical_curriculum: Paper 043 Historical 22-Level Curriculum"
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
  - education/documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/_archive/records/source_inputs_2026_09_25/monograph_direct/symbol_game_monograph.md  # not found at source pin c419cc6beb (2026-10-20)
  - education/documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/_archive/records/source_inputs_2026_09_25/monograph_direct/0_monograph.md  # not found at source pin c419cc6beb (2026-10-20)
  - education/documentation/3_the_symbol_game_proposal_fidelity_protocol_pfp/_archive/records/source_inputs_2026_09_25/monograph_direct/21_monograph.md  # not found at source pin c419cc6beb (2026-10-20)
prerequisites:
  - ./meta_00_symbol_game_foundations.md
aliases:
  - 1_symbol_game.md
  - 1_symbol_game
related:
  - ./meta_00_symbol_game_foundations.md
  - ./meta_02_symbol_game_pfp.md
  - ./meta_03_symbol_game_proof_ledger.md
last_verified: 2026-09-29
---

# 1_symbol_game_historical_curriculum: Paper 043 Historical 22-Level Curriculum

**AuthorityEffect:** None.  
**Scope:** Technical summary of the historical 22-level monograph curriculum from Paper 043 (Levels 0–21).

> [!WARNING]
> **Historical Curriculum Notice:**  
> ```text
> This numbering is historical and does not identify levels with current MSS-N row indices.
> ```
> Modern MSS-N indexing (e.g. MSS-0 = zero-degree `<>` ground, MSS-1 = single-mark carrier) treats its progression as an externally designed atlas. Do not conflate or identify historical Paper 043 level numbers directly with modern MSS-0..21. A full crosswalk is provided in Section 3.

---

## 1. Master Curriculum Matrix (Historical Levels 0–21)

| Level | Primary Focus | Carrier Structure | Key Mathematical Invariant / Gate |
|:---|:---|:---|:---|
| **0** | Primitive Substrate | Distinction `<>`, operator `a>b` | Non-triviality requires at least 2 distinct terms; irreflexivity `¬(x R x)`. |
| **1** | Directed Cuts & Rigidity | Digraph $D_2$, alphabet $\{0, 1\}$ | Rigid automorphism $\operatorname{Aut}(D_2) = \{\mathrm{id}\}$; binary naming expansion. |
| **2** | Directed Graphs & Cochains | 2-step complex $C^0 \xrightarrow{d_0} C^1 \xrightarrow{d_1} C^2$ | Boundary maps $d_1 \circ d_0 = 0$; coboundary defects $\Phi_1 = \|[c]\|_{Q^1}$, $\Gamma_2 = \|d_1 c\|$. |
| **3** | Simplices & Weak Duality | Oriented triangles, incidence matrices | Exact LP weak duality over ordered field $\mathbb{Q}$: $c^\top x \le b^\top y$. |
| **4** | Presheaves & Noncongruence | Simplicial sets, presheaves | Context categories $\mathcal{C}$; failure of syntactic quotient congruence. |
| **5** | Lift Contracts & Naming | Contract $\Lambda_n$, statistic $\mathrm{NP}(n)$ | Monotone naming pressure; same-level exhaustion required before lift. |
| **6** | Tower & Survivor Zeta | MSS-N tower, spectrum $s_n$ | Survivor zeta function $\zeta_{\mathrm{surv}}(s) = \sum s_n n^{-s}$; terminal states. |
| **7** | Shifts & Extension Audit | De Bruijn graph $B(2, k)$, orbits | 12 extension conditions for valid context growth; bounded cycle length. |
| **8** | Adjoint Monads & Packets | Adjunction $F \dashv U$, 16 packet families | Unit $\eta: \mathrm{Id} \to UF$ and counit $\varepsilon: FU \to \mathrm{Id}$; $L_1$ stabilization. |
| **9** | Dagger Monads & Symmetry | Dagger category $\mathcal{C}^\dagger$, reflection | Adjoint involution $f^{\dagger\dagger} = f$; emergence of reflection symmetry. |
| **10** | Spectral Shadows & Quarantine | Adjacency spectrum $\lambda_i$, quarantine | Graph eigenvalues quarantined as diagnostic probes; zero state mutation. |
| **11** | ARS & Polygraphs | Abstract Rewriting Systems, 2-cells | Replayed declared critical peaks are joinable; local critical pair resolution. |
| **12** | DDA Event Records & Observer | Deterministic Dataflow Automata | Observer profile frozen prior to admission; replayable event ledgers. |
| **13** | Alternation & Fuel Bounds | Alternating quantifier ladders | Non-Turing completeness; bounded execution under a declared finite fuel budget. |
| **14** | MSS-15 R-B-G Proof Program | Tri-colour partition (Red-Blue-Green) | Four structural premises; strict color separation across boundary interfaces. |
| **15** | Authority Calculus & Fano | Fano plane $PG(2, 2)$, terminalization | Information-theoretic lower bounds; master terminalizer policy routing. |
| **16** | Filtered Ind-Objects | Ind-category $\operatorname{Ind}(\mathcal{C})$ | Colimits over finite approximations; directed systems of presentations. |
| **17** | Dialect Languages & Audits | Per-lift AST dialects | Lexical conformance audits; strict isolation between dialect versions. |
| **18** | Discrete Hodge Decomposition | Hodge Laplacian $\Delta = d \delta + \delta d$ | Orthogonal decomposition $C^1 = \operatorname{im}(d_0) \oplus \mathcal{H}^1 \oplus \operatorname{im}(d_1^*)$ over $\mathbb{Q}$. |
| **19** | Ihara-Ramanujan Zeta | Graph zeta $\zeta_G(u)$, Ramanujan bounds | Alon-Boppana spectral bound; quarantine against continuous field smuggling. |
| **20** | Autopoietic Cohomology | Self-referential cochains | Mandatory `GODEL_BREAK` on circular proofs; unprovable self-certificates. |
| **21** | Discrete 4D Regge Deficits | Simplicial manifolds, deficit angles | Deficit angle $\epsilon_h = 2\pi - \sum \theta$; discrete curvature without smooth metrics. |

---

## 2. Detailed Level Syntheses (Historical 0–21)

### Level 0: Primitive Substrate & Distinction Operator
- **Scope:** Starts from the void `<>` and declares the primitive mark.
- **Rules:** Two elements minimum; irreflexivity `¬(x R x)`.
- **Invariants:** Evaluated strictly over finite carriers; satisfies the Tripartite Law ($\text{repair} \neq \text{extend} \neq \text{promote}$).
- **Paper 043 Mapping:** Section I.1.

### Level 1: Directed Cuts, Rigidity & Binary Uplift
- **Scope:** Upgrades undirected pairs $S_2$ to directed cuts $D_2$.
- **Rules:** Automorphism group is trivial ($\operatorname{Aut}(D_2) = \{\mathrm{id}\}$), enforcing structural asymmetry.
- **Invariants:** Binary expansion over $\{0, 1\}$ provides unbounded identifier capacity.
- **Paper 043 Mapping:** Section I.2.

### Level 2: Directed Graphs & 2-Step Cochain Complex
- **Scope:** Carrier is a finite directed graph $G = (V, E)$.
- **Cochain Chain:** $C^0(V, \mathbb{Q}) \xrightarrow{d_0} C^1(E, \mathbb{Q}) \xrightarrow{d_1} C^2(T, \mathbb{Q})$.
- **Metrics:** Coboundary defect $\Phi_1 = \|[c]\|_{C^1/\operatorname{im}(d_0)}$ and cycle defect $\Gamma_2 = \|d_1 c\|_{C^2}$.
- **Paper 043 Mapping:** Section II.1.

### Level 3: Abstract Simplices & Exact LP Weak Duality
- **Scope:** Adds oriented 2-simplices (triangles) to cap cycles.
- **Theorem:** Weak LP Duality over linearly ordered fields: for any feasible $x \ge 0$ with $Ax \le b$ and $y \ge 0$ with $A^\top y \ge c$, $c^\top x \le b^\top y$. Weak duality gives the inequality; a zero gap, checked together with primal and dual feasibility, certifies that both vectors are optimal.
- **Paper 043 Mapping:** Section II.3 (`L043_07`).

### Level 4: Simplex Skeletons & Presheaf Semantics
- **Scope:** Finite simplicial sets and presheaf topoi.
- **Mechanics:** Context category $\mathcal{C}$; demonstrates that quotienting syntax does not automatically preserve observation congruence.
- **Paper 043 Mapping:** Section III.1.

### Level 5: Lift Contracts & Naming Pressure
- **Scope:** Formalizes the lift contract $\Lambda_n: \text{MSS-}n \to \text{MSS-}(n+1)$.
- **Mechanics:** Tracks naming pressure $\mathrm{NP}(n)$; forbids lifting until same-level repair is provably exhausted.
- **Paper 043 Mapping:** Section III.2 (`L043_10`).

### Level 6: MSS-N Tower, Survivor Zeta & Terminal States
- **Scope:** Assembles the infinite tower of finite stages $\text{MSS-}0 \to \text{MSS-}1 \to \dots$
- **Formulation:** Survivor sequence $s_n$ generates the formal Dirichlet series $\zeta_{\mathrm{surv}}(s) = \sum s_n n^{-s}$. *(Note, 2026-10-20: this is a different object from the survivor generating function of [Chapter 07](../math/07_math_filtered_diagrams_persistence_and_survivors.md), the Euler product $\prod_p (1 - z^{\deg p})^{-1}$ over primitive survivors. The two share a name only.)*
- **Paper 043 Mapping:** Section IV.1.

### Level 7: Shift Dynamics, De Bruijn Orbits & 12 Extension Conditions
- **Scope:** Word dynamics on De Bruijn graphs $B(2, k)$.
- **Audit Gate:** 12 explicit conditions (boundary preservation, acyclicity, cost non-negativity, etc.) required for context extension.
- **Paper 043 Mapping:** Section V.1.

### Level 8: Adjoint Monads & 16-Family Packet Catalog
- **Scope:** Categorical adjunction $F \dashv U$ over packet spaces.
- **Packet Families:** 16 discrete packet families with frozen schemas and typed boundary witnesses.
- **Paper 043 Mapping:** Section VI.1 (`L043_03`, `L043_05`).

### Level 9: Dagger Monads & Reflection Duality
- **Scope:** Introduces involutive dagger categories $\mathcal{C}^\dagger$.
- **Duality:** Reversible transitions satisfy $f^{\dagger\dagger} = f$; describes reflection symmetry on symmetric subcarriers (a definition-level statement, not a theorem).
- **Paper 043 Mapping:** Section VI.3.

### Level 10: Spectral Arithmetic Shadows & Epistemic Quarantine
- **Scope:** Eigenvalues of graph Laplacian matrices $\Delta$.
- **Quarantine:** Spectral bounds (e.g., Cheeger inequalities) are treated purely as external diagnostics; they never enter carrier state assertions.
- **Paper 043 Mapping:** Section VII.1.

### Level 11: Term Rewriting, ARS Confluence & 3-Polygraphs
- **Scope:** Abstract Rewriting Systems (ARS) over 2-cells.
- **Confluence:** Replayed declared critical peaks are joinable; resolves local critical pairs on closed boundaries without asserting global confluence or Newman's termination lemma.
- **Paper 043 Mapping:** Section VIII.1.

### Level 12: DDA Event Records & Operational Observer
- **Scope:** Deterministic Dataflow Automata (DDA).
- **Observer:** Observer filters are declared and immutable prior to packet replay; records are append-only.
- **Paper 043 Mapping:** Section IX.1.

### Level 13: Higher Alternation Ladders & Fuel Bounds
- **Scope:** Stratified quantifier alternation ($\Sigma_k, \Pi_k$).
- **Complexity Bound:** Execution paths terminate within declared finite fuel budgets; models remain strictly sub-Turing.
- **Paper 043 Mapping:** Section X.1.

### Level 14: MSS-15 R-B-G Proof Program & Four Premises
- **Scope:** Tri-partite carrier partition (Red, Blue, Green).
- **Premises:** Four formal separation premises are intended to ensure that cross-color interference cannot forge valid witness packets.
- **Paper 043 Mapping:** Section XI.1.

### Level 15: Authority Calculus, Fano Lower Bounds & Terminalization
- **Scope:** Combinatorial geometries (Fano plane $PG(2, 2)$).
- **Policy:** First-match terminalizer table routes packets into `ExactRepair`, `OpenObstruction`, or `Refused`.
- **Name note (2026-10-20):** the Fano plane $PG(2, 2)$ and Fano's inequality (see [`information_theoretic_limits.md`](../math/information_theoretic_limits.md)) are unrelated results that share a name.
- **Paper 043 Mapping:** Section XII.1 (`L043_08`).

### Level 16: Infinite SymSys Filtered Ind-Objects
- **Scope:** Categorical ind-completion $\operatorname{Ind}(\mathcal{C})$.
- **Structure:** Treats infinite systems strictly as filtered colimits of finite carrier presentations.
- **Paper 043 Mapping:** Section XIII.1.

### Level 17: Per-Lift Dialect Languages & Conformance Audits
- **Scope:** Dialect isolation between adjacent stages.
- **Conformance:** Verifies that no stage $n$ rule executes syntax reserved for stage $n+1$.
- **Paper 043 Mapping:** Section XIV.1.

### Level 18: Discrete Hodge Decomposition & LP Optimization
- **Scope:** Combinatorial differential forms over rational field $\mathbb{Q}$.
- **Decomposition:** Orthogonal splitting of 1-cochains into exact, co-exact, and harmonic subspaces: $C^1 = \operatorname{im}(d_0) \oplus \mathcal{H}^1 \oplus \operatorname{im}(\delta_1)$.
- **Paper 043 Mapping:** Section XV.1.

### Level 19: Ihara-Ramanujan Zeta Quarantine & Spectral Arithmetic
- **Scope:** Ihara graph zeta function $\mathbf{Z}_G(u) = \prod_{[C]} (1 - u^{|C|})^{-1}$.
- **Quarantine:** Alon-Boppana bounds and Ramanujan properties are verified as discrete algebraic invariants without continuum limits.
- **Paper 043 Mapping:** Section XVI.1.

### Level 20: Autopoietic Cohomology & Mandatory `GODEL_BREAK`
- **Scope:** Self-referential verification loops.
- **Safety Interlock:** Automated detection of circular proof loops triggers an immediate, unmaskable `GODEL_BREAK` refusal.
- **Paper 043 Mapping:** Section XVII.1.

### Level 21: Discrete 4D Regge Metric Deficits & Gauge Foundations
- **Scope:** Discrete simplicial geometries (Regge calculus).
- **Curvature:** Deficit angle $\epsilon_h = 2\pi - \sum \theta_h$ measures discrete curvature on bones without invoking smooth differential manifolds.
- **Paper 043 Mapping:** Section XVIII.1.

---

## 3. Historical vs. Current MSS-N Crosswalk

The table below delineates the historical Paper 043 22-level curriculum from the modern 101-stage Minimal Symbol System (MSS-N) and Proposal Fidelity Protocol (SG-N) row indices:

| Historical Paper 043 Level | Historical Focus | Modern MSS-N Row Index & Canonical Document | Notes & Structural Divergence |
|:---:|:---|:---|:---|
| **0** | Primitive Substrate `<>` & Binary Relation | MSS-00 ([`level_00_ground.md`](level_00_ground.md)) & MSS-01 | Modern MSS-0 is zero degrees of freedom `<>` ground; binary relations appear in MSS-01/02. |
| **1** | Directed Cuts & Rigidity ($D_2$) | MSS-01 ([`level_01_symbol_genesis.md`](level_01_symbol_genesis.md)) | Rigid asymmetric directed cut breaking permutation symmetry. |
| **2** | Directed Graphs & 2-Step Cochains | MSS-02 ([`level_02_relational_pairings.md`](level_02_relational_pairings.md)) | $C^0 \to C^1 \to C^2$ cochains, boundary defect $\Phi_1$, and cycle defect $\Gamma_2$. |
| **3** | Abstract Simplices & Weak Duality | MSS-03 ([`level_03_abstract_simplices.md`](level_03_abstract_simplices.md)) | Exact rational LP weak duality bounding $c^\top x \le b^\top y$. |
| **4** | Presheaves & Noncongruence | MSS-04 ([`level_04_simplex_graph_expansions.md`](level_04_simplex_graph_expansions.md)) | Simplicial set presheaves and observation congruence failure. |
| **5** | Lift Contracts & Naming Pressure | MSS-05 ([`level_05_regge_metric_simplices.md`](level_05_regge_metric_simplices.md) / Lift Engine) | Paper 043 placed lift contracts at Level 5; modern MSS-05 focuses on Regge simplices. |
| **6** | Tower & Survivor Zeta | MSS-06 ([`level_06_tower_extension_retraction.md`](level_06_tower_extension_retraction.md)) | Formal Dirichlet survivor series $\zeta_{\mathrm{surv}}(s)$. |
| **7** | Shift Dynamics & 12 Conditions | MSS-07 ([`level_07_transfer_operators_orbits.md`](level_07_transfer_operators_orbits.md)) | De Bruijn shift word graphs and CEC 12-condition audit gate. |
| **8** | Adjoint Monads & 16 Families | MSS-08 ([`level_08_monadic_adjunction_cochains.md`](level_08_monadic_adjunction_cochains.md)) | Categorical adjunction $F \dashv U$ and 16 packet families. |
| **9** | Dagger Monads & Reflection | MSS-09 ([`level_09_dagger_monads_reversal.md`](level_09_dagger_monads_reversal.md)) | Involutive dagger categories and reflection duality. |
| **10** | Spectral Shadows & Quarantine | MSS-10 ([`level_10_spectral_epistemic_quarantine.md`](level_10_spectral_epistemic_quarantine.md)) | Laplacian spectrum $\operatorname{spec}(\Delta)$ diagnostic quarantine. |
| **11** | ARS & Critical Peaks | MSS-11 ([`level_11_polygraph_confluence_peaks.md`](level_11_polygraph_confluence_peaks.md)) | 3-polygraphs and local critical peak joinability. |
| **12** | DDA Event Records & Observer | MSS-12 ([`level_12_observer_stack_dda.md`](level_12_observer_stack_dda.md)) | Deterministic Dataflow Automata and append-only event traces. |
| **13** | Alternation & Fuel Bounds | MSS-13 ([`level_13_alternation_cycle_detection.md`](level_13_alternation_cycle_detection.md)) | Quantifier alternation ladders bounded by finite fuel budgets. |
| **14** | MSS-15 R-B-G Proof Program | MSS-15 ([`level_15_rbg_authority_separation.md`](level_15_rbg_authority_separation.md)) | Historical Level 14 corresponds to MSS-15; modern MSS-14 is Bounded Quantifier Grammar. |
| **15** | Authority Calculus & Fano Lower Bounds | MSS-15 ([`level_15_rbg_authority_separation.md`](level_15_rbg_authority_separation.md)) | Information-theoretic lower bounds and terminalizer table routing. |
| **16** | Filtered Ind-Objects | MSS-16 ([`level_16_filtered_ind_objects.md`](level_16_filtered_ind_objects.md)) | Ind-completion $\operatorname{Ind}(\mathcal{C})$ over finite presentations. |
| **17** | Dialect Languages & Audits | MSS-17 ([`level_17_per_lift_dialects.md`](level_17_per_lift_dialects.md)) | Per-lift dialect syntax isolation and checksum verification. |
| **18** | Discrete Hodge Decomposition | MSS-18 ([`level_18_discrete_hodge_decomposition.md`](level_18_discrete_hodge_decomposition.md)) | Combinatorial Hodge Laplacian $\Delta = d\delta + \delta d$ over $\mathbb{Q}$. |
| **19** | Ihara-Ramanujan Zeta | MSS-19 ([`level_19_zeta_spectral_shadow.md`](level_19_zeta_spectral_shadow.md)) | Graph zeta function and Ramanujan bounds. |
| **20** | Autopoietic Reflection & `GODEL_BREAK` | MSS-20 ([`level_20_autopoietic_reflection.md`](level_20_autopoietic_reflection.md)) | Automated loop detection and unmaskable `GODEL_BREAK` refusal. |
| **21** | Discrete 4D Regge Deficits | MSS-21 ([`level_21_discrete_4d_regge_curvature.md`](level_21_discrete_4d_regge_curvature.md)) | Discrete spacetime bone deficit angles and Bianchi holonomy. |

---

## 4. Claim Hygiene Quadrant

1. **What this supports:**
   - Curricular mapping of the 22 base-tower stages (Levels 0–21) from Paper 043.
   - Step-by-step verification invariants from combinatorial rigidity through 4D Regge curvature deficits.
2. **What this does not support:**
   - Does not prove continuous Riemann hypothesis or continuum general relativity from finite simplicial complexes.
   - Does not assert that finite toy games describe empirical LLM architectures.
3. **The narrowest defensible claim:**
   - The historical Paper-043 Levels 0–21 specify a finite sequence of discrete verification obligations; their modern SG/MSS correspondences are documented separately and are not identities.
4. **Next test needed:**
   - Implement the Levels 00–21 referees, then replay their test vectors; no level referee exists at source pin `c419cc6beb` (2026-10-20).
