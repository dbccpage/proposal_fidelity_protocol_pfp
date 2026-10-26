# Lesson 700.06 -- 1. Simplicial Cochains and Coboundary Operators

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_700_06_1_simplicial_cochains_coboundary_operators.ipynb](../notebooks/lesson_700_06_1_simplicial_cochains_coboundary_operators.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

# 05 - Discrete L_1 Coboundary Projection vs. Continuous Softmax Cancellation

> **Claim-typing legend**
> - **[Pinned]**: reproduced from a named local script, benchmark, or cryptographic receipt (`code/*.json`).
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a grammar, carrier alphabet, cost, or objective chosen by the model.
> - **[Open]**: an obligation for which this package supplies no proof or exhaustive decision.

*Simplicial Cochains, Primary Obstruction Norm Phi_1, and Idempotent Projection P_S^2 = P_S*

---

## 1. Simplicial Cochains and Coboundary Operators

Let $G = (V, E)$ be a finite directed graph.
- **0-Cochains $C^0(G)$**: Functions $f: V \to \mathbb{Q}$ assigning rational potentials to vertices.
- **1-Cochains $C^1(G)$**: Functions $c: E \to \mathbb{Q}$ assigning rational values (claims) to directed edges.

The simplicial **coboundary operator** $\delta: C^0(G) \to C^1(G)$ computes edge differences:
$$(\delta f)(u \to v) = f(v) - f(u)$$

### The Primary Obstruction $\Phi_1$
Given edge claims $c \in C^1(G)$, the section defect measures the difference between asserted claims and any exact gradient $\delta f$:
$$\Phi_1([c]) = \min_{f \in C^0(G)} \sum_{e=(u,v) \in E} w_e |c_e - (f(v) - f(u))|$$

If $\Phi_1 = 0$, the edge claims are **cycle-consistent**: traversing any closed cycle sums to zero.
If $\Phi_1 > 0$, the graph contains **frustrated cycles** — a direct mathematical witness of contradictory deduction.

## Anchors

- Former notebook: `05_discrete_l1_coboundary_projection`
- The code checks one finite example. It is not a general proof.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.

Tower files for this sitting:

- [research/mssn_sn_tower/math/symbol_game/readme.md](../../../../../research/mssn_sn_tower/math/symbol_game/readme.md)
- [research/mssn_sn_tower/math/symbol_game/2_math_cochains_repairs_and_quotients.md](../../../../../research/mssn_sn_tower/math/symbol_game/2_math_cochains_repairs_and_quotients.md)

Frontier sitting already on disk: [N3_simplices_and_exact_betti_numbers.md](../../600_mssn_frontier/N3_simplices_and_exact_betti_numbers/N3_simplices_and_exact_betti_numbers.md). It is a different folder. This lesson does not replace it.
