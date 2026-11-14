# PAPER001-DIRECTED-CYCLE-MINIMUM-FORMULA: Directed Cycle Minimum Formula and Manuscript Triangle Witness

AuthorityEffect: None.

- Archive claim: [ATL-P001-004](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers) ("A directed cycle has minimum \(\min_e w_e\,\lvert\sum_e c_e\rvert\); the manuscript triangle costs 6 at zero, 3 at an optimum, and has dual value 3.", [paper_claim_ledger.md:16](../../atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/paper_claim_ledger.md?plain=1#L16))
- Audit derivation node: [PAPER001-DIRECTED-CYCLE-MINIMUM-FORMULA](../../atlas/atlas_claim_ledger.md#part-ii-derivations-recorded-by-the-repository-audit) (`ATL-D-PAPER001-DIRECTED-CYCLE-MINIMUM-FORMULA`)
- Review verdict: `matched` (`states_same_claim_as`)

## Claim

A directed cycle with positive rational edge penalties has quotient minimum obstruction given by:
$$\Phi(c) = \left(\min_{e \in E} w_e\right) \left| \sum_{e \in E} c_e \right|.$$
Furthermore, the manuscript triangle (edges $a \to b, b \to c, c \to a$ with penalties $w = (1, 2, 3)$ and reports $c = (1, 1, 1)$) costs 6 at zero potential, 3 at an optimum potential $s^\star = (0, -2, -1)$, and admits a feasible dual circulation $y = (1, 1, 1)$ of value 3 certifying the minimum with zero duality gap.

## Context & Scope

This derivation analyzes discrete 1-cochain quotient defect on finite 1-dimensional cell complexes (graphs) without 2-cells ($C^2 = 0$).
Specifically, it addresses:
1. Directed simple cycles $C_n = (V, E)$ of length $n \ge 3$ where the cycle rank is $b_1(G) = 1$.
2. The concrete manuscript introductory witness triangle with 3 vertices, non-uniform weights $(1, 2, 3)$, and uniform reports $(1, 1, 1)$.

## Hypotheses & Definitions

- Finite directed cycle $G = (V, E)$ with $n \ge 3$ vertices $v_0, v_1, \dots, v_{n-1}$ and $n$ directed edges $e_k = (v_k, v_{k+1 \pmod n})$.
- Discrete boundary operator / incidence matrix $B: \mathbb{Q}^V \to \mathbb{Q}^E$, where $(Bs)_{u \to v} = s_v - s_u$.
- Strictly positive rational penalties $w_e \in \mathbb{Q}_{>0}$ for all $e \in E$. Let $\rho = \min_{e \in E} w_e > 0$.
- Rational 1-cochain edge reports $c \in \mathbb{Q}^E$.
- Total cycle holonomy $h = \sum_{e \in E} c_e \in \mathbb{Q}$.
- Candidate potential $s \in \mathbb{Q}^V$ (0-cochain), residual vector $r = c - Bs \in \mathbb{Q}^E$, and candidate defect cost $D_c(s) = \sum_{e \in E} w_e |c_e - (Bs)_e|$.
- Quotient obstruction $\Phi(c) = \min_{s \in \mathbb{Q}^V} D_c(s)$.
- Dual circulation space $Z_1(G, w) = \{ y \in \mathbb{Q}^E : B^\top y = 0 \text{ and } |y_e| \le w_e \text{ for all } e \in E \}$.

## Mathematical Derivation

### 1. Directed Cycle Minimum Formula

**Step 1: Holonomy invariance under potential coboundary shifts.**
For any candidate potential $s \in \mathbb{Q}^V$, the sum of potential differences around the closed directed cycle telescopes to zero:
$$\sum_{k=0}^{n-1} (Bs)_{e_k} = \sum_{k=0}^{n-1} (s_{v_{k+1}} - s_{v_k}) = (s_{v_1} - s_{v_0}) + (s_{v_2} - s_{v_1}) + \dots + (s_{v_0} - s_{v_{n-1}}) = 0.$$
Therefore, for any residual vector $r = c - Bs$:
$$\sum_{e \in E} r_e = \sum_{e \in E} \left(c_e - (Bs)_e\right) = \sum_{e \in E} c_e - \sum_{e \in E} (Bs)_e = h - 0 = h.$$
The sum of residuals around the cycle is an invariant equal to the total report holonomy $h = \sum_{e \in E} c_e$.

**Step 2: Lower bound on candidate defect cost.**
Let $\rho = \min_{e \in E} w_e > 0$. Because $w_e \ge \rho > 0$ for all $e \in E$ and $|r_e| \ge 0$:
$$D_c(s) = \sum_{e \in E} w_e |r_e| \ge \sum_{e \in E} \rho |r_e| = \rho \sum_{e \in E} |r_e|.$$
By the standard triangle inequality on $\mathbb{Q}$:
$$\sum_{e \in E} |r_e| \ge \left| \sum_{e \in E} r_e \right| = |h|.$$
Multiplying by $\rho > 0$ preserves the inequality:
$$D_c(s) \ge \rho |h| = \left(\min_{e \in E} w_e\right) \left| \sum_{e \in E} c_e \right|.$$
Because this lower bound holds for every candidate potential $s \in \mathbb{Q}^V$:
$$\Phi(c) = \min_{s \in \mathbb{Q}^V} D_c(s) \ge \rho |h|.$$

**Step 3: Constructive primal attainment.**
Select an edge $j \in E$ that attains the minimal penalty, $w_j = \rho = \min_{e \in E} w_e$.
Define target residual vector $r^\star \in \mathbb{Q}^E$ by concentrating the entire holonomy $h$ onto edge $j$:
$$r^\star_j = h, \quad \text{and} \quad r^\star_e = 0 \quad \text{for all } e \neq j.$$
The defect of this target residual is:
$$D(r^\star) = \sum_{e \in E} w_e |r^\star_e| = w_j |h| + \sum_{e \neq j} w_e |0| = \rho |h|.$$
To confirm that $r^\star$ is realized by an admissible potential $s^\star \in \mathbb{Q}^V$, consider fitted reports $c' = c - r^\star$.
The sum of $c'$ around the cycle is:
$$\sum_{e \in E} c'_e = \sum_{e \in E} c_e - \sum_{e \in E} r^\star_e = h - h = 0.$$
Because $\sum_{e \in E} c'_e = 0$, $c' \in \operatorname{im} B$ is an exact 1-coboundary.
Set $s^\star_{v_0} = 0$, and for $k = 0, \dots, n-2$:
$$s^\star_{v_{k+1}} = s^\star_{v_k} + c'_{e_k}.$$
This ensures $(Bs^\star)_{e_k} = s^\star_{v_{k+1}} - s^\star_{v_k} = c'_{e_k}$ for all $k \in \{0, \dots, n-2\}$.
On the closing edge $e_{n-1} = (v_{n-1}, v_0)$:
$$(Bs^\star)_{e_{n-1}} = s^\star_{v_0} - s^\star_{v_{n-1}} = -\sum_{k=0}^{n-2} c'_{e_k} = c'_{e_{n-1}},$$
because the sum over the entire cycle is zero.
Therefore, $Bs^\star = c' = c - r^\star$, meaning $c - Bs^\star = r^\star$.
Evaluating candidate defect yields $D_c(s^\star) = \rho |h|$.
Combined with the lower bound $D_c(s) \ge \rho |h|$, this demonstrates:
$$\Phi(c) = \min_{s \in \mathbb{Q}^V} D_c(s) = \left(\min_{e \in E} w_e\right) \left| \sum_{e \in E} c_e \right|.$$

**Step 4: Uniqueness and optimal face dimension.**
If $h \neq 0$ and the minimal-weight edge $j$ is unique, equality in $w_e |r_e| \ge \rho |r_e|$ forces $r_e = 0$ for all $e \neq j$, so $r^\star$ and fitted edges $c - r^\star$ are uniquely determined.
If multiple edges achieve minimal weight $\rho$, any distribution of $h$ among those minimal-weight edges with matching sign achieves the same objective $\rho |h|$.
In particular, when weights are uniform ($w_e = \rho$ for all $e$), any non-negative partition of $|h|$ across the $n$ edges with common sign $\operatorname{sgn}(h)$ yields an optimal residual:
$$\left\{ r \in \mathbb{Q}^E : \operatorname{sgn}(r_e) = \operatorname{sgn}(h) \text{ and } \sum_{e \in E} |r_e| = |h| \right\}.$$
This set forms an $(n-1)$-dimensional simplex in $\mathbb{Q}^E$. Because cycle rank is $b_1(G) = 1$, this shows in this setting that cycle rank does not bound the dimension of the optimal residual face.

---

### 2. Manuscript Triangle Witness Replay

The manuscript introductory witness specifies:
- Vertices: $V = \{a, b, c\}$.
- Directed edges: $e_1 = (a \to b), e_2 = (b \to c), e_3 = (c \to a)$.
- Penalties: $w = (w_{a \to b}, w_{b \to c}, w_{c \to a}) = (1, 2, 3)$.
- Edge reports: $c = (c_{a \to b}, c_{b \to c}, c_{c \to a}) = (1, 1, 1)$.
- Holonomy sum: $h = 1 + 1 + 1 = 3$.
- Minimal penalty: $\rho = \min(1, 2, 3) = 1$, uniquely achieved on edge $a \to b$.
- Minimum formula prediction: $\Phi(c) = 1 \cdot |3| = 3$.

**Calculation 1: Candidate defect at zero potential $s_0 = (0, 0, 0)$.**
$$(Bs_0)_{a \to b} = 0 - 0 = 0 \implies r_{a \to b} = 1 - 0 = 1.$$
$$(Bs_0)_{b \to c} = 0 - 0 = 0 \implies r_{b \to c} = 1 - 0 = 1.$$
$$(Bs_0)_{c \to a} = 0 - 0 = 0 \implies r_{c \to a} = 1 - 0 = 1.$$
$$D_c(s_0) = 1 \cdot |1| + 2 \cdot |1| + 3 \cdot |1| = 1 + 2 + 3 = 6.$$

**Calculation 2: Candidate defect at optimal potential $s^\star = (0, -2, -1)$.**
$$(Bs^\star)_{a \to b} = s^\star_b - s^\star_a = -2 - 0 = -2 \implies r_{a \to b} = 1 - (-2) = 3.$$
$$(Bs^\star)_{b \to c} = s^\star_c - s^\star_b = -1 - (-2) = 1 \implies r_{b \to c} = 1 - 1 = 0.$$
$$(Bs^\star)_{c \to a} = s^\star_a - s^\star_c = 0 - (-1) = 1 \implies r_{c \to a} = 1 - 1 = 0.$$
$$D_c(s^\star) = 1 \cdot |3| + 2 \cdot |0| + 3 \cdot |0| = 3 + 0 + 0 = 3.$$
This attains the cycle lower bound $\rho |h| = 1 \cdot 3 = 3$.

**Calculation 3: Dual circulation certificate and zero duality gap.**
Let $y = (y_{a \to b}, y_{b \to c}, y_{c \to a}) = (1, 1, 1)$.
1. Flow conservation ($B^\top y = 0$):
   At vertex $a$: $y_{c \to a} - y_{a \to b} = 1 - 1 = 0$.
   At vertex $b$: $y_{a \to b} - y_{b \to c} = 1 - 1 = 0$.
   At vertex $c$: $y_{b \to c} - y_{c \to a} = 1 - 1 = 0$.
   Thus $B^\top y = 0$, confirming $y \in Z_1(G)$ is a balanced circulation.
2. Capacity bounds ($|y_e| \le w_e$ for all $e \in E$):
   $|y_{a \to b}| = 1 \le w_{a \to b} = 1$.
   $|y_{b \to c}| = 1 \le w_{b \to c} = 2$.
   $|y_{c \to a}| = 1 \le w_{c \to a} = 3$.
   All edge capacity constraints are satisfied.
3. Dual objective value:
   $$c^\top y = c_{a \to b} y_{a \to b} + c_{b \to c} y_{b \to c} + c_{c \to a} y_{c \to a} = 1 \cdot 1 + 1 \cdot 1 + 1 \cdot 1 = 3.$$
4. Duality gap:
   $$\text{gap} = D_c(s^\star) - c^\top y = 3 - 3 = 0.$$
   By weak duality, $c^\top y \le D_c(s)$ for every feasible circulation $y$ and potential $s$.
   Because $c^\top y = 3 = D_c(s^\star)$, $s^\star$ is an optimal potential and 3 is the exact quotient minimum.

## Test Witnesses & Verification Evidence

1. **Python manuscript replay**:
   `atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/tests/test_manuscript_witnesses.py`:
   - `test_manuscript_triangle_costs_and_certificate`:
     Asserts `governor.compute_section_defect(governor.section) == 6` (cost at zero potential).
     Asserts `governor.compute_section_defect(best) == 3` for `best = {"a": 0, "b": -2, "c": -1}`.
     Asserts `verify_phi_1_certificate(VERTICES, TRIANGLE, REPORTS, manual)` for manual dual circulation $(1, 1, 1)$ with dual value 3 and zero gap.
     Asserts `compute_exact_phi_1(VERTICES, TRIANGLE, REPORTS).phi_1 == 3`.
     Asserts exact reports case $(1, 1, -2)$ gives `phi_1 == 0`.
   - `test_demo1_replays_every_manuscript_witness`:
     Replays demo and verifies output contains `DEMO 1 PASSED` with no failures.
   - Command:
     ```bash
     python -m pytest atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/code/tests/test_manuscript_witnesses.py -v
     ```
     Result: 3 passed with zero failures.

2. **Native Rust solver test**:
   `code/rust/core_solvers/src/solver_graph_phi1_distance.rs`:
   - `manuscript_triangle_minimum_is_three`:
     Solves the manuscript triangle via `solve_graph_phi1`, asserting `result.phi1 == "3"` and that the returned gauge potential satisfies residual $1 - (s_b - s_a) = 3$ on edge $a \to b$.
   - Command:
     ```bash
     cargo test --manifest-path code/rust/Cargo.toml -p core_solvers --lib manuscript_triangle_minimum_is_three
     ```
     Result: 1 passed with zero failures.

## Limits and Non-Claims

- Requires strictly positive rational penalties ($w_e > 0$). If zero penalties were admitted, a zero-penalty edge could absorb arbitrary residuals without contributing cost, altering the quotient obstruction.
- Applies to single directed cycles ($b_1(G) = 1$). In general graphs with multiple interlocking cycles, holonomy is distributed according to network circulation rather than a single cycle minimum formula.
- Residual uniqueness holds only when the minimal-weight edge is unique ($h \neq 0$). When minimal weight is shared across edges, optimal residuals form higher-dimensional simplices; cycle rank does not bound optimal residual face dimension.
- Discrete 1-cochain formulation on 1-dimensional graph complexes does not assert continuous differential forms, curvature on smooth manifolds, or continuous Hodge theory.
- Exact rational arithmetic does not assert floating-point machine precision stability or arbitrary numerical tolerances.
- Does not evaluate LLM token probabilities, agent intention, or cryptographic message provenance.

## Claim Hygiene Summary

1. **What it supports**: Demonstrates in this finite graph model with strictly positive rational penalties that a directed cycle has quotient minimum $\Phi(c) = \min_{e \in E} w_e \left|\sum_{e \in E} c_e\right|$; demonstrates by exact rational arithmetic that the manuscript triangle with weights $(1, 2, 3)$ and reports $(1, 1, 1)$ costs 6 at zero potential, 3 at an optimal potential $s^\star = (0, -2, -1)$, and admits a feasible dual circulation $y = (1, 1, 1)$ with dual value 3, establishing zero duality gap. Checked by both Python test witnesses (`test_manuscript_witnesses.py`) and native Rust tests (`manuscript_triangle_minimum_is_three`).
2. **What it does not support**: Does not support claims for graphs with non-positive (zero or negative) penalties; does not generalize the single-cycle formula to arbitrary multicycle graphs where cycle interactions require linear programming circulation optimization; does not assert residual uniqueness when multiple edges achieve the minimum weight; does not assert that cycle rank bounds optimal face dimension; does not assert continuous differential geometry or real-world LLM capabilities.
3. **Narrowest defensible claim**: For any finite directed cycle with positive rational weights $w_e > 0$ and rational edge reports $c_e$, the discrete 1-cochain quotient obstruction is $\Phi(c) = (\min_{e \in E} w_e) |\sum_{e \in E} c_e|$; for the specific 3-cycle with weights $(1, 2, 3)$ and reports $(1, 1, 1)$, candidate defect is 6 at $s = (0, 0, 0)$, 3 at $s = (0, -2, -1)$, and the dual circulation $(1, 1, 1)$ achieves matching objective 3.
4. **Next test needed**: Derivation ATL-P001-005 (Paper 001 residual sparsity existence bound: some optimal residual is supported on at most $|E| - \operatorname{rank} B$ edges).

## Cross-References & Provenance

- Archive Claim: [ATL-P001-004](../../atlas/atlas_claim_ledger.md#part-i-claims-of-the-archived-papers)
- Paper Claim: [PFP001-04](../../atlas/archive/pfp/001_pfp_discrete_cochain_retraction_and_toy_involutions/paper_claim_ledger.md?plain=1#L16)
- DAG Review Node: `PAPER001-DIRECTED-CYCLE-MINIMUM-FORMULA`
- Review Registry: `dag/reviews/additional_paper_001_support.json`
