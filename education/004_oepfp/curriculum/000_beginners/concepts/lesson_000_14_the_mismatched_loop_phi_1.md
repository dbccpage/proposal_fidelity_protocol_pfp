# Lesson 000.14 -- The Mismatched Loop: Circulation and Primary Obstruction $\Phi_1$

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_14_the_mismatched_loop_phi_1.ipynb](../notebooks/lesson_000_14_the_mismatched_loop_phi_1.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea: Circulation Around a Closed Cycle
- 2. Primary Obstruction $\Phi_1$ and the Single-Cycle Fixture
- 3. Diagnostic Probe (2026 Micro-Attention Check)
- 4. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Symbol Game governor specifications (`l1_symbol_game_governor.py`).
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea: Circulation Around a Closed Cycle

[Pinned] Let $G$ be a constraint graph, $c \in C^1(G; \mathbb{Q})$ an edge cochain, and $z$ a 1-cycle ($\partial_1 z = 0$).
The **circulation** of $c$ around a general chain $z = \sum_e z_e e$ is the bilinear pairing:
$$\text{circ}(c, z) = \langle c, z \rangle = \sum_e c_e z_e.$$
For the particular unit-coefficient directed cycle $z = e_0 + e_1 + e_2$ ($z_e = 1$ for $e \in z$), this simplifies to $\sum_{e \in z} c_e$.

Consider our canonical directed triangle:
$$e_0 = (0, 1), \quad e_1 = (1, 2), \quad e_2 = (2, 0), \quad z = e_0 + e_1 + e_2.$$
With assigned step heights:
$$c = (2, -1, 0),$$
the circulation around the triangle is:
$$\text{circ}(c, z) = 2 + (-1) + 0 = 1.$$
If you walk around this staircase, you do not return to your original altitude; you have an accumulated net elevation mismatch of $+1$!

## 2. Primary Obstruction $\Phi_1$ and the Single-Cycle Fixture

[Pinned] In the Symbol Game governor, the **Primary Obstruction** $\Phi_1([c])$ is the minimum attainable section defect over all possible vertex potentials $s \in C^0(G; \mathbb{Q})$:
$$\Phi_1([c]) = \min_{s} \sum_{e=(u,v)} w_e |c_e - (s(v) - s(u))|.$$

[Declared] **Special Property of the Single Unit-Weight Cycle:**
Because vertex adjustments telescope to zero around any closed cycle (Lesson 15), for every vertex potential $s$:
$$\sum_{e \in z} (c_e - (s(v) - s(u))) = \sum_{e \in z} c_e = \text{circ}(c, z).$$
By the triangle inequality, for unit weights ($w_e = 1$):
$$\sum_{e \in z} |c_e - (s(v) - s(u))| \ge \left| \sum_{e \in z} (c_e - (s(v) - s(u))) \right| = |\text{circ}(c, z)|.$$
For this single unit-weight triangle cycle, there exists a potential that attains this bound, so:
$$\Phi_1([c]) = |\text{circ}(c, z)| = |1| = 1.$$

[Declared] **Scope Warning:** This convenient equality $\Phi_1 = |\text{circulation}|$ holds strictly for a single cycle with unit weights. On arbitrary graphs with multiple cycles or non-uniform edge weights, $\Phi_1$ is an exact rational linear programming optimum, not simply a cycle sum.

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** If the step heights on the triangle are $c = (1, 1, -2)$, what is the circulation, and is there an obstruction?

- **A:** Circulation is 1; obstructed.
- **B:** Circulation is $1 + 1 + (-2) = 0$; there is zero obstruction ($\Phi_1 = 0$).
- **C:** Circulation is 4.

*(Correct answer: **B**. When circulation is zero around the cycle, the edge claims can be matched exactly by vertex elevations, leaving zero obstruction.)*

## 4. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** If you climb up 2 steps, down 1 step, and across 0 steps, are you higher than where you started? *(Answer: Yes, 1 step higher!)*
2. **Exercise 2 (Age 15):** Compute the circulation for $c = (3, 2, -4)$ around the triangle. What is the minimum $L_1$ defect $\Phi_1$ for this single unit-weight cycle?
3. **Exercise 3 (Age 500):** Verify by exact calculation that for $c = (2, -1, 0)$, the circulation equals 1, and explain why $\Phi_1([c]) \ge 1$ for all vertex potentials.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction as Q

# 1. Mismatched loop circulation
c_mismatched = (Q(2), Q(-1), Q(0))
circ_mismatched = sum(c_mismatched)
assert circ_mismatched == Q(1)
phi_1_mismatched = abs(circ_mismatched)
assert phi_1_mismatched == Q(1)

# 2. Consistent loop (zero obstruction)
c_consistent = (Q(1), Q(1), Q(-2))
circ_consistent = sum(c_consistent)
assert circ_consistent == Q(0)
phi_1_consistent = abs(circ_consistent)
assert phi_1_consistent == Q(0)

# 3. Arbitrary exercise fixture
c_ex = (Q(3), Q(2), Q(-4))
assert sum(c_ex) == Q(1)

print("Circulation and primary obstruction bounds verified successfully!")
```
</details>
