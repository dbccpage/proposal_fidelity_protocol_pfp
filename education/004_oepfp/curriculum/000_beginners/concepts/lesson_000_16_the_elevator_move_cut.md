# Lesson 000.16 -- The Elevator Move CUT: Local Vertex Perturbations

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_16_the_elevator_move_cut.ipynb](../notebooks/lesson_000_16_the_elevator_move_cut.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea: The Elevator Move on Vertex $v$
- 2. Sign Conventions: Incoming vs. Outgoing Edges
- 3. Diagnostic Probe (2026 Micro-Attention Check)
- 4. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Symbol Game governor specifications (`l1_symbol_game_governor.py`).
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea: The Elevator Move on Vertex $v$

[Pinned] An elementary section move in the Symbol Game is the **Elevator Move (local CUT)**:
We select a single vertex $v$ and perturb its potential by a scalar shift $\delta \in \mathbb{Q}$:
$$\phi(v) \leftarrow \phi(v) + \delta,$$
while keeping all other vertices unchanged.

How does this local shift affect the edge step heights $c' = c + d\phi$?

## 2. Sign Conventions: Incoming vs. Outgoing Edges

[Pinned] By definition, the gradient across a directed edge $(u, w)$ is $d\phi(u, w) = \phi(w) - \phi(u)$.
When we shift vertex $v$ by $+\delta$:
1. **Incoming Edges $(u, v)$:**
   Vertex $v$ is the target.
   $$d\phi(u, v) = (\phi(v) + \delta) - \phi(u) = (\phi(v) - \phi(u)) + \delta.$$
   The step height **increases by $+\delta$**.
2. **Outgoing Edges $(v, w)$:**
   Vertex $v$ is the source.
   $$d\phi(v, w) = \phi(w) - (\phi(v) + \delta) = (\phi(w) - \phi(v)) - \delta.$$
   The step height **decreases by $-\delta$**.
3. **Unconnected Edges $(u, w)$ ($u, w \ne v$):**
   Neither endpoint is shifted. The step height is **unchanged**.

### Local Cancellation Along Cycles
Because any cycle passing through vertex $v$ must enter $v$ through an incoming edge and leave $v$ through an outgoing edge, the net change along the cycle is:
$$(+\delta) + (-\delta) = 0.$$
The local elevator move shifts weight between adjacent edges while preserving total cycle circulation identically.

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** If you lower the potential of vertex 1 by $\delta = -1$, what happens to the incoming edge $(0, 1)$ and outgoing edge $(1, 2)$?

- **A:** Both increase by 1.
- **B:** Incoming edge $(0, 1)$ shifts by $-1$; outgoing edge $(1, 2)$ shifts by $-(-1) = +1$.
- **C:** Neither changes.

*(Correct answer: **B**. Shifting vertex 1 by $-1$ decreases incoming edge $(0, 1)$ by $-1$ and increases outgoing edge $(1, 2)$ by $+1$.)*

## 4. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** If you push down on one end of a see-saw, what happens to the other end?
2. **Exercise 2 (Age 15):** Given initial $c = (2, -1, 0)$ on $((0, 1), (1, 2), (2, 0))$, apply an elevator shift $\delta = -1$ to vertex 1. What are the resulting edge values?
3. **Exercise 3 (Age 500):** Verify that the sum of the resulting edges equals the original circulation of 1.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction as Q

edges = ((0, 1), (1, 2), (2, 0))
c = (Q(2), Q(-1), Q(0))

# Apply elevator move: shift vertex 1 by delta = -1
# phi = (0, -1, 0)
delta = Q(-1)
dphi = (delta, -delta, Q(0))  # incoming (0, 1), outgoing (1, 2), unconnected (2, 0)
assert dphi == (Q(-1), Q(1), Q(0))

c_shifted = tuple(x + d for x, d in zip(c, dphi))
assert c_shifted == (Q(1), Q(0), Q(0))

# Verify incoming decreased, outgoing increased, circulation conserved
assert c_shifted[0] == c[0] + delta
assert c_shifted[1] == c[1] - delta
assert c_shifted[2] == c[2]
assert sum(c_shifted) == sum(c) == Q(1)

print("Elevator move and sign conventions verified successfully!")
```
</details>
