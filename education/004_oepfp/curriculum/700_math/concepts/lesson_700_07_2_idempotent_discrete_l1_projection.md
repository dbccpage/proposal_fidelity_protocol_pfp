# Lesson 700.07 -- 2. Idempotent Discrete L1 Projection $P_S^2 = P_S$

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_700_07_2_idempotent_discrete_l1_projection.ipynb](../notebooks/lesson_700_07_2_idempotent_discrete_l1_projection.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## 2. Idempotent Discrete L1 Projection $P_S^2 = P_S$

The projection operator $P_S$ finds the optimal potentials $f^*$:
$$P_S(c) = c - \delta f^*$$
It satisfies mathematical **idempotence**:
$$P_S(P_S(c)) = P_S(c)$$
Applying the projection once eliminates all solvable defect; applying it a second time makes zero further change.

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.
## Anchors

- Former notebook: `05_discrete_l1_coboundary_projection`
- The code checks one finite example. It is not a general proof.

## Exercise

Change one declared input in the code cell. The check should fail for the wrong object and pass for the finite example written here.

Tower files for this sitting:

- [research/mssn_sn_tower/math/symbol_game/readme.md](../../../../../research/mssn_sn_tower/math/symbol_game/readme.md)
- [research/mssn_sn_tower/math/symbol_game/2_math_cochains_repairs_and_quotients.md](../../../../../research/mssn_sn_tower/math/symbol_game/2_math_cochains_repairs_and_quotients.md)

Frontier sitting already on disk: [N3_simplices_and_exact_betti_numbers.md](../../600_mssn_frontier/N3_simplices_and_exact_betti_numbers/N3_simplices_and_exact_betti_numbers.md). It is a different folder. This lesson does not replace it.
