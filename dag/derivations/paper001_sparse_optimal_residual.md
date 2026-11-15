# PAPER001-SPARSE-OPTIMAL-RESIDUAL: Sparse Optimal Residual Existence Bound

AuthorityEffect: None.

- Archive claim: [ATL-P001-005](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers) ("Some optimal residual uses at most \(|E|-\operatorname{rank} B\) edges.", [paper_claim_ledger.md:17](../../atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/paper_claim_ledger.md?plain=1#L17))
- Audit derivation node: [PAPER001-SPARSE-OPTIMAL-RESIDUAL](../../atlas/atlas_claim_ledger.md#part-ii-derivations-recorded-by-the-repository-audit) (`ATL-D-PAPER001-SPARSE-OPTIMAL-RESIDUAL`)
- Review verdict: `matched` (`states_same_claim_as`)

## Claim

For any finite directed graph with strictly positive rational edge weights and rational edge reports, there exists an optimal residual vector that uses at most \(|E|-\operatorname{rank} B\) edges:
$$\min_{r^\star \in \mathcal{R}^\star(c)} |\operatorname{supp}(r^\star)| \le |E| - \operatorname{rank} B = b_1(G),$$
where $\mathcal{R}^\star(c) = \{ c - Bf^\star : f^\star \in \arg\min_{f \in \mathbb{Q}^V} D_c(f) \}$ is the set of optimal residuals, and $b_1(G)$ is the first Betti number (cycle rank) of the graph.

## Context & Scope

This derivation addresses discrete 1-cochain quotient defect minimization on finite 1-dimensional cell complexes (graphs) without 2-cells ($C^2 = 0$).
Specifically, it analyzes:
1. The polyhedral geometry of the residual coset $\mathcal{A} = c + \operatorname{im} B \subset \mathbb{Q}^E$.
2. The existence of basic feasible solutions (extreme points) of the standard-form linear program representing quotient residual defect.
3. The correspondence between extreme points and spanning forest tree potentials.
4. The distinction between an existence bound on basic optimal solutions and claims regarding all minimizers or the optimal-face dimension.

## Hypotheses & Definitions

- Finite directed graph $G = (V, E)$ without self-loops, with $|V|$ vertices, $|E|$ edges, and $k \ge 1$ connected components.
- Boundary operator / incidence matrix $B: \mathbb{Q}^V \to \mathbb{Q}^E$, with $(Bf)_{u \to v} = f_v - f_u$.
- Kernel $\ker B \subset \mathbb{Q}^V$ consisting of potentials constant on each connected component; $\dim \ker B = k$.
- Boundary operator rank: $\operatorname{rank} B = |V| - k$.
- Cycle space: $Z_1(G) = \ker B^\top \subset \mathbb{Q}^E$, with cycle rank $\dim Z_1(G) = |E| - \operatorname{rank} B = |E| - |V| + k = b_1(G)$.
- Edge reports: $c \in \mathbb{Q}^E$ (rational 1-cochain).
- Strictly positive rational penalties: $w_e \in \mathbb{Q}_{>0}$ for all $e \in E$.
- Candidate potential: $f \in \mathbb{Q}^V$ (0-cochain), residual vector $r(f) = c - Bf \in \mathbb{Q}^E$, and candidate defect $D_c(f) = \sum_{e \in E} w_e |c_e - (Bf)_e|$.
- Quotient obstruction: $\Phi(c) = \min_{f \in \mathbb{Q}^V} D_c(f)$.
- Residual support: $\operatorname{supp}(r) = \{ e \in E : r_e \neq 0 \}$.

## Mathematical Derivation

### 1. Quotient Residual Coset Formulation

For any candidate potential $f \in \mathbb{Q}^V$, the residual vector $r = c - Bf$ satisfies:
$$c - r = Bf \in \operatorname{im} B.$$
Therefore, the residual vector $r$ belongs to the affine coset:
$$\mathcal{A} = c + \operatorname{im} B \subset \mathbb{Q}^E.$$
The linear subspace $\operatorname{im} B \subset \mathbb{Q}^E$ has dimension $\operatorname{rank} B = |V| - k$.
Under discrete orthogonality on $\mathbb{Q}^E$, the orthogonal complement of $\operatorname{im} B$ is the cycle space:
$$(\operatorname{im} B)^\perp = \ker B^\top = Z_1(G).$$
Consequently, a vector $r \in \mathbb{Q}^E$ lies in $c + \operatorname{im} B$ if and only if $r - c$ is orthogonal to $Z_1(G)$:
$$\gamma^\top (r - c) = 0 \iff \gamma^\top r = \gamma^\top c \quad \text{for all } \gamma \in Z_1(G).$$
Let $m = \dim Z_1(G) = |E| - \operatorname{rank} B = b_1(G)$.
Selecting a cycle basis $\{\gamma_1, \dots, \gamma_m\}$ of $Z_1(G)$ defines a constraint matrix $C \in \mathbb{Q}^{m \times |E|}$ whose rows are $\gamma_i^\top$.
Because the cycles are linearly independent, $C$ has full row rank $m$.
Let $d = C c \in \mathbb{Q}^m$ denote the report holonomy vector along this basis.
The condition $r \in c + \operatorname{im} B$ is equivalent to the system of $m$ linear constraints:
$$C r = d.$$
The defect minimization problem in residual space is:
$$\min_{r \in \mathbb{Q}^E} \sum_{e \in E} w_e |r_e| \quad \text{subject to} \quad C r = d.$$

### 2. Standard-Form LP and Basic Feasible Solutions

To cast this problem as a standard-form linear program, decompose each residual coordinate into non-negative positive and negative parts:
$$r_e = r_e^+ - r_e^-, \quad r_e^+ \ge 0, \quad r_e^- \ge 0.$$
Because each weight $w_e > 0$ is strictly positive:
At any optimal solution, at most one of $r_e^+$ or $r_e^-$ can be strictly positive:
$$\min(r_e^+, r_e^-) = 0 \quad \text{for all } e \in E.$$
If $\delta = \min(r_e^+, r_e^-) > 0$ were positive for some edge $e$, replacing $r_e^+$ by $r_e^+ - \delta$ and $r_e^-$ by $r_e^- - \delta$ would preserve $r_e^+ - r_e^- = r_e$ (maintaining $C(r^+ - r^-) = d$) while reducing the objective $\sum_e w_e (r_e^+ + r_e^-)$ by $2 w_e \delta > 0$, contradicting optimality.
Consequently, $|r_e| = r_e^+ + r_e^-$ at every optimal solution, and the minimization becomes:
$$\min \sum_{e \in E} w_e (r_e^+ + r_e^-) \quad \text{subject to} \quad C r^+ - C r^- = d, \quad r^+ \ge 0, \quad r^- \ge 0.$$
In block matrix form, define:
$$x = \begin{pmatrix} r^+ \\ r^- \end{pmatrix} \in \mathbb{Q}_{\ge 0}^{2|E|}, \quad \tilde{w} = \begin{pmatrix} w \\ w \end{pmatrix} \in \mathbb{Q}_{> 0}^{2|E|}, \quad A = [C \mid -C] \in \mathbb{Q}^{m \times 2|E|}.$$
The problem takes standard form:
$$\min \tilde{w}^\top x \quad \text{subject to} \quad A x = d, \quad x \ge 0.$$

1. **Feasibility**: Choosing $f = 0$ gives $r = c$. Setting $r^+ = \max(c, 0) \ge 0$ and $r^- = \max(-c, 0) \ge 0$ gives $A x = C(r^+ - r^-) = C c = d$. The feasible polyhedron $\mathcal{P} = \{ x \in \mathbb{Q}^{2|E|} : A x = d, x \ge 0 \}$ is nonempty.
2. **Boundedness**: Because $\tilde{w} > 0$ and $x \ge 0$, $\tilde{w}^\top x \ge 0$ is bounded below by 0.
3. **Attainment at an Extreme Point**: By the fundamental theorem of linear programming, every feasible and bounded linear program in standard form attains its minimum at a basic feasible solution (extreme point of $\mathcal{P}$).
4. **Basic Variable Bound**: In a standard-form LP with $m$ equality constraints, a basic feasible solution corresponds to a set of linearly independent columns of $A$. Because $A$ has $m$ rows, any linearly independent set of columns contains at most $m$ columns.
5. **Support Sparsity**: All nonbasic variables in a basic feasible solution are zero. Therefore, at most $m$ variables among $\{r_e^+, r_e^-\}_{e \in E}$ can be strictly positive in an optimal basic feasible solution $x^\star$.
Because complementarity ensures that $r_e^{\star+}$ and $r_e^{\star-}$ cannot both be positive for the same edge, the number of edges with nonzero residual $r^\star_e = r_e^{\star+} - r_e^{\star-} \neq 0$ is bounded by the number of positive basic variables:
$$|\operatorname{supp}(r^\star)| = |\{ e \in E : r^\star_e \neq 0 \}| \le m = |E| - \operatorname{rank} B = b_1(G).$$
This establishes the existence of an optimal residual with support bounded by $|E| - \operatorname{rank} B$.

### 3. Spanning Forest Basis Interpretation

This polyhedral bound admits an equivalent combinatorial realization via spanning forests:
1. Let $F \subset E$ be a spanning forest of $G$, comprising one spanning tree for each of the $k$ connected components of $G$.
2. The number of edges in $F$ is:
   $$|F| = \sum_{K} (|V(K)| - 1) = |V| - k = \operatorname{rank} B.$$
3. The remaining edges $E \setminus F$ are chord edges (co-forest edges), with cardinality:
   $$|E \setminus F| = |E| - |F| = |E| - \operatorname{rank} B = b_1(G)$.$$
4. Restricting attention to forest edges $F$, the acyclic structure ensures that the system $(B s)_e = c_e$ for all $e \in F$ possesses an exact potential solution $s_F \in \mathbb{Q}^V$ (unique up to one constant reference per component).
5. The tree potential $s_F$ yields zero residual on every forest edge:
   $$r(s_F)_e = c_e - (B s_F)_e = 0 \quad \text{for all } e \in F.$$
6. Therefore, the support of the residual $r(s_F)$ is contained in the chord edge set:
   $$\operatorname{supp}(r(s_F)) \subseteq E \setminus F \implies |\operatorname{supp}(r(s_F))| \le |E \setminus F| = |E| - \operatorname{rank} B.$$
7. Under network simplex duality, extreme points of the potential LP correspond to spanning forest tree potentials. Because the quotient minimum is attained at an extreme point, there exists an optimal spanning forest $F^\star$ whose tree potential $s^\star = s_{F^\star}$ yields an optimal residual $r^\star$ supported on at most $|E| - \operatorname{rank} B$ edges.

### 4. Manuscript Cycle Witness Replay

On the manuscript triangle witness:
- Vertices: $V = \{a, b, c\}$, $|V| = 3$.
- Edges: $E = \{a \to b, b \to c, c \to a\}$, $|E| = 3$.
- Connected components: $k = 1$.
- Boundary operator rank: $\operatorname{rank} B = 3 - 1 = 2$.
- Cycle rank: $|E| - \operatorname{rank} B = 3 - 2 = 1$.
- Reports: $c = (1, 1, 1)$, weights: $w = (1, 2, 3)$.
- Optimal potential: $s^\star = (0, -2, -1)$ yields residuals:
  $$r^\star_{a \to b} = 1 - (-2 - 0) = 3,$$
  $$r^\star_{b \to c} = 1 - (-1 - (-2)) = 0,$$
  $$r^\star_{c \to a} = 1 - (0 - (-1)) = 0.$$
- Residual support: $\operatorname{supp}(r^\star) = \{ a \to b \}$, with $|\operatorname{supp}(r^\star)| = 1 \le |E| - \operatorname{rank} B = 1$.
- The support size exactly equals the cycle rank $b_1(G) = 1$, illustrating agreement with the theoretical bound.

## Test Witnesses & Verification Evidence

1. **Manuscript Witness Replay (`test_manuscript_witnesses.py`)**:
   `atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/tests/test_manuscript_witnesses.py`:
   - `test_manuscript_triangle_costs_and_certificate`: Verifies that the optimal potential $s^\star = (0, -2, -1)$ attains defect 3 on the manuscript triangle, with residuals $(3, 0, 0)$ supported on exactly 1 edge, matching $|E| - \operatorname{rank} B = 3 - 2 = 1$.
   - Command:
     ```bash
     python -m pytest atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/tests/test_manuscript_witnesses.py -v
     ```
     Result: 3 passed with zero failures.

2. **Spanning Tree Solver Enumeration (`symbol_game_governor.py`)**:
   `atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/symbol_game_governor.py:447-454`:
   - The reference solver `compute_exact_phi_1` computes the exact quotient minimum by enumerating spanning trees, constructing tree potentials with zero residual on all tree edges, and selecting the optimal tree.
   - Tested across multicycle degeneracies in `test_review_regressions.py::test_degenerate_multicycle_dual_is_feasible` (4 vertices, 5 edges, $\operatorname{rank} B = 3$, $|E| - \operatorname{rank} B = 2$).
   - Command:
     ```bash
     python -m pytest atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/tests/test_review_regressions.py -v
     ```
     Result: 22 passed with zero failures.

3. **Rust Solver Independent Spanning Forest Verification**:
   `code/rust/core_solvers/src/solver_lp_phi1_quotient.rs`:
   - `solver_agrees_with_independent_spanning_forest_enumeration`: Directly tests that the LP quotient solver matches the independent spanning forest enumeration solver across 3-vertex, 4-vertex, and 6-vertex test graphs.
   - Command:
     ```bash
     cargo test --manifest-path code/rust/Cargo.toml -p core_solvers --lib solver_agrees_with_independent_spanning_forest_enumeration
     ```
     Result: 1 passed with zero failures.

## Limits and Non-Claims

- **Existence Only**: The bound asserts that at least one optimal residual has support bounded by $|E| - \operatorname{rank} B$. It does not assert that all optimal residuals satisfy this bound. Non-basic optimal residuals or interior points of an optimal face may have dense support.
- **Optimal Face Dimension**: Cycle rank $b_1(G) = |E| - \operatorname{rank} B$ does not bound the dimension of the optimal residual face. In an $n$-cycle with uniform weights and nonzero holonomy, the set of optimal residuals forms an $(n-1)$-dimensional simplex, while cycle rank is 1.
- **Positive Penalties Required**: Requires strictly positive rational penalties ($w_e > 0$). If penalties could be zero, zero-cost residuals could be distributed across unpenalized edges without objective penalty.
- **Finite Graphs Only**: The basic feasible solution property and spanning forest decomposition apply to finite 1-dimensional cell complexes with rational edge data.
- **No Machine Learning Claims**: Does not assert that token representations, neural network weights, or language model activations become sparse. Residual optimization on finite graphs is an explicit discrete optimization problem distinct from token decoding.

## Claim Hygiene Summary

1. **What it supports**: Demonstrates in this finite graph model with strictly positive rational edge weights that at least one optimal residual vector uses at most $|E| - \operatorname{rank} B = b_1(G)$ edges. Supported by the basic feasible solution extreme point property of standard-form linear programs and the spanning forest tree potential construction, and is consistent with manuscript test witnesses and solver spanning forest enumerations.
2. **What it does not support**: Does not support sparsity across all optimal residuals; does not bound the dimension of the optimal residual face; does not hold for graphs with non-positive (zero or negative) weights; does not assert sparsity in neural network activations or language model tokens.
3. **Narrowest defensible claim**: For any finite directed graph with strictly positive rational penalties $w_e > 0$ and rational edge reports $c_e$, there exists an optimal residual vector $r^\star \in \arg\min_{r \in c + \operatorname{im} B} \|r\|_{1, w}$ with $|\operatorname{supp}(r^\star)| \le |E| - \operatorname{rank} B$.
4. **Next test needed**: Derivation ATL-P001-006 (Weighted null-space property on residual support suffices for residual uniqueness).

## Cross-References & Provenance

- Archive Claim: [ATL-P001-005](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers)
- Paper Claim: [PFP001-05](../../atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/paper_claim_ledger.md?plain=1#L17)
- DAG Review Node: `PAPER001-SPARSE-OPTIMAL-RESIDUAL`
- Review Registry: `dag/reviews/additional_paper_001_support.json`
- Pull Request: #116 (placeholder / to be assigned upon creation)
