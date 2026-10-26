# Lesson 000.18 -- The Stubborn Cycle: Cohomology $H^1$ and Non-Exactness

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_18_the_stubborn_cycle.ipynb](../notebooks/lesson_000_18_the_stubborn_cycle.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. Homology ($H_1$) vs. Cohomology ($H^1$)
- 2. Graph Non-Exactness: Why Nonzero Circulation Obstructs Potentials
- 3. The Filled-Face Qualification
- 4. Diagnostic Probe (2026 Micro-Attention Check)
- 5. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from algebraic topology specifications (Hatcher Ch. 3).
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. Homology ($H_1$) vs. Cohomology ($H^1$)

[Declared] In algebraic topology, lower indices denote **chains and homology**, while upper indices denote **cochains and cohomology**:
- **Chains and Homology ($H_1$):**
  $C_1(G)$ consists of directed geometric paths and cycles. The boundary operator $\partial_1: C_1 \to C_0$ decreases dimension.
  The first homology group is:
  $$H_1(G) = \ker \partial_1 / \text{im } \partial_2.$$
- **Cochains and Cohomology ($H^1$):**
  $C^1(G)$ consists of scalar assignments (step heights) on edges. The coboundary operator $d^0: C^0 \to C^1$ increases dimension ($d^0 \phi(u, v) = \phi(v) - \phi(u)$).
  The first cohomology group is:
  $$H^1(G) = \ker d^1 / \text{im } d^0.$$

## 2. Graph Non-Exactness: Why Nonzero Circulation Obstructs Potentials

[Pinned] On a 1-dimensional graph $G$ with vertices and edges (and no 2-cells):
- Every 1-cochain $c$ is vacuously a cocycle: $\ker d^1 = C^1(G)$ (there are no 2-cells for $d^1$ to evaluate on).
- A 1-cochain $c$ is called **exact** if it can be written as the gradient of a vertex potential:
  $$c = d^0 \phi \quad \text{for some } \phi \in C^0(G; \mathbb{Q}).$$
- **The Non-Exactness Theorem:**
  If a closed cycle $z$ has nonzero circulation $\langle c, z \rangle \ne 0$, then $c$ **cannot be exact**.

### Proof by Contradiction
Suppose there existed a potential $\phi$ such that $c = d^0 \phi$.
Then by the Telescoping Theorem (Lesson 15):
$$\langle c, z \rangle = \langle d^0 \phi, z \rangle = \sum_{e \in z} (\phi(v) - \phi(u)) = 0.$$
But for our triangle fixture $c = (2, -1, 0)$, $\langle c, z \rangle = 1 \ne 0$.
Contradiction ($0 = 1$)! Hence, no exact potential exists; the nonzero circulation is an irreducible cohomological obstruction on the graph.

## 3. The Filled-Face Qualification

[Declared] **What happens when a 2-cell (triangle face $F$) is filled?**
- Once a 2-cell $F$ with boundary $\partial_2 F = z$ is attached to the graph:
  $$d^1 c(F) = \langle c, \partial_2 F \rangle = \langle c, z \rangle = 1 \ne 0.$$
- Because $d^1 c(F) \ne 0$, $c$ is **not a cocycle** on the filled 2-complex ($c \notin \ker d^1$).
- Therefore, on a filled triangle, $c$ does *not* represent a cohomology class in $H^1$!
Understanding whether the complex is a 1-skeleton graph or a filled 2-simplex is essential to avoid conflating cocycles with curvature.

## 4. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** On a 1D graph with no 2-cells (or for 1-cocycles in general), which mathematical group represents 1-cocycles modulo vertex coboundaries?

- **A:** $H_1$ (first homology).
- **B:** $H^1$ (first cohomology).
- **C:** $\pi_1$ (fundamental group).

*(Correct answer: **B**. In general 2-complexes, 1-cochains modulo coboundaries form the quotient space $C^1 / \text{im } d^0$, while cohomology requires cocycles: $H^1 = \ker d^1 / \text{im } d^0$. On a 1D graph without 2-cells, every 1-cochain is automatically a cocycle, so $C^1 = \ker d^1$ and the two spaces coincide. On a filled triangle, non-closed cochains have classes in $C^1 / \text{im } d^0$ but not in $H^1$.)*

## 5. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** Can you build a staircase of three steps where each step goes up or down, but when you return to the start you are higher than before, without any tricks?
2. **Exercise 2 (Age 15):** Try solving for $\phi = (\phi_0, \phi_1, \phi_2)$ such that $d\phi = (2, -1, 0)$. Show that summing the three equations yields $0 = 1$.
3. **Exercise 3 (Age 500):** Verify that on the filled triangle with face $F$, the coboundary $d^1 c(F)$ evaluates to exactly the circulation 1.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction as Q

# 1. Algebraic proof of non-exactness
# System:
# phi_1 - phi_0 = 2
# phi_2 - phi_1 = -1
# phi_0 - phi_2 = 0
# Sum of left sides: (phi_1 - phi_0) + (phi_2 - phi_1) + (phi_0 - phi_2) = 0
# Sum of right sides: 2 + (-1) + 0 = 1
sum_lhs = 0
sum_rhs = Q(2) + Q(-1) + Q(0)
assert sum_lhs != sum_rhs
assert sum_rhs == Q(1)

# 2. Filled-face coboundary evaluation
# d^1 c(F) = <c, boundary_2(F)> = circulation(c, z)
d1_c_face = sum_rhs
assert d1_c_face == Q(1)
print("Cohomology H^1 non-exactness and filled-face coboundary verified successfully!")
```
</details>
