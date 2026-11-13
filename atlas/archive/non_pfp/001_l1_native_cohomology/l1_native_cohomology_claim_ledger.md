# Claim Ledger — ℓ¹-Native Cohomology of Finite Defect Fields

**Mathematical Scope and Nonclaims:** The general real $L^p$ and Schatten discussion is classical finite-dimensional convex analysis and operator theory. Lean 4 formalizations mechanize the finite matrix certificate theorem (L1C-TG) and model lemmas over finite integer complexes. The finite list certificate uses capacity, circulation and saturation hypotheses. Python solvers implement exact rational simplex and certified verification for $p=1, 2, \infty$, while interior-$p$ iterations use 64-bit floating-point optimization.

**Paper Key:** `001_finite_obstruction_calculus/002_l1_native_cohomology`  

**Date:** 2026-10-15

**Version:** 6.5.2

| ID | Statement | Mathematical status | Contribution status | Formalization and evidence |
|---|---|---|---|---|
| LpC-T1 | Finite weighted $L^p$ quotient infimum is attained for all $p \in [1, \infty]$. | Classical proposition; proof supplied | Classical background | Classical §2 argument remains in the manuscript. Not mechanized at this generality. |
| L1C-T1 | On the integer 3-cycle, a gauge-fixed potential is controlled by its weighted $L^1$ coboundary. | Proved for the stated integer model | Classical background; finite mechanization | `l1c_t01_coercivity_bound` in `l1c_t01_attainment`; `test_l1_cohomology.py::test_simplex_solver_standard_lp` calls `ExactTwoPhaseSimplexSolver` |
| LpC-T2 | $\Phi_p$ is a norm on $Q^1 = C^1/\text{im } d_0$ for all $p \in [1, \infty]$ under positive weights. | Classical proposition; proof supplied | Classical background | Classical §2 argument remains in the manuscript. Not mechanized at this generality. |
| L1C-T2 | Integer three-edge weighted-norm axioms and residual-addition compatibility; zero-weight refusal. | Proved for the stated integer model | Classical background; finite mechanization | `l1_norm3_positive_definite` concerns the ambient cochain norm. `l1_quotient_subadditive` adds supplied residual representatives; neither defines nor establishes a minimized quotient norm. See `l1c_t02_quotient_norm.lean`. |
| LpC-T3 | Fenchel-Rockafellar Hölder duality theorem for all $p \in [1, \infty]$ with conjugate exponent $q = p/(p-1)$. | Classical proposition; proof supplied | Classical background | Classical §3 argument remains in the manuscript. Not mechanized at this generality. The integer 3-cycle lemma `holder_weak_duality_1_inf` is not this theorem. |
| L1C-T3 | On the integer 3-cycle, a capacity-bounded circulation pairing is at most the weighted $L^1$ residual. | Proved for the stated integer model | Classical background; finite mechanization | `l1c_t03_weak_duality` in `l1c_t03_weak_duality`; `test_l1_cohomology.py::test_simplex_solver_standard_lp` calls the shipped solver. Strong duality is not this theorem. |
| LpC-C1 | Vanishing circulation pairings characterize exactness for all $p \in [1, \infty]$. | Classical proposition; proof supplied | Classical background | Classical §3 argument remains in the manuscript. Not mechanized at this generality. |
| L1C-C1 | Vanishing circulation pairings characterize exactness on a general graph. | Classical proposition; proof supplied | Classical background | Lean elaborates only `circulation_annihilates_coboundary` on the integer 3-cycle. The general converse is proved in prose, not mechanized. |
| L1C-T4 | On the integer 3-cycle, complementary-slackness data give a zero gap and certify the candidate residual. | Proved for the stated integer model | Classical background; finite mechanization | `l1c_t04_zero_duality_gap`, `l1c_t04_primal_optimality` in `l1c_t04_complementary_slackness`; `test_l1_cohomology.py::test_l1c_single_cycle_exact_formula` |
| L1C-TG | A finite list certificate with capacity, circulation, primal feasibility, and zero gap certifies global optimality. | Proved for the stated integer model | Classical certificate argument; reusable finite mechanization | `general_finite_certificate_optimality` in `l1c_general_certificate`; `test_l1_cohomology.py::test_l1_solver_primal_feasibility_check_and_receipt_validator` calls `check_certificate_receipt` Conditional integer-list theorem; no certificate existence or Python correctness theorem. |
| LpC-T4P | Uniform convexity, strict uniqueness, and nonlinear graph $p$-Laplacian optimality for $p \in (1, \infty)$. | Classical proposition; proof supplied | Classical background | Classical §4.2 argument remains in the manuscript. `gauge_fixed_lp_zero_difference` is not this theorem. |
| LpC-T4H | Classical Hilbertian $L^2$ Hodge-Helmholtz decomposition and Moore-Penrose graph Laplacian solution. | Classical proposition; proof supplied | Classical background | Classical §4.3 argument remains in the manuscript. `hodge_helmholtz_energy_conservation` on the integer 3-cycle is not the Moore-Penrose formula. |
| LpC-T4INF | Discrete Chebyshev approximation on graphs and active-edge subgradient pairing. | Classical proposition; proof supplied | Classical background | Classical §4.4 argument remains in the manuscript. Not mechanized at this generality. The Aronsson equation for arbitrary cochains stays withdrawn. |
| LpC-P1 | Secondary selection in the $p \to 1^+$ limit via weighted entropy minimization on $\mathcal{M}_1$. | Classical proposition; proof supplied | Classical background | Classical §4.5 argument remains in the manuscript. Not mechanized at this generality. |
| L1C-T5 | On the integer 3-cycle, flux is gauge-invariant and a one-sparse representative attains the weighted lower bound. | Proved for the stated integer model | Classical background; finite mechanization | `sparse_representative_attainment` in `l1c_t05_cycle_invariant`; `test_l1_cohomology.py::test_l1c_cycle_rank_support_bound_on_grid`. The general cycle-rank bound in §5 is not this theorem. |
| L1C-T6 | Integral graph data admit an integral optimum by total unimodularity. | Classical proposition; proof supplied | Classical background | Classical §6 argument remains in the manuscript. Not mechanized at this generality. `test_l1c_total_unimodularity_integer_attainment` checks shipped solver output on finite instances and is not this proof. |
| L1C-T7 | On the triangle, the plaquette, and the 5-cycle, the coboundary composite vanishes. | Proved for the stated integer model | Classical background; finite mechanization | `triangle_bianchi_nilpotency`, `plaquette_bianchi_nilpotency`, `cycle5_loop_nilpotency` in `l1c_t07_bianchi_nilpotency`; `test_l1_cohomology.py::test_discrete_physics_bianchi_identity` calls `Simplicial2Complex` |
| LpC-T8 | Quantum Schatten-$p$ operator extension and non-commutative Hölder coherence bounds. | Classical proposition; proof supplied | Classical background | Classical §8 argument remains in the manuscript. Not mechanized at this generality. |
| L1C-T8 | Quantum phase cocycle defect bound and trace-norm coherence bounding. | Classical proposition; proof supplied | Classical background | Classical §8 argument remains in the manuscript. Not mechanized at this generality. The Python tests check shipped finite functions and are not this proof. |
| L1C-NC1 | Nonzero classes represent non-trivial cohomology classes in $H^1(G; \mathbb{R})$. | Scope definition (§9) | Classical background | §9 |

## Open obligations

- Infinite-dimensional and continuum extensions are open and outside scope.
- Exact receipts certify their checked mathematical instance; finite tests do not prove implementation correctness for every input.
- The manuscript supplies proofs for the general finite-dimensional propositions. Lean covers only the declarations and coefficient domains specified above. Mathematical proof, originality, and mechanization are separate assessments.
- The general cycle-rank bound is proved in §5; dense optima may coexist with a sparse optimum. L1C-T5 mechanizes only the integer three-cycle witness.
- The earlier general Aronsson equation for arbitrary cochains remains withdrawn (§4.4).
- Continuous-$p$ and irrational-modulus outputs are binary64 diagnostics, not exact certificates.
- Current replay of the Python suite requires optional development dependencies `pytest` and `pytest-cov`; do not treat historical coverage receipts as current replay evidence unless rerun in the release environment.
