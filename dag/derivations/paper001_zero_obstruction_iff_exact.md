# PAPER001-ZERO-OBSTRUCTION-IFF-EXACT: Zero Obstruction If and Only If Exact

AuthorityEffect: None.

- Archive claim: [ATL-P001-001](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers) ("Positive rational penalties on a finite graph give \(D_c(s)\geq\Phi(c)\), with \(\Phi=0\) exactly for \(c\in\operatorname{im}B\).", [paper_claim_ledger.md:13](../../atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/paper_claim_ledger.md?plain=1#L13))
- Audit derivation node: [PAPER001-ZERO-OBSTRUCTION-IFF-EXACT](../../atlas/atlas_claim_ledger.md#part-ii-derivations-recorded-by-the-repository-audit) (`ATL-D-PAPER001-ZERO-OBSTRUCTION-IFF-EXACT`)
- Review verdict: `matched` (`states_same_claim_as`)

## Claim

With strictly positive rational penalties on a finite graph, candidate potential defect bounds the quotient obstruction from above ($D_c(s) \ge \Phi(c)$ for every candidate potential $s$), and the quotient minimum satisfies $\Phi(c) = 0$ if and only if edge reports form an exact coboundary ($c \in \operatorname{im} B$, i.e. $c = Bf$ for some potential $f$).

## Hypotheses

- Finite directed graph $G = (V, E)$ without self-loops, represented by the discrete boundary operator / edge-by-vertex incidence matrix $B: \mathbb{Q}^V \to \mathbb{Q}^E$, with $(Bs)_{u \to v} = s_v - s_u$.
- Edge reports $c \in \mathbb{Q}^E$ (rational 1-cochains).
- Strictly positive rational edge penalties $w_e \in \mathbb{Q}_{>0}$ for all $e \in E$.
- Candidate potential $s \in \mathbb{Q}^V$ (rational 0-cochain).
- Residual vector $r = c - Bs \in \mathbb{Q}^E$, defect cost $D_c(s) = \sum_{e \in E} w_e |r_e|$, and quotient obstruction $\Phi(c) = \min_{f \in \mathbb{Q}^V} D_c(f)$.

## Derivation / Evidence

1. **Lower Bound ($D_c(s) \ge \Phi(c)$)**:
   By definition, $\Phi(c) = \min_{f \in \mathbb{Q}^V} D_c(f)$. Because candidate $s \in \mathbb{Q}^V$ is an admissible potential in the domain of the minimization, $D_c(s) \ge \min_{f} D_c(f) = \Phi(c)$. Both $D_c(s) \ge 0$ and $\Phi(c) \ge 0$ hold because penalties $w_e > 0$ and absolute values $|r_e| \ge 0$.

2. **LP Attainment**:
   The minimization $\min_{f} \sum_e w_e |c_e - (Bf)_e|$ converts to a standard rational linear program by splitting absolute values ($t_e \ge c_e - (Bf)_e$, $t_e \ge -(c_e - (Bf)_e)$) and pinning one potential reference per connected component to quotient out the constant kernel of $B$. Since the LP is feasible ($f = 0$) and bounded below by 0, standard LP duality establishes that a rational minimizer $f^\star \in \mathbb{Q}^V$ is attained with objective $\Phi(c)$.

3. **Exactness Equivalence ($\Phi(c) = 0 \iff c \in \operatorname{im} B$)**:
   - ($\Leftarrow$ Reverse / Exact coboundary): If $c \in \operatorname{im} B$, there exists $f \in \mathbb{Q}^V$ such that $c = Bf$. Evaluating candidate defect at $f$ yields residuals $r_e = c_e - (Bf)_e = 0$ for all $e \in E$. Since $w_e > 0$, $D_c(f) = \sum_e w_e |0| = 0$. Because $D_c(s) \ge 0$ for all $s$, the minimum cannot be negative, establishing $\Phi(c) = 0$.
   - ($\Rightarrow$ Forward / Zero-obstruction): If $\Phi(c) = 0$, attainment yields an optimal rational potential $f^\star$ such that $D_c(f^\star) = \sum_{e \in E} w_e |c_e - (Bf^\star)_e| = 0$. Because each weight $w_e > 0$ is strictly positive and each term $|c_e - (Bf^\star)_e| \ge 0$, a non-negative linear combination equals zero if and only if each individual term vanishes: $|c_e - (Bf^\star)_e| = 0$ for all $e \in E$. Consequently, $c_e = (Bf^\star)_e$ for all $e \in E$, meaning $c = Bf^\star \in \operatorname{im} B$.

4. **Executable Verification**:
   Executable test suites in `atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/tests/` check both directions and boundary controls:
   - `test_manuscript_witnesses.py::test_manuscript_triangle_costs_and_certificate`: Verifies that exact reports ($c = (1, 1, -2)$ with sum 0 on triangle) yield $\Phi(c) = 0$ via `compute_exact_phi_1(VERTICES, TRIANGLE, exact).phi_1 == 0`. It also checks candidate cost $D_c(s) = 6 \ge \Phi(c) = 3$ on non-exact reports $(1, 1, 1)$ certified by primal/dual witnesses.
   - `test_review_regressions.py::test_small_rational_cycles_against_independent_potential_grid`: Tests all 27 rational report combinations on a 3-cycle against an independent potential grid search, confirming `cert.phi_1 == best` and `verify_phi_1_certificate(vertices, edges, claims, cert)`.
   - Execution command:
     ```bash
     python -m pytest atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/tests/test_manuscript_witnesses.py atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/tests/test_review_regressions.py -v
     ```
     All 41 tests pass with zero failures.

## Limits

- Applies to 1-cochains on finite 1-dimensional cell complexes (graphs) without 2-cells; $C^2 = 0$, so no face curvature or higher coboundary is evaluated.
- Requires strictly positive rational penalties ($w_e > 0$). If any penalty were zero ($w_e = 0$), a nonzero residual on that edge would contribute zero cost, concealing non-exactness.
- Attainment of rational minimizer is established for finite graphs; infinite graphs and irrational edge data are outside this scope.
- Does not assert general continuous differential form exactness or de Rham cohomology on manifolds.
- Does not authenticate caller identity, edge report source veracity, or cryptographic signatures.

## Claim Hygiene Summary

1. **What it supports**: Demonstrates in this finite graph model with strictly positive rational edge weights that candidate potential defect bounds the quotient obstruction from above ($D_c(s) \ge \Phi(c)$), and that the quotient minimum $\Phi(c) = 0$ if and only if edge reports $c$ form an exact coboundary ($c \in \operatorname{im} B$). Checked by both constructive linear programming / dual witness certificates and pytest test suites (`test_manuscript_witnesses.py`, `test_review_regressions.py`).
2. **What it does not support**: Does not support claims for graphs with non-positive (zero or negative) weights; does not extend to higher-dimensional cochain complexes with filled 2-cells; does not assert runtime complexity bounds for large graphs or unconstrained integer programs; does not evaluate general model capabilities or physical field emergence.
3. **Narrowest defensible claim**: For finite graphs with strictly positive rational weights, the discrete 1-cochain quotient minimum $\Phi(c) = \min_f \sum_e w_e |c_e - (Bf)_e|$ satisfies $D_c(s) \ge \Phi(c)$ for any 0-cochain $s$, and vanishes ($\Phi(c) = 0$) if and only if $c = Bf$ for some 0-cochain $f$.
4. **Next test needed**: Derivation ATL-P001-002 (Paper 001 gauge invariance of the quotient minimum: $\Phi(c + Bu) = \Phi(c)$ for every potential $u$).
