# PAPER001-WEIGHTED-NULL-SPACE-UNIQUENESS: Weighted Null-Space Property Uniqueness

AuthorityEffect: None.

- Archive claim: [ATL-P001-006](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers) ("A weighted null-space property on the residual support suffices for uniqueness.", [paper_claim_ledger.md:18](../../atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/paper_claim_ledger.md?plain=1#L18))
- Audit derivation node: [PAPER001-WEIGHTED-NULL-SPACE-UNIQUENESS](../../atlas/atlas_claim_ledger.md#part-ii-derivations-recorded-by-the-repository-audit) (`ATL-D-PAPER001-WEIGHTED-NULL-SPACE-UNIQUENESS`)
- Review verdict: `matched` (`states_same_claim_as`)

## Claim

Let $G = (V, E)$ be a finite directed graph with strictly positive rational edge weights $w \in \mathbb{Q}_{>0}^E$ and discrete boundary operator $B: \mathbb{Q}^V \to \mathbb{Q}^E$.
If $r^\star \in c + \operatorname{im} B$ is an optimal residual vector with support $S = \operatorname{supp}(r^\star) = \{e \in E : r^\star_e \neq 0\}$, and every nonzero coboundary $z \in \operatorname{im} B \setminus \{0\}$ satisfies the weighted null-space inequality:
$$\sum_{e \in S} w_e |z_e| < \sum_{e \notin S} w_e |z_e|,$$
then $r^\star$ is uniquely the optimal residual vector in the affine coset $c + \operatorname{im} B$:
$$\|r\|_{1, w} > \|r^\star\|_{1, w} \quad \text{for all } r \in (c + \operatorname{im} B) \setminus \{r^\star\}.$$

## Context & Scope

This derivation addresses discrete 1-cochain quotient defect minimization on finite 1-dimensional cell complexes (graphs) without 2-cells ($C^2 = 0$).
Specifically, it analyzes:
1. The geometry of the quotient residual coset $\mathcal{A} = c + \operatorname{im} B \subset \mathbb{Q}^E$.
2. The discrete adaptation of the null-space property from $\ell_1$-minimization and compressed sensing to graph coboundary cosets.
3. The distinction between residual vector uniqueness in $\mathbb{Q}^E$ and potential uniqueness in $\mathbb{Q}^V$ (which retains gauge freedom on connected components).
4. The boundary distinction between a sufficient condition and a necessary certificate.

## Hypotheses & Definitions

- Finite directed graph $G = (V, E)$ without self-loops, with vertices $V$, directed edges $E$, and $k \ge 1$ connected components.
- Boundary operator / incidence matrix $B: \mathbb{Q}^V \to \mathbb{Q}^E$, defined on directed edge $e = (u \to v)$ by $(Bf)_e = f_v - f_u$.
- Kernel $\ker B \subset \mathbb{Q}^V$ consisting of 0-cochains that are constant on each connected component ($\dim \ker B = k$).
- Coboundary image $\operatorname{im} B \subset \mathbb{Q}^E$, with $\dim \operatorname{im} B = |V| - k$.
- Edge reports: $c \in \mathbb{Q}^E$ (rational 1-cochain).
- Strictly positive rational penalties: $w_e \in \mathbb{Q}_{>0}$ for all $e \in E$.
- Weighted $\ell_1$-norm on $\mathbb{Q}^E$: $\|x\|_{1, w} = \sum_{e \in E} w_e |x_e|$.
- Candidate potential $f \in \mathbb{Q}^V$, residual vector $r(f) = c - Bf \in \mathbb{Q}^E$, and candidate defect cost $D_c(f) = \|c - Bf\|_{1, w}$.
- Quotient obstruction: $\Phi(c) = \min_{f \in \mathbb{Q}^V} D_c(f) = \min_{r \in c + \operatorname{im} B} \|r\|_{1, w}$.
- Optimal residual: $r^\star \in c + \operatorname{im} B$ such that $\|r^\star\|_{1, w} = \Phi(c)$.
- Support of residual: $S = \operatorname{supp}(r^\star) = \{e \in E : r^\star_e \neq 0\}$, with complement $S^c = E \setminus S = \{e \in E : r^\star_e = 0\}$.
- For any vector $z \in \mathbb{Q}^E$, the support restrictions are denoted $z_S \in \mathbb{Q}^E$ (with $(z_S)_e = z_e$ for $e \in S$ and 0 otherwise) and $z_{S^c} \in \mathbb{Q}^E$ (with $(z_{S^c})_e = z_e$ for $e \in S^c$ and 0 otherwise), so that $\|z_S\|_{1, w} = \sum_{e \in S} w_e |z_e|$ and $\|z_{S^c}\|_{1, w} = \sum_{e \notin S} w_e |z_e|$.

## Mathematical Derivation

### 1. Affine Coset Parameterization of Perturbations

Let $r^\star \in c + \operatorname{im} B$ be an optimal residual with support $S = \operatorname{supp}(r^\star)$.
Any candidate residual vector $r \in \mathbb{Q}^E$ belongs to the affine coset $c + \operatorname{im} B$ if and only if $r - c \in \operatorname{im} B$.
Because both $r$ and $r^\star$ lie in $c + \operatorname{im} B$, their difference satisfies:
$$r - r^\star = (r - c) - (r^\star - c) \in \operatorname{im} B.$$
Therefore, any alternative residual $r \in c + \operatorname{im} B$ can be parameterized as:
$$r = r^\star + z, \quad \text{where } z \in \operatorname{im} B.$$
If $r \neq r^\star$, then $z = r - r^\star \neq 0$, so $z \in \operatorname{im} B \setminus \{0\}$.

### 2. Norm Evaluation and Support Splitting

Evaluate the weighted $\ell_1$-norm of the perturbed residual $r^\star + z$:
$$\|r^\star + z\|_{1, w} = \sum_{e \in E} w_e |r^\star_e + z_e|.$$
Partition the sum over all edges $E$ into support edges $S$ and off-support edges $S^c$:
$$\|r^\star + z\|_{1, w} = \sum_{e \in S} w_e |r^\star_e + z_e| + \sum_{e \in S^c} w_e |r^\star_e + z_e|.$$

1. **Off-support evaluation on $S^c$**:
   By definition of the support $S = \{e \in E : r^\star_e \neq 0\}$, every edge $e \in S^c$ has $r^\star_e = 0$.
   Therefore, on $S^c$:
   $$|r^\star_e + z_e| = |0 + z_e| = |z_e|.$$
   Because each weight $w_e > 0$:
   $$\sum_{e \in S^c} w_e |r^\star_e + z_e| = \sum_{e \in S^c} w_e |z_e| = \|z_{S^c}\|_{1, w}.$$

2. **Support lower bound on $S$**:
   For each edge $e \in S$, by the reverse triangle inequality on $\mathbb{Q}$:
   $$|r^\star_e + z_e| \ge |r^\star_e| - |z_e|.$$
   Multiplying by strictly positive weight $w_e > 0$:
   $$w_e |r^\star_e + z_e| \ge w_e |r^\star_e| - w_e |z_e|.$$
   Summing over all edges in $S$:
   $$\sum_{e \in S} w_e |r^\star_e + z_e| \ge \sum_{e \in S} w_e |r^\star_e| - \sum_{e \in S} w_e |z_e| = \|r^\star\|_{1, w} - \|z_S\|_{1, w}.$$

### 3. Application of the Weighted Null-Space Property

Combining the two sums gives a lower bound on the objective of the perturbed residual:
$$\|r^\star + z\|_{1, w} \ge \left(\|r^\star\|_{1, w} - \|z_S\|_{1, w}\right) + \|z_{S^c}\|_{1, w} = \|r^\star\|_{1, w} + \left(\|z_{S^c}\|_{1, w} - \|z_S\|_{1, w}\right).$$
By hypothesis, the weighted null-space property holds on $S$: every nonzero coboundary $z \in \operatorname{im} B \setminus \{0\}$ satisfies:
$$\|z_S\|_{1, w} < \|z_{S^c}\|_{1, w} \iff \|z_{S^c}\|_{1, w} - \|z_S\|_{1, w} > 0.$$
Because $r \neq r^\star$, the perturbation $z = r - r^\star$ is nonzero ($z \in \operatorname{im} B \setminus \{0\}$).
Substituting this strict inequality into the lower bound yields:
$$\|r\|_{1, w} = \|r^\star + z\|_{1, w} \ge \|r^\star\|_{1, w} + (\|z_{S^c}\|_{1, w} - \|z_S\|_{1, w}) > \|r^\star\|_{1, w}.$$
This demonstrates that every alternative residual $r \in (c + \operatorname{im} B) \setminus \{r^\star\}$ incurs strictly greater defect than $r^\star$.
Consequently, $r^\star$ is the unique optimal residual vector in $c + \operatorname{im} B$.

### 4. Manuscript Triangle Witness Replay

The manuscript introductory witness provides an exact setting to examine the weighted null-space property:
- Vertices: $V = \{a, b, c\}$.
- Edges: $e_1 = (a \to b), e_2 = (b \to c), e_3 = (c \to a)$.
- Penalties: $w = (w_{a \to b}, w_{b \to c}, w_{c \to a}) = (1, 2, 3)$.
- Edge reports: $c = (1, 1, 1)$, with cycle holonomy $h = 3$.
- Optimal residual: $r^\star = (3, 0, 0)$ supported on $S = \{a \to b\}$, with $\|r^\star\|_{1, w} = 1 \cdot 3 + 2 \cdot 0 + 3 \cdot 0 = 3$.
- Off-support edges: $S^c = \{b \to c, c \to a\}$.

**Evaluation of the Weighted Null-Space Property on $S = \{a \to b\}$:**
For any potential vector $u \in \mathbb{Q}^V$, the coboundary $z = Bu$ has coordinates:
$$z_{a \to b} = u_b - u_a, \quad z_{b \to c} = u_c - u_b, \quad z_{c \to a} = u_a - u_c.$$
Because the cycle telescopes to zero:
$$z_{a \to b} + z_{b \to c} + z_{c \to a} = 0 \implies z_{a \to b} = -(z_{b \to c} + z_{c \to a}).$$
By the triangle inequality:
$$|z_{a \to b}| = |z_{b \to c} + z_{c \to a}| \le |z_{b \to c}| + |z_{c \to a}|.$$
Evaluating the weighted norms on $S$ and $S^c$:
$$\|z_S\|_{1, w} = w_{a \to b} |z_{a \to b}| = 1 \cdot |z_{a \to b}| \le |z_{b \to c}| + |z_{c \to a}|.$$
$$\|z_{S^c}\|_{1, w} = w_{b \to c} |z_{b \to c}| + w_{c \to a} |z_{c \to a}| = 2 |z_{b \to c}| + 3 |z_{c \to a}|.$$
If $z \neq 0$, then $z_{b \to c}$ and $z_{c \to a}$ cannot both be zero. Because $w_{b \to c} = 2 > 1$ and $w_{c \to a} = 3 > 1$:
$$\|z_{S^c}\|_{1, w} = 2 |z_{b \to c}| + 3 |z_{c \to a}| > 1 \cdot (|z_{b \to c}| + |z_{c \to a}|) \ge |z_{a \to b}| = \|z_S\|_{1, w}.$$
Therefore, $\|z_S\|_{1, w} < \|z_{S^c}\|_{1, w}$ holds strictly for every nonzero $z \in \operatorname{im} B$.
The weighted null-space property on $S = \{a \to b\}$ is satisfied, showing under declared hypotheses that $r^\star = (3, 0, 0)$ is the unique optimal residual.

### 5. Uniform Weights Counterexample Witnessing Non-Uniqueness

To demonstrate that the condition separates unique from non-unique regimes, consider the uniform weight triangle:
- Vertices: $V = \{a, b, c\}$.
- Edges: $e_1 = (a \to b), e_2 = (b \to c), e_3 = (c \to a)$.
- Penalties: $w = (1, 1, 1)$.
- Edge reports: $c = (1, 1, 1)$, holonomy $h = 3$.
- Candidate optimal residual: $r^\star = (3, 0, 0)$ with support $S = \{a \to b\}$.
- Candidate perturbation: $u = (-1, 0, 0) \implies z = Bu = (1, 0, -1)$.
- Weighted norms:
  $$\|z_S\|_{1, w} = 1 \cdot |1| = 1.$$
  $$\|z_{S^c}\|_{1, w} = 1 \cdot |0| + 1 \cdot |-1| = 1.$$
  Here $\|z_S\|_{1, w} = \|z_{S^c}\|_{1, w}$, so the strict weighted null-space property fails.
- Evaluating perturbed residual $r' = r^\star - z = (3 - 1, 0 - 0, 0 - (-1)) = (2, 0, 1)$:
  $$\|r'\|_{1, w} = 1 \cdot |2| + 1 \cdot |0| + 1 \cdot |1| = 3 = \|r^\star\|_{1, w}.$$
  Both $r^\star = (3, 0, 0)$ and $r' = (2, 0, 1)$ achieve optimal defect 3, confirming that when the weighted null-space property fails, optimal residuals can form an optimal face with multiple minimizers.

## Test Witnesses & Verification Evidence

1. **Manuscript Witness Replay (`test_manuscript_witnesses.py`)**:
   `atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/tests/test_manuscript_witnesses.py`:
   - `test_manuscript_triangle_costs_and_certificate`: Verifies that optimal potential $s^\star = (0, -2, -1)$ yields residual $r^\star = (3, 0, 0)$ with cost 3, certified by dual circulation $(1, 1, 1)$ of value 3 with zero duality gap.
   - Command:
     ```bash
     python -m pytest atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/tests/test_manuscript_witnesses.py -v
     ```
     Result: 3 passed with zero failures.

2. **Potential Grid Search Across Rational Reports (`test_review_regressions.py`)**:
   `atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/tests/test_review_regressions.py`:
   - `test_small_rational_cycles_against_independent_potential_grid`: Tests all 27 rational report combinations on a 3-cycle with non-uniform weights $(1, 2, 3)$ against an independent grid search, verifying agreement with the exact certificate solver.
   - Command:
     ```bash
     python -m pytest atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/tests/test_review_regressions.py -k test_small_rational_cycles_against_independent_potential_grid -v
     ```
     Result: 1 passed with zero failures.

3. **Rust Solver Manuscript Triangle Conformance**:
   `code/rust/core_solvers/src/solver_graph_phi1_distance.rs`:
   - `manuscript_triangle_minimum_is_three`: Solves the manuscript triangle in Rust, confirming $\Phi_1 = 3$ and gauge potential $(0, -2, -1)$ with residual 3 on edge $a \to b$.
   - Command:
     ```bash
     cargo test --manifest-path code/rust/Cargo.toml -p core_solvers --lib manuscript_triangle_minimum_is_three
     ```
     Result: 1 passed with zero failures.

## Limits and Non-Claims

- **Sufficient Condition Only**: The weighted null-space property is a sufficient condition for residual uniqueness; it is not a necessary condition.
- **Failure of a sufficient condition is not a nonuniqueness certificate**: If $\|z_S\|_{1, w} \ge \|z_{S^c}\|_{1, w}$ for some $z \in \operatorname{im} B$, the optimal residual $r^\star$ may still be strictly unique. The reverse triangle inequality $|r^\star_e + z_e| \ge |r^\star_e| - |z_e|$ represents worst-case opposing alignment ($\operatorname{sgn}(z_e) = -\operatorname{sgn}(r^\star_e)$). If candidate perturbations align with $r^\star_e$ in sign ($|r^\star_e + z_e| = |r^\star_e| + |z_e|$), defect increases strictly even if the null-space condition fails. Therefore, failure of the condition cannot be used to certify nonuniqueness.
- **Residual Uniqueness vs. Potential Uniqueness**: Residual uniqueness in $\mathbb{Q}^E$ does not imply potential uniqueness in $\mathbb{Q}^V$. Because the boundary operator $B$ has kernel $\ker B$ of dimension $k \ge 1$ (potentials constant on connected components), potentials $f^\star + \alpha \mathbf{1}$ yield identical residuals $c - B(f^\star + \alpha \mathbf{1}) = c - Bf^\star = r^\star$.
- **Strictly Positive Penalties Required**: Requires $w_e > 0$ for all $e \in E$. If unpenalized edges ($w_e = 0$) were present, perturbations on zero-penalty edges could preserve defect, violating uniqueness.
- **Finite Graphs Only**: Applies to 1-cochains on finite 1-dimensional cell complexes with rational edge data.
- **No Machine Learning Claims**: Does not evaluate token logits, attention patterns, or language model representations.

## Claim Hygiene Summary

1. **What it supports**: Demonstrates in this finite graph model with strictly positive rational edge weights that if an optimal residual vector $r^\star$ with support $S$ satisfies the weighted null-space property ($\sum_{e \in S} w_e |z_e| < \sum_{e \notin S} w_e |z_e|$ for all nonzero $z \in \operatorname{im} B$), then $r^\star$ is uniquely the optimal residual in $c + \operatorname{im} B$. Supported by reverse triangle inequality norm decomposition and consistent with manuscript triangle witness tests and independent rational grid checks.
2. **What it does not support**: Does not support the claim that the weighted null-space condition is necessary for uniqueness; failure of a sufficient condition is not a nonuniqueness certificate; does not assert potential uniqueness (potentials retain component-wise gauge freedom); does not apply to graphs with non-positive (zero or negative) edge weights; does not evaluate continuous differential forms or language model token distributions.
3. **Narrowest defensible claim**: For any finite directed graph with strictly positive rational weights $w_e > 0$, an optimal residual $r^\star \in \arg\min_{r \in c + \operatorname{im} B} \|r\|_{1, w}$ with support $S$ is the unique minimizer in $c + \operatorname{im} B$ whenever every nonzero coboundary $z \in \operatorname{im} B \setminus \{0\}$ satisfies $\sum_{e \in S} w_e |z_e| < \sum_{e \notin S} w_e |z_e|$.
4. **Next test needed**: Derivation ATL-P001-007 (Strict rational descent alone does not imply finite termination: single-edge sequence $D_t = 2^{-t}$ exhausts fuel without reaching minimum).

## Cross-References & Provenance

- Archive Claim: [ATL-P001-006](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers)
- Paper Claim: [PFP001-06](../../atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/paper_claim_ledger.md?plain=1#L18)
- DAG Review Node: `PAPER001-WEIGHTED-NULL-SPACE-UNIQUENESS`
- Review Registry: `dag/reviews/additional_paper_001_support.json`
- Pull Request: #117 (placeholder / assigned upon creation)
