# Lesson 700.11 -- 2. Machine-Checked Lean 4 Proof

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_700_11_2_machine_checked_lean_4_proof.ipynb](../notebooks/lesson_700_11_2_machine_checked_lean_4_proof.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## 2. Machine-Checked Lean 4 Proof

The names `TotalUnimodularity.incidence_entry_bounds` and `TotalUnimodularity.column_sum_zero` are background. `TotalUnimodularity.lean` was not re-run here. The cell checks that three columns of one matrix each sum to 0:
- **Lean 4 Source**: `lean4/TotalUnimodularity.lean`
- **Theorem**: `TotalUnimodularity.incidence_entry_bounds`
- **Theorem**: `TotalUnimodularity.column_sum_zero`

Every column of $\partial_1$ has exactly one $+1$ and one $-1$, ensuring $\sum_v (\partial_1)_{v, e} = 0$.

## 3. Scope: CAN-Show vs. CANNOT-Show

> **CAN-Show**:
> - The cell checks that three columns of one matrix each sum to 0.
> - `TotalUnimodularity.lean` was not re-run. Strong duality for every integral program is not decided here.
>
> **CANNOT-Show**:
> - Does not show that hyper-graph incidence matrices (arity $k \ge 3$) are totally unimodular.

## 4. Student Exercises

### Exercise 06.1: Submatrix Determinants
Why does Total Unimodularity ensure that solving a system of linear equations $A x = b$ with integer coefficients $A$ and $b$ produces integer solutions?

<details>
<summary><b>Click to reveal solution</b></summary>
By Cramer's rule, the components of the solution $x$ are ratios of determinants: $x_i = \det(A_i) / \det(A)$.
If $A$ is totally unimodular, any non-singular basis submatrix has $\det(A) = \pm 1$.
Since $\det(A_i)$ is an integer and $\det(A) = \pm 1$, the quotient is always an exact integer.
</details>

## 5. Anchors

- **Paper 032 Sections**: §3.4
- **Ledger IDs**: `PO032-C37` through `PO032-C42`
- **Code**: `papers/032.../code/scaling_benchmark_v20.py`
- **Lean 4**: `lean4/TotalUnimodularity.lean`

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.
## Anchors

- Former notebook: `06_total_unimodularity_and_exact_lp_duality`
- The code checks one finite example. It is not a general proof.

Tower files for this sitting:

- [research/mssn_sn_tower/math/symbol_game/readme.md](../../../../../research/mssn_sn_tower/math/symbol_game/readme.md)
- [research/mssn_sn_tower/math/symbol_game/18_math_zero_float_law_and_exact_rational_lp_solvers.md](../../../../../research/mssn_sn_tower/math/symbol_game/18_math_zero_float_law_and_exact_rational_lp_solvers.md)
