# Lesson 000.11 -- Two Dots and a Bridge: The Simplicial Boundary Operator

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_11_two_dots_and_a_bridge.ipynb](../notebooks/lesson_000_11_two_dots_and_a_bridge.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea: Directed Edges as 1-Chains
- 2. The Simplicial Boundary Operator $\partial_1$
- 3. Diagnostic Probe (2026 Micro-Attention Check)
- 4. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in simplicial cochain and graph specifications (`l1_symbol_game_governor.py`).
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea: Directed Edges as 1-Chains

[Declared] In our discrete graph adapter, we study constraint networks built from vertices $V$ and directed edges $E$:
- A vertex $v \in V$ is a 0-simplex (a dot).
- A directed edge $e = (u, v)$ is a 1-simplex (a bridge directed from source $u$ to target $v$).
- Formal integer linear combinations of edges are called **1-chains** $C_1(G; \mathbb{Z})$.

## 2. The Simplicial Boundary Operator $\partial_1$

[Pinned] The fundamental boundary operator on 1-simplices is:
$$\partial_1(u, v) = v - u.$$
As a formal linear combination of vertices (a 0-chain), the boundary assigns:
- Target vertex $v$: coefficient $+1$.
- Source vertex $u$: coefficient $-1$.
- All other vertices: coefficient $0$.

### Complete Signed Vector vs. Tautological Sum
A common beginner mistake is to test only `sum(boundary.values()) == 0`.
Notice that `sum([-1, 1]) == 0`, but so does `sum([1, -1])` (the reversed edge) or `sum([0, 0])` (no boundary) or `sum([-5, 5])` (wrong scale)!
To honestly verify the boundary operator, we must compare the **complete signed vector/dictionary**:
$$\partial_1(0, 1) = \{0: -1, 1: +1\}.$$
For the reversed edge $-e = (1, 0)$:
$$\partial_1(1, 0) = \{0: +1, 1: -1\}.$$

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** Why is checking `sum(boundary.values()) == 0` insufficient to verify that an edge $(0, 1)$ was computed correctly?

- **A:** Because vertices cannot have positive numbers.
- **B:** Because the reversed edge $(1, 0)$ and arbitrary scaled values like $\{-5, +5\}$ also sum to zero while having wrong signs or magnitudes.
- **C:** Because boundary sums are always nonzero.

*(Correct answer: **B**. Conservation of total sum is necessary, but only matching the complete signed vector $\{0: -1, 1: +1\}$ verifies orientation and scale.)*

## 4. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** If an arrow points from dot 0 to dot 1, where did it start (minus) and where did it end (plus)?
2. **Exercise 2 (Age 15):** Compute the boundary of a path of two edges: $e_1 = (0, 1)$ and $e_2 = (1, 2)$. What is the net coefficient at the interior vertex 1?
3. **Exercise 3 (Age 500):** Implement a general function `boundary_1d(edges)` and verify that it matches the exact vertex dictionary for any directed 1-chain.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
# Function to compute exact simplicial boundary
def boundary_1d(edges, vertices):
    b = {v: 0 for v in vertices}
    for u, v in edges:
        b[u] -= 1
        b[v] += 1
    return b

# 1. Single edge boundary
b_single = boundary_1d([(0, 1)], [0, 1])
assert b_single == {0: -1, 1: 1}

# 2. Reversed edge boundary
b_rev = boundary_1d([(1, 0)], [0, 1])
assert b_rev == {0: 1, 1: -1}

# 3. Two-edge path: interior vertex 1 cancels to 0
b_path = boundary_1d([(0, 1), (1, 2)], [0, 1, 2])
assert b_path == {0: -1, 1: 0, 2: 1}

print("Simplicial boundary operator verified with complete signed vectors!")
```
</details>
