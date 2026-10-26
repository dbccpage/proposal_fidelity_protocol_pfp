# Lesson 700.09 -- 4. Track A — one directed 3-cycle (Paper 033 `play_demo`)

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_700_09_directed_3_cycle_play_demo.ipynb](../notebooks/lesson_700_09_directed_3_cycle_play_demo.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## 4. Track A — one directed 3-cycle (Paper 033 `play_demo`)

The opening cell used a **chorded** triangle $A,B,C$ with a chord $A \to C$ and claims $(1,2,0)$ vs $(1,2,3)$. That cell stays. This section is a **different** graph — the Course I on-ramp example:

- vertices $a,b,c$
- edges $a \to b$ (weight 1), $b \to c$ (weight 2), $c \to a$ (weight 2)
- claims $c = (1,1,1)$
- host $\Phi_1 = 3$  **[Pinned]** `compute_phi1` / `play_demo.py`

Short video of this single example: `notebooks/scenes/three_cycle_phi1.py` (matplotlib+ffmpeg; optional Manim class `ThreeCyclePhi1`).

**Predict-then-run.** Before executing the next cell, write `CONSISTENT` / `CONTRADICTION` and $\Phi_1$. The checked-in values are the worked solution; change a claim without updating them and the cell fails.

## 5. Scope: CAN-Show vs. CANNOT-Show

> **CAN-Show**:
> - Demonstrates that simplicial coboundary operators detect cycle inconsistencies with zero floating-point loss.
> - Demonstrates that $L_1$ projection is idempotent ($P_S^2 = P_S$) on finite graphs.
> - Replays Paper 033 `play_demo.py` on the directed 3-cycle: $\Phi_1 = 3$, a defect-increasing CUT is refused (`DefectIncrease`, `admitted=False`), ExactRepair lands at 0, RETRACT restores 3. **[Pinned]**
> - One-parameter transfer: changing only $c(c \to a)$ from $1$ to $-2$ flips the host class to CONSISTENT with $\Phi_1 = 0$. **[Pinned]**
>
> **CANNOT-Show**:
> - Does not show that every frustrated cycle can be resolved without retracting at least one claim.
> - Does not solve NP-hard combinatorial optimization problems in polynomial time.
> - The 3-cycle is one finite weighted graph. It is not a claim that language models are cochain complexes.

## 6. Student Exercises

### Exercise 05.1: Cycle Frustration
This is the Track A directed cycle (not the chorded opening cell). Edges $a \to b, b \to c, c \to a$, claims $(1,1,1)$. What is the cycle sum, and what does the host return?

<details>
<summary><b>Click to reveal solution</b></summary>
The cycle sum is $1 + 1 + 1 = 3 \neq 0$. Coboundaries have cycle sum 0, so this is not in $B^1$. `compute_phi1` returns $\Phi_1 = 3$ and the host verdict is CONTRADICTION. **[Pinned]**
</details>

### Exercise 05.2: One-parameter transfer
Change exactly one claim so the host class flips to CONSISTENT. Check $\Phi_1$ with `compute_phi1`, not by averaging.

<details>
<summary><b>Click to reveal solution</b></summary>
$c(c \to a) = -2$ gives cycle sum $0$ and $\Phi_1 = 0$ (gauge $f(a)=0, f(b)=1, f(c)=2$). Any other single-claim change that leaves the cycle sum nonzero stays CONTRADICTION.
</details>

## 7. Anchors

- **Paper 032 Sections**: §3.1–§3.3
- **Paper 033**: §5 worked session (`play_demo.py`)
- **Ledger IDs**: `PO032-C29` through `PO032-C36`
- **Code**: `papers/032_the_symbol_game_three_layer_sovereignty_and_discrete_l1_projection/code/l1_symbol_game_governor.py` (`compute_phi1`, module-level)
- **Code**: `papers/033_the_symbol_game_practitioners_field_manual/code/play_demo.py`
- **Video**: `notebooks/scenes/three_cycle_phi1.py` (Track A video 3)

> **Claim-typing legend**
> - **[Pinned]**: taken from a file this repository already has.
> - **[Proved]**: a finite check in this notebook. Not a general proof.
> - **[Declared]**: a carrier, rule, or heading chosen for this sitting.
> - **[Open]**: something this sitting does not decide.
## Anchors

- Former notebook: `05_discrete_l1_coboundary_projection`
- The code checks one finite example. It is not a general proof.

Tower files for this sitting:

- [research/mssn_sn_tower/math/symbol_game/readme.md](../../../../../research/mssn_sn_tower/math/symbol_game/readme.md)
- [research/mssn_sn_tower/math/symbol_game/2_math_cochains_repairs_and_quotients.md](../../../../../research/mssn_sn_tower/math/symbol_game/2_math_cochains_repairs_and_quotients.md)

Frontier sitting already on disk: [N3_simplices_and_exact_betti_numbers.md](../../600_mssn_frontier/N3_simplices_and_exact_betti_numbers/N3_simplices_and_exact_betti_numbers.md). It is a different folder. This lesson does not replace it.
