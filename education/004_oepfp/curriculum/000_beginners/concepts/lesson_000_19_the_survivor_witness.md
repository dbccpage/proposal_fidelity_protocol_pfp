# Lesson 000.19 -- The Survivor Witness: Dual Certification and Irreducible Obstruction

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_19_the_survivor_witness.ipynb](../notebooks/lesson_000_19_the_survivor_witness.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea: Dual Certification of Minimal Defect
- 2. The Worked Canonical Triangle Certificate
- 3. Diagnostic Probe (2026 Micro-Attention Check)
- 4. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Symbol Game dual witness specifications (`l1_symbol_game_governor.py`).
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea: Dual Certification of Minimal Defect

[Pinned] How do we know that an obstruction cannot be reduced further on a fixed carrier under vertex-potential moves?
(Note: This certificate establishes minimality under the admitted vertex moves on this declared unit-weight carrier; changes of carrier, weights, or repair family lie outside this certificate's conclusion).
A concrete cycle $z$ with $\partial_1 z = 0$ and $\langle c, z \rangle \ne 0$ proves that $c$ is not exact. But to prove that a specific candidate representative $c'$ has the **exact minimum $L_1$ defect $\Phi_1$**, we construct a **Dual Witness Certificate**:
1. **Dual Lower Bound:**
   A closed cycle $z = (1, 1, 1)$ with $\|z\|_\infty = 1$. By telescoping, for *every* potential $\psi \in C^0(G; \mathbb{Q})$:
   $$\langle c + d\psi, z \rangle = \langle c, z \rangle = 1.$$
   By Hölder's inequality $\|x\|_1 \|z\|_\infty \ge |\langle x, z \rangle|$:
   $$\|c + d\psi\|_1 \ge 1 \quad \text{for all } \psi.$$
   No vertex shift can ever reduce the $L_1$ norm below 1.
2. **Primal Attaining Representative:**
   We exhibit an explicit shifted representative $c' = c + d\phi = (1, 0, 0)$ whose primal $L_1$ norm is:
   $$\|c'\|_1 = |1| + |0| + |0| = 1.$$
3. **Zero Duality Gap:**
   $$\text{Primal}(c') - \text{Dual}(z) = 1 - 1 = 0.$$
   Because the primal value equals the dual lower bound, $c'$ is **certified minimal**.

## 2. The Worked Canonical Triangle Certificate

| Quantity | Initial Representative $c$ | Shifted Attaining $c' = c + d\phi$ |
| :--- | :--- | :--- |
| **Edge Values** | $(2, -1, 0)$ | $(1, 0, 0)$ |
| **Cycle Circulation $\langle c, z \rangle$** | $1$ | $1$ |
| **Representative $L_1$ Mass ($D$)** | $3$ | **$1$** |
| **Minimum $L_1$ Mass ($\Phi_1$)** | $1$ | **$1$** |
| **Movable Excess** | $3 - 1 = 2$ | $1 - 1 = 0$ |
| **Surviving Obstruction** | $1$ | $1$ |

The elevator move removed the movable excess of 2; the surviving obstruction of 1 is certified irreducible by the cycle witness $z$.

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What guarantees that no vertex potential $\psi$ can achieve an $L_1$ defect of 0 on this triangle?

- **A:** We checked 100 random potentials and none worked.
- **B:** The cycle $z=(1, 1, 1)$ has $\partial_1 z = 0$ and $\langle c+d\psi, z \rangle = 1$ for all $\psi$, proving $\|c+d\psi\|_1 \ge 1$ via Hölder's inequality.
- **C:** The graph has 3 vertices.

*(Correct answer: **B**. The closed cycle $z$ supplies an exact dual certificate bounding the $L_1$ norm from below for every possible vertex potential.)*

## 4. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** If 2 parts of the mess can be cleaned up, but 1 part cannot be removed by any vertex shift on this fixed carrier, how much mess is left? *(Answer: 1 part!)*
2. **Exercise 2 (Age 15):** In Python, verify that $c' = (1, 0, 0)$ attains $\|c'\|_1 = 1$, matching the circulation $\langle c, z \rangle = 1$ with zero duality gap.
3. **Exercise 3 (Age 500):** Implement the full dual witness verification script below and assert that $\text{primal} == \text{dual}$.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction as Q

# 1. Triangle setup
edges = ((0, 1), (1, 2), (2, 0))
c = tuple(map(Q, (2, -1, 0)))
phi = tuple(map(Q, (0, -1, 0)))
gradient = tuple(phi[v] - phi[u] for u, v in edges)
shifted = tuple(x + delta for x, delta in zip(c, gradient))

# 2. Dual witness cycle z = (1, 1, 1)
boundary = {v: 0 for v in range(3)}
for u, v in edges:
    boundary[u] -= 1
    boundary[v] += 1
assert boundary == {0: 0, 1: 0, 2: 0}  # Verified closed cycle

# 3. Exact matching certificate
assert shifted == (Q(1), Q(0), Q(0))
assert sum(c) == sum(shifted) == Q(1)
dual_bound = abs(sum(c))               # Dual lower bound from cycle
primal_norm = sum(abs(x) for x in shifted)  # Primal objective
assert dual_bound == primal_norm == Q(1)    # Zero duality gap!

# 4. Movable excess and surviving obstruction
initial_norm = sum(abs(x) for x in c)
movable_excess = initial_norm - primal_norm
surviving_obstruction = primal_norm
assert movable_excess == Q(2)
assert surviving_obstruction == Q(1)

print("Dual certificate, zero duality gap, and survivor witness verified successfully!")
```
</details>
