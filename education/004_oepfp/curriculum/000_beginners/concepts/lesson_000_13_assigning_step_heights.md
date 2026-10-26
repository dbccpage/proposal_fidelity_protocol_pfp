# Lesson 000.13 -- Assigning Step Heights: 1-Cochains over $\mathbb{Q}$

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_13_assigning_step_heights.ipynb](../notebooks/lesson_000_13_assigning_step_heights.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea: 1-Cochains as Step Heights
- 2. Exact Rational Domain and Reversal Antisymmetry
- 3. Diagnostic Probe (2026 Micro-Attention Check)
- 4. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in simplicial cochain specifications (`l1_symbol_game_governor.py`).
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea: 1-Cochains as Step Heights

[Declared] While a 1-chain is a geometric collection of directed edges, a **1-cochain** $c \in C^1(G; \mathbb{Q})$ is a function that assigns a numerical value (a "step height", "voltage drop", or "relational claim") to each directed edge.

For our canonical directed triangle with edges:
$$e_0 = (0, 1), \quad e_1 = (1, 2), \quad e_2 = (2, 0),$$
we assign rational step heights $c \in \mathbb{Q}^3$:
$$c(e_0) = \frac{2}{1}, \quad c(e_1) = -\frac{1}{1}, \quad c(e_2) = \frac{0}{1}.$$

## 2. Exact Rational Domain and Reversal Antisymmetry

[Pinned] The cochain calculus adheres to two foundational laws:
1. **The Exact Rational Domain Law:**
   All coefficients are elements of the rational field $\mathbb{Q}$, implemented via Python's `fractions.Fraction`. Floating-point numbers are strictly forbidden to eliminate rounding artifacts.
2. **Reversal Antisymmetry:**
   Reversing the orientation of an edge negates its step height:
   $$c(-e) = -c(e), \quad \text{where } -(u, v) = (v, u).$$
   For example, if $c(0, 1) = 2$, then traversing backwards from 1 to 0 has step height $c(1, 0) = -2$.

### The Natural Pairing $\langle c, z \rangle$
The evaluation of cochain $c$ on a 1-chain $z = \sum_e a_e e$ is given by the dual pairing:
$$\langle c, z \rangle = \sum_{e} c(e) a_e \in \mathbb{Q}.$$

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** If directed edge $(0, 1)$ has assigned step height $c(0, 1) = 2$, what is the step height of the reversed traversal $(1, 0)$?

- **A:** $c(1, 0) = 2$.
- **B:** $c(1, 0) = -2$, by reversal antisymmetry.
- **C:** $c(1, 0) = 0$.

*(Correct answer: **B**. By antisymmetry of 1-cochains, traversing an edge in the opposite direction negates the assigned value.)*

## 4. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** If going upstairs is $+2$ steps, what is going downstairs? *(Answer: $-2$ steps!)*
2. **Exercise 2 (Age 15):** Given $c = (2, -1, 0)$ on $((0, 1), (1, 2), (2, 0))$, compute the pairing $\langle c, z \rangle$ for the triangle cycle $z = (1, 1, 1)$.
3. **Exercise 3 (Age 500):** Verify that pairing $\langle c, z \rangle$ is bilinear and exact under `Fraction`.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction as Q

# 1. Exact rational assignments
edges = ((0, 1), (1, 2), (2, 0))
c = { (0, 1): Q(2), (1, 2): Q(-1), (2, 0): Q(0) }

# 2. Reversal antisymmetry
for (u, v), val in list(c.items()):
    c[(v, u)] = -val

assert c[(1, 0)] == Q(-2)
assert c[(2, 1)] == Q(1)
assert c[(0, 2)] == Q(0)

# 3. Pairing with cycle z = (1, 1, 1)
cycle_edges = ((0, 1), (1, 2), (2, 0))
pairing = sum(c[e] for e in cycle_edges)
assert pairing == Q(1)
print("1-Cochains and exact rational antisymmetry verified successfully!")
```
</details>
