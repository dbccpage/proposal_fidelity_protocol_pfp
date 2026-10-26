# Track 200: Intermediates (Discrete Homology & Governors)

AuthorityEffect: None.

## 25-Lesson Syllabus

| Lesson ID | Title | Core Concept | Existing Anchor |
| :--- | :--- | :--- | :--- |
| **200.01** | [Minimal Symbol Systems](concepts/lesson_200_01_minimal_symbol_systems.md) | The MSS-0 to MSS-100 arity filtration and tower architecture | `NOTEBOOK_PLAN_MSSN.md` |
| **200.02** | [Arity Filtration and ARS](concepts/lesson_200_02_arity_filtration_and_ars.md) | Abstract Rewriting Systems, redex matching, and confluence | `02_arity_filtration` |
| **200.03** | [Symmetric Group Actions](concepts/lesson_200_03_symmetric_group_actions.md) | S_n permutation actions and diagonal element excision | `SnTower.lean` |
| **200.04** | [The S_n Expressivity Obstruction](concepts/lesson_200_04_the_s_n_expressivity_obstruction.md) | Cohomology classes o_n in H^1 bounding expressivity | `PO-032 §3.7` |
| **200.05** | [Constructive Difference Setoids](concepts/lesson_200_05_constructive_difference_setoids.md) | Homotopy Type Theory identity paths and primitive differences | `07_constructive_hott` |
| **200.06** | [The 1-Skeleton Complex](concepts/lesson_200_06_the_1_skeleton_complex.md) | Cochains C^0 -> C^1 -> C^2 and the coboundary operator delta^0 | `05_discrete_l1` |
| **200.07** | [Calculating Coboundary Matrices](concepts/lesson_200_07_calculating_coboundary_matrices.md) | Matrix representation: delta^0 v = v_j - v_i | `Incidence Matrix` |
| **200.08** | [Exact Subspaces B^1 and Z^1](concepts/lesson_200_08_exact_subspaces_b_1_and_z_1.md) | Coboundaries, cocycles, and the quotient homology H^1 | `Cohomology` |
| **200.09** | [Weighted L1 Defect Functional](concepts/lesson_200_09_weighted_l1_defect_functional.md) | Phi_1(c) = min_alpha ||c - delta^0 alpha||_{1, W} | `l1_governor.py` |
| **200.10** | [Holonomy on Directed Graphs](concepts/lesson_200_10_holonomy_on_directed_graphs.md) | Non-conservative vector fields and loop circulation integrals | `Directed Holonomy` |
| **200.11** | [Primal Nearest Coboundary LP](concepts/lesson_200_11_primal_nearest_coboundary_lp.md) | Linear programming formulation of optimal vertex cut shifts | `LP Primal` |
| **200.12** | [Dual Circulation Certificates](concepts/lesson_200_12_dual_circulation_certificates.md) | Dual LP circulations certifying maximum lower bounds on defect | `LP Dual` |
| **200.13** | [Total Unimodularity of Networks](concepts/lesson_200_13_total_unimodularity_of_networks.md) | Why discrete network flow problems always have integer solutions | `TUM Lemma` |
| **200.14** | [Exact Rational Duality Gap](concepts/lesson_200_14_exact_rational_duality_gap.md) | Proving Primal - Dual = 0 in Q with zero float error | `06_total_unimodularity` |
| **200.15** | [Nullspace Property and Sparse Landing](concepts/lesson_200_15_nullspace_property_and_sparse_landing.md) | Weighted NSP ensuring unique sparse projection landings | `SparseLanding.lean` |
| **200.16** | [The Five DDA Operators](concepts/lesson_200_16_the_five_dda_operators.md) | PIN, SHAPE, DEMAND, REFUSE, LAND as interior lattice contractions | `DDA Specification` |
| **200.17** | [Contravariant State Contraction](concepts/lesson_200_17_contravariant_state_contraction.md) | Monotonic shrinking of the admissible region A_{k+1} subset A_k | `DDA Contraction` |
| **200.18** | [Order-Independent Core Collapse](concepts/lesson_200_18_order_independent_core_collapse.md) | Proving collapse confluence regardless of operator application order | `Collapse Theorem` |
| **200.19** | [Terminal State Trichotomy](concepts/lesson_200_19_terminal_state_trichotomy.md) | LANDED, RESIDUAL, or REFUSED_EMPTY terminal outcomes | `Trichotomy Lemma` |
| **200.20** | [Multi-Pass Adaptive Demands](concepts/lesson_200_20_multi_pass_adaptive_demands.md) | Synthesizing new demands from residual defect cochains | `Adaptive Collapse` |
| **200.21** | [L1 Governor Architecture](concepts/lesson_200_21_l1_governor_architecture.md) | Layer-3 governor intercepting and scoring model candidates | `L1SymbolGameGovernor` |
| **200.22** | [Monotone Descent Enforcement](concepts/lesson_200_22_monotone_descent_enforcement.md) | DefectIncrease refusal: rejecting moves that worsen defect | `Monotone Descent` |
| **200.23** | [Bullshit Excision Benchmark](concepts/lesson_200_23_bullshit_excision_benchmark.md) | 50-task benchmark: L1 sparsity vs dense CoT token waste | `08_l1_sparsity` |
| **200.24** | [Governor Integration with Lean 4](concepts/lesson_200_24_governor_integration_with_lean_4.md) | Topology-50: 50/50 governed vs 0/50 ungoverned proof synthesis | `10_interactive_lean4` |
| **200.25** | [Intermediate Capstone](concepts/lesson_200_25_intermediate_capstone.md) | Autonomous solver gated by exact duality gap receipts | `Demo 4 Capstone` |
