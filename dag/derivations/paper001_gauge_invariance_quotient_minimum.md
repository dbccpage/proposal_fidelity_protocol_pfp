# PAPER001-GAUGE-INVARIANCE-QUOTIENT-MINIMUM: Gauge Invariance of Quotient Minimum

AuthorityEffect: None.

- Archive claim: [ATL-P001-002](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers) ("Adding a coboundary to the reports leaves the quotient minimum invariant; a section update leaves it unchanged.", [paper_claim_ledger.md:14](../../atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/paper_claim_ledger.md?plain=1#L14))
- Audit derivation node: [PAPER001-GAUGE-INVARIANCE-QUOTIENT-MINIMUM](../../atlas/atlas_claim_ledger.md#part-ii-derivations-recorded-by-the-repository-audit) (`ATL-D-PAPER001-GAUGE-INVARIANCE-QUOTIENT-MINIMUM`)
- Review verdict: `matched` (`states_same_claim_as`)

## Claim

Adding an exact coboundary $Bu$ (for any 0-cochain potential $u \in \mathbb{Q}^V$) to 1-cochain edge reports $c \in \mathbb{Q}^E$ leaves the quotient minimum invariant:
$\Phi(c + Bu) = \Phi(c)$ for every potential $u \in \mathbb{Q}^V$.
Furthermore, updating a candidate section potential $s \mapsto s'$ while holding edge reports $c$ fixed leaves the quotient minimum $\Phi(c)$ unchanged.

## Hypotheses

- Finite directed graph $G = (V, E)$ without self-loops, represented by discrete boundary operator / edge-by-vertex incidence matrix $B: \mathbb{Q}^V \to \mathbb{Q}^E$, where $(Bs)_{u \to v} = s_v - s_u$.
- Edge reports $c \in \mathbb{Q}^E$ (rational 1-cochains).
- Strictly positive rational edge penalties $w_e \in \mathbb{Q}_{>0}$ for all $e \in E$.
- Admissible candidate potentials $s, u, f \in \mathbb{Q}^V$ (rational 0-cochains).
- Residual vector $r = c - Bf \in \mathbb{Q}^E$, candidate defect cost $D_c(f) = \sum_{e \in E} w_e |c_e - (Bf)_e|$, and quotient obstruction $\Phi(c) = \min_{f \in \mathbb{Q}^V} D_c(f)$.

## Derivation / Evidence

1. **Primal Invariance via Affine Potential Substitution**:
   For any fixed potential $u \in \mathbb{Q}^V$, consider shifted edge reports $c' = c + Bu$. For any evaluation potential $f \in \mathbb{Q}^V$:
   $$D_{c + Bu}(f) = \sum_{e \in E} w_e |(c + Bu)_e - (Bf)_e| = \sum_{e \in E} w_e |c_e - (B(f - u))_e| = D_c(f - u).$$
   Define the map $\tau_u: \mathbb{Q}^V \to \mathbb{Q}^V$ by $\tau_u(f) = f - u$. Because $u$ is fixed, $\tau_u$ is an affine bijection on $\mathbb{Q}^V$ with inverse $\tau_u^{-1}(g) = g + u$.
   Because $\tau_u$ is a bijection onto $\mathbb{Q}^V$:
   $$\Phi(c + Bu) = \min_{f \in \mathbb{Q}^V} D_{c + Bu}(f) = \min_{f \in \mathbb{Q}^V} D_c(\tau_u(f)) = \min_{g \in \mathbb{Q}^V} D_c(g) = \Phi(c).$$
   If $f^\star$ minimizes $D_c(f)$, then $f^\star + u$ minimizes $D_{c + Bu}(f')$, attaining the identical objective minimum $\Phi(c)$.

2. **Dual Circulation Orthogonality**:
   By linear programming strong duality on finite graphs:
   $$\Phi(c) = \max \left\{ c^\top x : x \in \mathbb{Q}^E,\ B^\top x = 0,\ |x_e| \le w_e \right\}.$$
   For shifted reports $c + Bu$ evaluated against any feasible dual circulation $x$:
   $$(c + Bu)^\top x = c^\top x + (Bu)^\top x = c^\top x + u^\top (B^\top x).$$
   Because every feasible dual vector $x$ satisfies flow conservation at every vertex ($B^\top x = 0$):
   $$u^\top (B^\top x) = u^\top 0 = 0.$$
   Therefore, $(c + Bu)^\top x = c^\top x$ on the entire dual feasible polytope.
   Because the dual feasible region $\{x : B^\top x = 0,\ |x_e| \le w_e\}$ is identical and the objective values coincide on every feasible point, the dual maximum is identical:
   $$\Phi(c + Bu) = \max_{x \in Z_1(G), \|x\|_\infty \le w} (c + Bu)^\top x = \max_{x \in Z_1(G), \|x\|_\infty \le w} c^\top x = \Phi(c).$$

3. **Section Update Invariance**:
   The quotient minimum $\Phi(c) = \min_{f \in \mathbb{Q}^V} D_c(f)$ is an intrinsic function of the fixed edge reports $c$ and edge weights $w$. It does not depend on the active candidate section $s$.
   A section update modifies the proposed potential $s \mapsto s'$, which changes candidate defect $D_c(s) \mapsto D_c(s')$.
   Because $\Phi(c)$ depends only on $c$, updating $s$ leaves $\Phi(c)$ unchanged.
   A valid section update may reduce candidate defect $D_c(s)$ toward the lower bound $\Phi(c)$, but does not alter the quotient minimum $\Phi(c)$.

4. **Executable Verification**:
   - `test_zenodo_regression_suite.py::test_regression_3_cut_invariance_and_defect_descent`: Verifies that an admitted `CUT` move updating section potentials from $s = (0, 0, 0)$ (defect 9) to $s' = (0, -4, -2)$ (defect 5) reduces candidate defect while leaving `phi_1` invariant at 5:
     `assert cut_step.defect == 5` and `assert cut_step.phi_1 == 5`.
   - `test_review_regressions.py::test_small_rational_cycles_against_independent_potential_grid`: Tests all 27 rational report combinations on a 3-cycle against an independent potential grid search, confirming exactness of $\Phi_1$ evaluation.
   - Dual flow conservation check in `test_certificate_gate.py`: Verifies that dual circulation certificates satisfy $B^\top x = 0$ exactly, confirming dual orthogonality $(Bu)^\top x = 0$.
   - Execution command:
     ```bash
     python -m pytest atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/tests/test_zenodo_regression_suite.py atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/tests/test_review_regressions.py -v
     ```
     All 25 tests in these suites pass with zero failures.

## Limits

- Applies to 1-cochains and 0-cochains on finite 1-dimensional cell complexes (directed graphs) without 2-cells; higher-dimensional coboundary shifts (e.g. 2-cochains) are outside this scope.
- Invariance holds for exact coboundary shifts $Bu$; adding non-coboundary report perturbations $c \mapsto c + \eta$ where $\eta \notin \operatorname{im} B$ alters the cohomology class $[c]$ and alters $\Phi(c)$.
- Report replacement (replacing reports $c$ by fitted coboundary $Bs$) yields $\Phi(Bs) = 0$, but changes the underlying problem rather than transforming the original reports.
- Requires strictly positive rational penalties ($w_e > 0$).
- Does not assert gauge invariance for non-linear or non-convex penalty functions.
- Does not authenticate caller identity, network transport integrity, or cryptographic report custody.

## Claim Hygiene Summary

1. **What it supports**: Demonstrates in this finite graph model with strictly positive rational edge weights that adding an exact coboundary $Bu$ to edge reports leaves the quotient minimum invariant ($\Phi(c + Bu) = \Phi(c)$ for every potential $u$), and that candidate section updates $s \mapsto s'$ leave the quotient minimum $\Phi(c)$ unchanged. Supported by constructive potential substitution bijection, dual circulation orthogonality ($B^\top x = 0 \implies (Bu)^\top x = 0$), and executable test checks in `test_zenodo_regression_suite.py`.
2. **What it does not support**: Does not support invariance under arbitrary report modifications outside $\operatorname{im} B$; does not support report replacement as preserving the original problem; does not extend to non-linear cost functions, continuous manifolds, or graphs with zero or negative weights; does not evaluate cryptographic key authorization or general agent capabilities.
3. **Narrowest defensible claim**: For any finite graph with positive rational weights $w_e > 0$, the discrete 1-cochain quotient minimum $\Phi(c) = \min_{f \in \mathbb{Q}^V} \sum_e w_e |c_e - (Bf)_e|$ satisfies $\Phi(c + Bu) = \Phi(c)$ for all $u \in \mathbb{Q}^V$, and is invariant under potential section updates $s \mapsto s'$.
4. **Next test needed**: Derivation ATL-P001-003 (Feasible primal and dual witnesses with equal values certify the optimum: weak duality and strong duality zero-gap certificate check).
