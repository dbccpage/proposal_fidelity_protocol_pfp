# Lesson 000.12 -- Walking in a Circle: 1-Cycles and Boundary Vanishing

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_12_walking_in_a_circle.ipynb](../notebooks/lesson_000_12_walking_in_a_circle.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea: The 1-Cycle Condition $\partial_1 z = 0$
- 2. Cycle vs. Homology Class: The Role of 2-Cells
- 3. Diagnostic Probe (2026 Micro-Attention Check)
- 4. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from simplicial homology specifications.
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea: The 1-Cycle Condition $\partial_1 z = 0$

[Pinned] A **1-cycle** $z = \sum_e a_e e \in Z_1(G; \mathbb{Z})$ is an algebraic 1-chain whose simplicial boundary vanishes identically:
$$\partial_1 z = 0.$$
While an elementary closed loop of directed edges is the primary concrete example, a 1-cycle in general can be a formal linear combination of multiple loops.

Consider a directed triangle with vertices $\{0, 1, 2\}$ and three directed edges:
$$e_0 = (0, 1), \quad e_1 = (1, 2), \quad e_2 = (2, 0).$$
Let $z = e_0 + e_1 + e_2$. Computing the boundary:
$$\partial_1 z = (v_1 - v_0) + (v_2 - v_1) + (v_0 - v_2) = \{0: 0, 1: 0, 2: 0\}.$$
Every vertex has exactly one incoming edge (+1) and one outgoing edge (-1). The net coefficient at every vertex is identically zero: $\partial_1 z = 0$.

In contrast, an open path such as $p = e_0 + e_1 = (0, 1) + (1, 2)$ has boundary $\partial_1 p = \{0: -1, 1: 0, 2: +1\} \ne 0$.

## 2. Cycle vs. Homology Class: The Role of 2-Cells

[Declared] **Crucial Distinction in Algebraic Topology:**
- **On a 1-dimensional graph (no 2-cells/faces):**
  There are no 2-cells, so the boundary of 2-simplices is empty: $B_1 = \text{im } \partial_2 = 0$.
  Therefore, the first homology group is identical to the cycle group:
  $$H_1(G) = \ker \partial_1 / \text{im } \partial_2 = Z_1 / 0 = Z_1.$$
  Every nonzero closed cycle generates a nontrivial homology class in the graph.
- **When faces (2-cells) are added:**
  If we fill the interior of the triangle with a 2-cell $F$, then by definition $\partial_2 F = e_0 + e_1 + e_2 = z$.
  In this filled 2-complex, the cycle $z$ is now a boundary ($z \in B_1$), so its homology class in $H_1$ collapses to zero: $[z] = 0 \in H_1$.

Distinguishing whether a 2-cell is attached or absent is essential before making claims about homology!

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** On a 1D graph with no 2-cells (faces), why does every closed cycle $z \ne 0$ represent a nontrivial homology class in $H_1$?

- **A:** Because graphs always have Euler characteristic 1.
- **B:** Because without 2-cells, $\text{im } \partial_2 = 0$, so no cycle can be the boundary of a face.
- **C:** Because cycles are always trees.

*(Correct answer: **B**. $H_1 = \ker \partial_1 / \text{im } \partial_2$. With no 2-cells present, $\text{im } \partial_2 = 0$, making every cycle homologically nontrivial on the graph.)*

## 4. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** If you walk from room 0 to room 1 to room 2 and back to room 0, did you end up where you started?
2. **Exercise 2 (Age 15):** In Python, construct the boundary of $z = (0, 1) + (1, 2) + (2, 0)$ and assert that every vertex evaluates to 0.
3. **Exercise 3 (Age 500):** If an edge is accidentally reversed: $z' = (0, 1) + (1, 2) + (0, 2)$, compute $\partial_1 z'$. Does it vanish? Test it below!

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
def boundary_1d(edges, vertices):
    b = {v: 0 for v in vertices}
    for u, v in edges:
        b[u] -= 1
        b[v] += 1
    return b

# 1. Closed oriented cycle vanishes
z_oriented = [(0, 1), (1, 2), (2, 0)]
b_z = boundary_1d(z_oriented, [0, 1, 2])
assert b_z == {0: 0, 1: 0, 2: 0}

# 2. Mis-oriented cycle fails to vanish
z_misoriented = [(0, 1), (1, 2), (0, 2)]
b_mis = boundary_1d(z_misoriented, [0, 1, 2])
assert b_mis != {0: 0, 1: 0, 2: 0}
assert b_mis == {0: -2, 1: 0, 2: 2}

print("1-Cycle boundary vanishing and orientation verified successfully!")
```
</details>
