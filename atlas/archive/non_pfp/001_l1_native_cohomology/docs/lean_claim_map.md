# Lean Claim Map: ℓ¹-Native Cohomology of Finite Defect Fields

**Evidence Scope:**

The general real $L^p$ and Schatten discussion is classical finite-dimensional convex analysis and operator theory. Lean 4 formalizations mechanize the finite matrix certificate theorem (L1C-TG) and model lemmas over finite integer complexes. The finite list certificate uses capacity, circulation and saturation hypotheses. Python solvers implement exact rational simplex and certified verification for $p=1, 2, \infty$, while interior-$p$ iterations use 64-bit floating-point optimization.

**Paper Target:** `001_finite_obstruction_calculus/002_l1_native_cohomology`
**Version:** v6.5.2
**Mechanization Level:** Formal interactive proof-assistant estate verified in `lean4/` under `lake build`. L1C-TG is `general_finite_certificate_optimality`. L1C-T1, L1C-T2, L1C-T3, L1C-T4, L1C-T5, and L1C-T7 are the named finite-model theorems. General propositions have prose proofs and are classical background; only the specified coefficient domains and declarations are mechanized. Proof-placeholder commands are absent and axiom reports stay within `{propext, Classical.choice, Quot.sound}`.

---

## Claim Mechanization Status

| ID | Claim | Paper Section | Declared Status | Lean 4 Status | Lake Module | Mechanized Theorems | Axioms |
|---|---|---|---|---|---|---|---|
| `LpC-T1` | Attainment of weighted $L^p$ quotient infimum ($p \in [1, \infty]$) | §2 | `PROVED_IN_PROSE` | `PROSE` | N/A | Finite-dimensional coercivity and continuity on gauge-fixed subspace. | N/A |
| `L1C-T1` | Integer three-cycle gauge-fixed coercivity bound | §2 | `PROVED` | `MECHANIZED_FINITE_MODEL` | `l1c_t01_attainment` | 3-vertex gauge-fixed kernel/coercivity lemmas: `gauge_fixed_kernel_trivial`, `potential_v1_le_edge0`, `potential_v2_le_edge_sum`, `l1c_t01_coercivity_bound` | `{propext, Quot.sound}` |
| `LpC-T2` | $\Phi_p$ is a norm on $Q^1 = C^1 / \text{im } d_0$ for all $p \in [1, \infty]$ | §2 | `PROVED_IN_PROSE` | `PROSE` | N/A | Minkowski inequality and positive definiteness under positive weights. | N/A |
| `L1C-T2` | Integer three-edge weighted-norm axioms and residual-addition compatibility | §2 | `PROVED` | `MECHANIZED_FINITE_MODEL` | `l1c_t02_quotient_norm` | Ambient 3-edge weighted-norm algebra, supplied residual addition, and zero-weight refusal: `cycle3_d0_add`, `residual3_add`, `l1_norm3_nonneg`, `l1_norm3_triangle`, `l1_quotient_subadditive`, `l1_norm3_positive_definite`, `zero_weight_refusal_counterexample` | `{propext, Quot.sound}` |
| `LpC-T3` | Fenchel-Rockafellar Hölder duality for $L^p$ quotient defects | §3 | `PROVED_IN_PROSE` | `PROSE` | N/A | Convex duality with conjugate exponent $q = p/(p-1)$ and circulation unit ball. | N/A |
| `L1C-T3` | Integer three-cycle weak-duality inequality | §3 | `PROVED` | `MECHANIZED_CYCLE3_CORE` | `l1c_t03_weak_duality` | 3-cycle circulation annihilation, gauge-invariant pairing, and weak duality: `int_mul_le_weight_abs`, `circulation_annihilates_coboundary`, `circulation_pairing_gauge_invariant`, `l1c_t03_weak_duality` | `{propext, Quot.sound}` |
| `LpC-C1` | $L^p$ exactness characterized by circulation pairings | §3 | `PROVED_IN_PROSE` | `PROSE` | N/A | Annihilation of exact cochains across all circulations. | N/A |
| `L1C-C1` | Exactness characterized by circulation pairings ($p=1$ base case) | §3 | `PROVED_IN_PROSE` | `CYCLE3_ANNIHILATION_ONLY` | `l1c_t03_weak_duality` | Paper corollary supported by cycle3 annihilation and Python algebraic checks. | `{propext, Quot.sound}` |
| `L1C-T4` | Integer three-cycle complementary-slackness certificate | §4 | `PROVED` | `MECHANIZED_CYCLE3_CORE` | `l1c_t04_complementary_slackness` | 3-edge complementary-slackness zero-gap and primal-optimality certificate: `pairing_eq_l1_norm_of_cs`, `l1c_t04_zero_duality_gap`, `l1c_t04_primal_optimality` | `{propext, Quot.sound}` |
| `L1C-TG` | General finite matrix certificate optimality theorem | §4 | `PROVED` | `MECHANIZED_GENERAL_FINITE_CERTIFICATE` | `l1c_general_certificate` | General finite list lemmas and theorem: `dot_vec_add`, `dot_le_weighted_l1_norm`, `general_finite_certificate_optimality` | `{propext, Classical.choice, Quot.sound}` |
| `LpC-T4P` | Uniform convexity of the cochain space, powered-objective uniqueness, and graph $p$-Laplacian | §4 | `PROVED_IN_PROSE` | `PROSE` | N/A | Clarkson inequalities and Euler-Lagrange optimality $d_0^*(\vert d_0 f - \omega\vert ^{p-1}\operatorname{sgn}(d_0 f - \omega))=0$. | N/A |
| `LpC-T4H` | Classical Hilbertian $L^2$ Hodge-Helmholtz decomposition | §4 | `PROVED_IN_PROSE` | `PROSE` | N/A | Moore-Penrose graph Laplacian solution $f_2^* = -L_0^\dagger B^\top \omega$. | N/A |
| `LpC-T4INF` | Chebyshev approximation and active-edge subgradient pairing | §4 | `PROVED_IN_PROSE` | `PROSE` | N/A | Minimal maximal-edge defect and active-edge subgradient pairing (Aronsson equation withdrawn for arbitrary cochains). | N/A |
| `LpC-P1` | Secondary selection in $p \to 1^+$ limit via weighted entropy minimization | §4.5 | `PROVED_IN_PROSE` | `PROSE` | N/A | $\Gamma$-convergence and first-order entropy selection on polyhedral set $\mathcal{M}_1$. | N/A |
| `L1C-T5` | Integer three-cycle one-sparse attainment witness | §5 | `PROVED` | `MECHANIZED_CYCLE3_WITNESS` | `l1c_t05_cycle_invariant` | 3-cycle flux invariance, topological lower bound, and 1-sparse representative witness: `cycle3_residual_flux_invariant`, `abs_sum3_le`, `nat_weighted_sum_lower_bound`, `cycle3_topological_lower_bound`, `sparse_representative_attainment` | `{propext, Classical.choice, Quot.sound}` |
| `L1C-T6` | Integral graph data admit integral optimum ($p=1$) | §6 | `PROVED_IN_PROSE` | `PROSE` | N/A | Total unimodularity of deleted incidence matrix (Dey et al. 2011); verified computationally in Python. | N/A |
| `L1C-T7` | Triangle, plaquette and five-cycle Bianchi witnesses | §7 | `PROVED` | `MECHANIZED_FINITE_WITNESSES` | `l1c_t07_bianchi_nilpotency` | Triangle, plaquette, and 5-cycle witnesses: `triangle_bianchi_nilpotency`, `plaquette_bianchi_nilpotency`, `cycle5_loop_nilpotency` | `{propext, Quot.sound}` |
| `LpC-T8` | Schatten-$p$ quantum defect and non-commutative Hölder bound | §8 | `PROVED_IN_PROSE` | `PROSE` | N/A | Non-commutative Hölder duality and Schatten-$p$ off-diagonal coherence bounds. | N/A |
| `L1C-T8` | Quantum Phase Cocycle & Trace Defect Bound ($p=1$) | §8 | `PROVED_IN_PROSE` | `PROSE` | N/A | Corrected capacity-normalized loop bound $M_C = \max_e \vert C_e\vert /w_e$, exact rational $LDL^\dagger$ PSD; exact rational-modulus coherence, binary64 otherwise; verified in Python. | N/A |
| `L1C-NC1`| Nonzero classes represent non-trivial cohomology classes in $H^1(G; \mathbb{R})$ | §9 | `SCOPE FENCE` | `N/A` | None | Definitional boundary; prevents overclaim. | None |

---

## Falsifier Check: Representative Lean as Full General Mechanization

- **General finite Lean certificate count:** 1 (`L1C-TG`)
- **Finite model/core Lean witness count:** 6 (`L1C-T1`, `L1C-T2`, `L1C-T3`, `L1C-T4`, `L1C-T5`, `L1C-T7`)
- **Prose proof rows:** 12; their mathematical status is independent of Lean coverage.
- **Scope fences:** 1 (`L1C-NC1`)
- **Proof-placeholder commands:** absent
- **Axiom whitelist:** `{propext, Classical.choice, Quot.sound}`
- **Result:** The general finite-dimensional propositions are proved in prose. Lean checks the scoped integer declarations; it does not prove certificate existence or Python implementation correctness. The general Aronsson assertion remains withdrawn.


L1C-T2 checks the ambient weighted norm and addition of supplied residual representatives. It does not define or establish positive-definiteness of a minimized quotient norm.
