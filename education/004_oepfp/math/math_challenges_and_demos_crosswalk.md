---
documentation_contract: symbol-game-documentation/v1
title: 'Mathematical Crosswalk: 143 Challenges, 30 Demos, and the 10-Chapter Canonical Spine'
kind: mathematical-reference
audience:
  - researchers
  - curriculum-designers
  - software-engineers
  - coding-agents
status: active
maturity: canonical
claim_status: verified
authority_effect: "None"
mathematical_status:
  definitions:
    - mathematical_crosswalk_mapping
    - challenge_tier_taxonomies
    - demo_operational_tiers
  prose_theorems:
    - cross_layer_namespace_separation
    - demo_challenge_spine_completeness
  lean_theorems: []
  finite_computations:
    - 143_challenge_specifications_catalog
    - 30_demo_suites_inventory
  declared_policies:
    - strict_namespace_separation
  applications:
    - educational_curriculum_navigation
    - research_verification_tracking
  open_conjectures: []
coefficient_domain: "ℚ / ℤ / ℂ"
runtime_dependency: "All 10 Canonical Math Chapters (MATH-00 through MATH-09)"
governance_dependency: "None"
---

# Mathematical Crosswalk: 143 Challenges, 30 Demos, and the 10-Chapter Canonical Spine

**Status:** Canonical Mathematics & Engineering Crosswalk  
**Context:** Establishes the bi-directional mapping between the 10-chapter canonical mathematics spine of the Symbol Game (`1_symbol_game_math/`), the 30 executable demo packages (`pilots/demo_003/`), the 143 challenge specifications (`pilots/demo_004/`), and the 10 modular application notes.

> **Path check (2026-10-20, pin `c419cc6beb`).** The spine is this folder, `omega_engine_education/documentation/004_oepfp/math/`. Neither `pilots/demo_003/` nor `pilots/demo_004/` exists under `omega_engine_education/` at the pin; copies appear only inside evidence snapshots. Some packages now live elsewhere: challenge packages such as `c051_exact_lp_solver_with_duals`, `c052`–`c055` and `c059` are under `omega_engine_woland/tests/pilots/`; demos `demo_3`, `demo_antimorphic_reversal`, `demo_eis_failure_classes` and `demo_token_frontier` are under `omega_engine_atlas/coda_atlas/F004_papers/015_pfp/003_pfp_host_admitted_failure_detectors/demos/`; challenge tests are under `omega_engine_pfp/tests/demo_004/`. The counts 143 and 30 were not recounted. Treat the demo and challenge columns as a historical map.  
**Authority:** None. Definitional and navigational crosswalk.

---

## 1. Cross-Layer Architecture & Namespace Discipline

The Symbol Game estate enforces strict cross-layer namespace separation:

$$\boxed{ \text{Math Chapter } (\text{MATH-}k) \iff \text{Carrier / Geometry} \iff \text{Demos } (\text{DEMO-}j) \iff \text{Challenges } (\text{C/G/W-}m) }$$

```
                                  [ 10-CHAPTER CANONICAL MATH SPINE ]
                                  (MATH-00 through MATH-09 in 1_symbol_game_math)
                                                 │
                        ┌────────────────────────┴────────────────────────┐
                        ▼                                                 ▼
          [ 10 DOWNSTREAM APPLICATION NOTES ]            [ 30 REPLAYABLE DEMOS ]
          (Regge, BQNF, Polygraphs, MUB(6),              (demo_1 .. demo_12, mub6,
           Antimorphisms, Decoders, EIS)                  token_frontier, polygraph)
                        │                                                 │
                        └────────────────────────┬────────────────────────┘
                                                 ▼
                                   [ 143 RESEARCH CHALLENGES ]
                                   (100 C-series, 25 G-series, 18 W-series)
```

---

## 2. Master Mapping: Canonical Math Chapters to Demos & Challenges

| Chapter | Title & Primary Mathematical Topic | Carrier / Invariant | Associated Demos | Primary Challenge Packages |
| :---: | :--- | :--- | :--- | :--- |
| **MATH-00** | [`00_math_scope_provenance_and_notation.md`](./00_math_scope_provenance_and_notation.md)<br>*Scope, Provenance, and Notation* | Namespace firewall, 7-grade claim taxonomy, naming pressure $NP(n)$. | `mssn/trajectory.py`, `demo_system_coverage` | **C100** (Metatheory), **G01–G25** (Genesis pins), **W10** (Primitive Axiomatics). |
| **MATH-01** | [`01_math_difference_cuts_and_rigidity.md`](./01_math_difference_cuts_and_rigidity.md)<br>*Primitive Difference, Cuts & Rigidity* | Formal ground `<>`, difference relation $R_{\mathrm{diff}}$, directed cut $D_2$ rigidity, symmetric link $S_2$. | `demo_1` (3-cycle cut descent), `demo_2` (stoquastic cuts) | **C001–C010** (Attention & carriers), **W01** (Event structures), **W04** (Clock packets). |
| **MATH-02** | [`02_math_cochain_complexes_repairs_and_quotients.md`](./02_math_cochain_complexes_repairs_and_quotients.md)<br>*Cochain Complexes, Repairs & Quotients* | Graded complex $C^0 \xrightarrow{d_0} C^1 \xrightarrow{d_1} C^2$, exact repairs $B^1$, quotient space $Q^1 = C^1 / \operatorname{im}(d_0)$. | `demo_4` ($b_1=1$), `demo_5` ($b_1=2, 4$), `demo_cohomology_battery` | **C011** (Cycle-rank coboundary repair), **C013** (Smith Normal Form), **W02** (Matroid circulation). |
| **MATH-03** | [`03_math_obstruction_mass_duality_and_exact_lp.md`](./03_math_obstruction_mass_duality_and_exact_lp.md)<br>*Obstruction Mass, Duality & Exact LP* | $\ell^1$ quotient obstruction mass $\Phi_1$, closure diagnostic $\Gamma_2$, dual witnesses in $\mathbb{Q}$, zero-gap certification. | `demo_4` (LP weak duality gap $= 0$), `demo_6` ($\Phi_2$), `demo_7` ($\Phi_3$) | **C051** (Exact LP with dual certificates), **C052** (Max-flow min-cut), **W11** (Fenchel-Rockafellar duality). |
| **MATH-04** | [`04_math_minimal_representatives_and_hodge.md`](./04_math_minimal_representatives_and_hodge.md)<br>*Minimal Representatives & Hodge Decomposition* | Discrete Hodge $C^1 = \operatorname{im}(d_0) \oplus \mathcal{H}^1 \oplus \operatorname{im}(d_1^*)$, minimal representatives, maximal-sparsity face selector $\Pi_1$. | `demo_5` (Kagome flux coupling), `bqnf_cochain_views` | **C014** (Discrete Hodge decomposition), **C018** (Signed graph frustration), **C019** ($H^2$ obstructions). |
| **MATH-05** | [`05_math_contexts_observers_and_detector_adequacy.md`](./05_math_contexts_observers_and_detector_adequacy.md)<br>*Contexts, Observers & Non-Factorization* | Context categories $\mathcal{C}_n$, observer tuple $\mathcal{O}$, calibration fixtures, Mechanized Non-Factorization (`PaperER007.lggr`). | `demo_8` (Sheaf descent on $U_1 \cap U_2$), `demo_10` (Monotonic authorization) | **C012** (Cellular sheaf $H^0, H^1$), **C087** (MHC partial views), **W05** (Čech gluing), **W12–W13** (LGGR I–VI). |
| **MATH-06** | [`06_math_extension_descent_and_lift_contracts.md`](./06_math_extension_descent_and_lift_contracts.md)<br>*Extension, Descent & Lift Contracts* | Graded lift contract $\Lambda_n = (w, E, m, F_n, U_n, I_n^\bullet, \pi)$, syntax retraction $U_n \circ F_n = \mathrm{id}$, invariant skeleton $\operatorname{Skel}_n$. | `demo_tower_lift`, `mssn/trajectory.py` (up-lift $u_n$, retraction $d_n$) | **C049** (Universal category constructions), **W03** (Double category descent), **W09** (Terminal profile transport). |
| **MATH-07** | [`07_math_filtered_diagrams_persistence_and_survivors.md`](./07_math_filtered_diagrams_persistence_and_survivors.md)<br>*Filtered Diagrams & Persistent Survivors* | Conditional filtered diagrams $D: (\mathbb{N}, \le) \to \mathbf{FinSym}$, directed colimit cohomology $H^1_\infty$, survivor monoid $\mathcal{H}$, $\zeta_{\mathrm{surv}}(z)$. | `mssn` (101-stage tower evaluation), `demo_cohomology_battery` | **C015** (Persistent homology barcodes), **C047** (Generating-function discovery), **W07** (Semiring path lumpability). |
| **MATH-08** | [`08_math_transfer_operators_periodic_orbits_and_zeta.md`](./08_math_transfer_operators_periodic_orbits_and_zeta.md)<br>*Transfer Operators & Orbit Zeta Functions* | De Bruijn graph $B(2,1)$, transfer matrix $A = \begin{pmatrix}1&1\\1&1\end{pmatrix}$, entropy $\log 2$, Artin-Mazur zeta $\zeta_A(z) = (1-2z)^{-1}$, primitive orbits $\pi(n)$. | `demo_8` (transfer operator trace), `demo_trajectory` | **C047** (Recurrence discovery), **C066** (Boolean GRN attractors), **W08** (Discrete isometry reconstruction). |
| **MATH-09** | [`09_math_reversal_spectral_shadows_and_quarantine.md`](./09_math_reversal_spectral_shadows_and_quarantine.md)<br>*Reversal, Spectral Shadows & Quarantine* | Graph orientation reversal, Ihara zeta completed functional equation, Alon-Boppana bound, Ramanujan graphs ($|\lambda| \le 2\sqrt{q}$), quarantine ledger. | `demo_antimorphic_reversal`, `demo_3_mub6`, `demo_woland_tribunal` | **C021–C030** (Quantum stabilizers), **C081–C090** (OEEIS immunity), **W16–W17** ($SO(k)$ gauge rigidity). |

---

## 3. Downstream Mathematical Application Notes

The 10 modular application notes housed in `1_symbol_game_math/` map directly to specialized demo suites and challenge clusters:

| Document | Primary Mathematical Focus | Grounded Demos | Target Challenges |
| :--- | :--- | :--- | :--- |
| [`bqnf_cochain_views.md`](./bqnf_cochain_views.md) | Boundary-Quotient Normal Form (BQNF), discrete Hodge view maintenance, SQL schema cochains. | `demo_2` (BQNF $\alpha/\lambda$) | **C059** (SQL 3VL synthesis), **C077** (Ledger reconciliation as $H^1$). |
| [`math_regge_geometry_and_holonomy.md`](./math_regge_geometry_and_holonomy.md) | Discrete 4D Regge calculus, signed Cayley-Menger nondegeneracy, $\mathrm{SO}(4)$ parallel transport, non-Abelian Bianchi identity. | `demo_mub6_regge` | **C017** (Nonabelian lattice holonomy), **C038** (Regge combinatorial curvature). |
| [`information_theoretic_limits.md`](./information_theoretic_limits.md) | Fano's inequality, equivocation lower bounds on unverified proposal prediction, channel capacity. | `demo_token_frontier` | **C001–C010** (Attention & decoding), **C070** (Self/nonself cover). |
| [`bounded_execution_and_authority_separation.md`](./bounded_execution_and_authority_separation.md) | Proposer/verifier authority separation, sufficient composite bounded-execution condition, terminal sum type $\mathbb{T}_S$, evaluation-state cycle breaking. | `demo_woland_tribunal` | **C100** (Metatheory authority preservation), **W09** (Terminal profile transport). |
| [`math_higher_cochains_and_bianchi_obstructions.md`](./math_higher_cochains_and_bianchi_obstructions.md) | Graded complexes $C^k \xrightarrow{d_k} C^{k+1}$, all-degree nilpotence, discrete Bianchi $d_2 d_1 = 0$, $\Phi_k([H])$, Green-Schwarz anomaly $d_3 H = \operatorname{Tr}(F \smile F)$. | `demo_6` ($b_2=1, 2$), `demo_7` ($b_3=1$), `demo_9` ($b_4=1$), `demo_11`, `demo_12` | **C013** (Homology torsion), **C016** (Cup products), **C019** ($H^2$ obstructions), **C031–C032** (Anomaly cancellation). |
| [`math_antimorphism_and_path_inversion.md`](./math_antimorphism_and_path_inversion.md) | Free path category $\mathcal{P}(G)$, contravariant involution $((p)^\dagger)^\dagger = p$, signed graph frustration, failure modes AM-1..AM-4, AM-FSP-2. | `demo_antimorphic_reversal`, `antimorphism_farm` | **C018** (Signed graph frustration), **C090** (Antimorphism farm to judge). |
| [`math_polygraph_rewriting_and_confluence.md`](./math_polygraph_rewriting_and_confluence.md) | 2-polygraphs $(\Sigma_0, \Sigma_1, \Sigma_2)$, 2-cell rewrites $u \Rightarrow v$, step continuity, divergent peaks, Newman's lemma, Level 11 stage floor. | `demo_polygraph_confluence` | **C046** (Knuth-Bendix completion), **C050** (Equational theorem proving). |
| [`math_constrained_decoding_and_token_frontiers.md`](./math_constrained_decoding_and_token_frontiers.md) | Simplex $\ell_1$ invariance theorem ($\|p\|_1 \equiv 1$), syntax-directed logit masking, Bayesian re-normalization, zero-retained-mass fail-stop, Three-Layer Sovereignty. | `demo_token_frontier`, `attention_sparse_output_boundary.md` | **C001–C005** (Attention & grammar masks), **C006** (Host scratch space). |
| [`math_quantum_mub_and_stabilizers.md`](./math_quantum_mub_and_stabilizers.md) | Finite MUB condition, $d=6$ composite obstruction, Segre variety corner minors, Deltoid cusp 6-cycle holonomy $\Gamma = 12133/5000 > 0$, Pauli stabilizer geometry. | `demo_3_mub6`, `demo_q40_quantum_solver` | **C021** (Q40-R synthesis), **C022** (Stabilizer distance), **C025** (MUB prime power). |
| [`math_epistemic_immune_system_and_negative_selection.md`](./math_epistemic_immune_system_and_negative_selection.md) | Artificial immune systems, sealed Self-Panel $S$, Negative Selection Algorithm (NSA), Two-Signal Activation Gate ($\text{Signal}_1 \land \text{Signal}_2$), Treg tolerance. | `demo_eis_failure_classes`, `demo_4e_cogsci_autopoiesis` | **C081** (Thymus self-panel), **C082** (Two-signal danger gate), **C083** (Clonal maturation). |

---

## 4. Challenge Estate Domains & Upgrades Summary

The 143 challenges in `pilots/demo_004/` (historical path) span 12 thematic clusters, A to L (corrected 2026-10-20 from "10"; the table lists 12 rows, with 100 C-series, 25 G-series and 18 W-series challenges):

```
+─────────────────────────────────────────────────────────────────────────────────────────────+
|                                143 CHALLENGES IN THE ESTATE                                 |
+──────────────────────────┬──────────────────────────┬───────────────────────────────────────+
| DOMAIN                   | CHALLENGE RANGE          | KEY CONCEPTS & GOVERNING EQUATIONS     |
+──────────────────────────┼──────────────────────────┼───────────────────────────────────────+
| A. Mechanism & Decoders  | C001 – C010 (10)         | Key attention masks, logit projection, KV surgery |
| B. Cohomology & Sheaves  | C011 – C020 (10)         | Coboundary repair, cellular sheaves, Smith Normal Form|
| C. Quantum Information   | C021 – C030 (10)         | Q40 stabilizer distance, Clifford synthesis, exact MUB|
| D. Physics & M-Theory    | C031 – C040 (10)         | Anomaly-free U(1), 6D SUGRA, Calabi-Yau Hodge numbers |
| E. Formal Math & Logic   | C041 – C050 (10)         | Lean 4 finite lemmas, SAT DRAT/LRAT, Knuth-Bendix    |
| F. Program Synthesis     | C051 – C060 (10)         | Exact LP Farkas duals, Bareiss fraction-free, SQL 3VL |
| G. Chemistry & Biology   | C061 – C070 (10)         | Reaction network deficiency, kinetic proofreading     |
| H. Economics & Markets   | C071 – C080 (10)         | Nash equilibria, Fisher market, arbitrage holonomy    |
| I. OEEIS Epistemic Immune| C081 – C090 (10)         | Thymus self-panel, Two-Signal danger, clonal affinity |
| J. Metatheory & Genesis  | C091 – C100 (10)         | Modal logic, cut elimination, AuthorityEffect: None   |
| K. Genesis (19L57G1)     | G01 – G25 (25)           | Cut census 2^(n-2), Alpha Engine, H3V7N5QF           |
| L. Witnessed Difference  | W01 – W18 (18)           | Retention packets, LGGR I–VI, SO(k) gauge rigidity     |
+──────────────────────────┴──────────────────────────┴───────────────────────────────────────+
```

---

## 5. Claim Hygiene & Artifact Boundary

1. **What this document supports:**
   - Provides a comprehensive, navigable 1-to-1 crosswalk between the canonical 10-chapter mathematics spine (`1_symbol_game_math/`), all 30 executable demos (`pilots/demo_003/`), all 143 research challenges (`pilots/demo_004/`), and all 10 downstream application notes.
   - Enforces cross-layer namespace separation ($\text{MATH-}k \neq \text{DEMO-}j \neq \text{C-}m$).

2. **What this document does NOT support:**
   - Does not assert that planned challenges without retained runs (`planned` status) have been scored or solved.
   - Does not mint operational authority for mathematical proofs.

3. **Narrowest defensible claim:**
   - The tables in this document accurately catalog the current cross-layer dependencies and conceptual mappings connecting the Symbol Game mathematical documentation, demo packages, and challenge specifications in this repository.

4. **Next test needed:**
   - Verify all file links in this crosswalk via the documentation integrity validator (`docs_integrity.py validate`).
