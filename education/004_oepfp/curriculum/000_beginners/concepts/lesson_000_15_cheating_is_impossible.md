# Lesson 000.15 -- Cheating is Impossible: Gauge Transformations and Telescoping Sums

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_15_cheating_is_impossible.ipynb](../notebooks/lesson_000_15_cheating_is_impossible.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea: The Gauge Shift $c \to c + d\phi$
- 2. The Telescoping Invariant Theorem
- 3. Diagnostic Probe (2026 Micro-Attention Check)
- 4. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Symbol Game governor specifications (`l1_symbol_game_governor.py`).
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea: The Gauge Shift $c \to c + d\phi$

[Pinned] Suppose you are unhappy with the step heights $c = (2, -1, 0)$ around your triangle. Can you "flatten" the loop by raising or lowering the floor levels at the vertices?

Let $\phi: V \to \mathbb{Q}$ be a **vertex potential** (an elevation assigned to each dot).
The potential induces a coboundary gradient $d\phi \in C^1(G; \mathbb{Q})$ on directed edges:
$$d\phi(u, v) = \phi(v) - \phi(u).$$
Under the potential transformation, the new edge values become:
$$c' = c + d\phi.$$

## 2. The Telescoping Invariant Theorem

[Pinned] Why is "cheating impossible"? Why can no vertex shift eliminate a nonzero cycle circulation?

Consider any closed directed cycle $z = (v_0, v_1, \dots, v_{k-1}, v_0)$. When we sum the gradient $d\phi$ along the edges of the cycle:
$$\sum_{e \in z} d\phi(e) = (\phi(v_1) - \phi(v_0)) + (\phi(v_2) - \phi(v_1)) + \dots + (\phi(v_0) - \phi(v_{k-1})).$$
Every vertex term appears exactly twice: once with a positive sign (as a target) and once with a negative sign (as a source).
The sum **telescopes to zero identically**:
$$\sum_{e \in z} d\phi(e) = \phi(v_0) - \phi(v_0) = 0.$$

Therefore:
$$\langle c + d\phi, z \rangle = \langle c, z \rangle + \sum_{e \in z} d\phi(e) = \langle c, z \rangle + 0 = \langle c, z \rangle.$$

[Declared] **Core Invariant:**
Vertex gauge shifts can move discrepancies between adjacent edges, but they *strictly preserve* the circulation around every closed cycle. A nonzero cycle circulation cannot be erased by changing vertex elevations.

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** If cycle $z$ has initial circulation $\langle c, z \rangle = 1$, can you find a vertex potential $\phi$ such that $\langle c + d\phi, z \rangle = 0$?

- **A:** Yes, by setting all vertex elevations to 100.
- **B:** No, because the gradient of any potential telescopes to zero around a closed cycle, leaving the circulation strictly invariant.
- **C:** Yes, if we use floating point numbers.

*(Correct answer: **B**. The Telescoping Theorem proves that $\sum_{e \in z} d\phi(e) = 0$ for all vertex potentials $\phi$. The circulation is an exact topological invariant.)*

## 4. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** If you raise the floor in the kitchen by 1 foot, what happens to the step going INTO the kitchen (+1) and the step going OUT of the kitchen (-1)? Do they cancel? *(Answer: Yes, +1 and -1 cancel!)*
2. **Exercise 2 (Age 15):** Given $\phi = (0, -1, 0)$ on vertices $\{0, 1, 2\}$, compute $d\phi$ on edges $((0, 1), (1, 2), (2, 0))$. Show that $\sum d\phi = 0$.
3. **Exercise 3 (Age 500):** Test an arbitrary random potential $\phi = (5, -3, 7)$ and assert that $\sum_{e \in z} d\phi(e) == 0$ and $\langle c + d\phi, z \rangle == \langle c, z \rangle$.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction as Q

edges = ((0, 1), (1, 2), (2, 0))
c = (Q(2), Q(-1), Q(0))

# 1. Standard test potential: phi = (0, -1, 0)
phi_1 = (Q(0), Q(-1), Q(0))
dphi_1 = tuple(phi_1[v] - phi_1[u] for u, v in edges)
assert dphi_1 == (Q(-1), Q(1), Q(0))
assert sum(dphi_1) == Q(0)

c_shifted_1 = tuple(x + d for x, d in zip(c, dphi_1))
assert sum(c_shifted_1) == sum(c) == Q(1)

# 2. Arbitrary potential: phi = (5, -3, 7)
phi_2 = (Q(5), Q(-3), Q(7))
dphi_2 = tuple(phi_2[v] - phi_2[u] for u, v in edges)
assert sum(dphi_2) == Q(0)

c_shifted_2 = tuple(x + d for x, d in zip(c, dphi_2))
assert sum(c_shifted_2) == sum(c) == Q(1)

print("Telescoping sum and circulation invariance verified successfully!")
```
</details>
