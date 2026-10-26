# Lesson 700.10 -- 1. Total Unimodularity (TUM) of the Incidence Matrix

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_700_10_1_total_unimodularity_tum_incidence_matrix.ipynb](../notebooks/lesson_700_10_1_total_unimodularity_tum_incidence_matrix.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

# 06 - Total Unimodularity and Exact Rational LP Duality

> **Claim-typing legend**
> - **[Pinned]**: reproduced from a named local script, benchmark, or cryptographic receipt (`code/*.json`).
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a grammar, carrier alphabet, cost, or objective chosen by the model.
> - **[Open]**: an obligation for which this package supplies no proof or exhaustive decision.

*Node-Edge Incidence Matrix TUM, Zero-Float Rational LP Duality, and Lean 4 Machine Checking*

---

## 1. Total Unimodularity (TUM) of the Incidence Matrix


`TotalUnimodularity.lean` was not re-run in this sitting. The cell checks one integer matrix.

A matrix $M$ is **Totally Unimodular (TUM)** if every square submatrix has determinant in $\{-1, 0, 1\}$.

For any oriented directed graph $G = (V, E)$, the node-edge incidence matrix $\partial_1 \in \mathbb{Z}^{|V| \times |E|}$ is defined by:
$$(\partial_1)_{v, e} = \begin{cases}
+1 & \text{if } v \text{ is the target of edge } e \\
-1 & \text{if } v \text{ is the source of edge } e \\
0 & \text{otherwise}
\end{cases}$$

### Why TUM Matters for Deduction

The Hoffman-Kruskal claim for every directed graph is background. This cell does not decide it.

By the Hoffman-Kruskal theorem, when an incidence matrix is TUM, the vertices of the linear programming constraint polytope are **strictly integral / rational**.
- **No Floating-Point Approximations**: Solutions are exact fractions.
- **Exact Dual Certificates**: Strong duality guarantees that primal minimum defect equals dual maximum circulation:
  $$c^T x^* = b^T y^*$$
with zero duality gap ($c^T x^* - b^T y^* = 0$).

## Anchors

- Former notebook: `06_total_unimodularity_and_exact_lp_duality`
- The code checks one finite example. It is not a general proof.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.

Tower files for this sitting:

- [research/mssn_sn_tower/math/symbol_game/readme.md](../../../../../research/mssn_sn_tower/math/symbol_game/readme.md)
- [research/mssn_sn_tower/math/symbol_game/18_math_zero_float_law_and_exact_rational_lp_solvers.md](../../../../../research/mssn_sn_tower/math/symbol_game/18_math_zero_float_law_and_exact_rational_lp_solvers.md)
