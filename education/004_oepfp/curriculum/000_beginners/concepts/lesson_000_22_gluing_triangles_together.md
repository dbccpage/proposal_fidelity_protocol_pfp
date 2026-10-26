# Lesson 000.22 -- Gluing Triangles Together: 2-Complexes, Orientation Cancellation, and Additivity of Flux

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_22_gluing_triangles_together.ipynb](../notebooks/lesson_000_22_gluing_triangles_together.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea: Building 2D Surfaces by Gluing Faces
- 2. Shared Edges and Orientation Cancellation
- 3. Simplicial Stokes' Theorem: Additivity of Face Flux
- 4. Diagnostic Probe (2026 Micro-Attention Check)
- 5. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in simplicial complex specifications.
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea: Building 2D Surfaces by Gluing Faces

[Declared] In Lesson 000.21, we filled a single 3-edge loop with a triangular 2-simplex. In real geometric modeling, computing networks, and physics simulations, surfaces are built by **gluing multiple triangles along shared edges**.

When two triangles share an edge, how does the boundary operator behave? How do the individual fluxes across faces combine to relate to the boundary of the combined surface?

## 2. Shared Edges and Orientation Cancellation

[Pinned] Consider two triangular 2-cells sharing vertices 0 and 1:
- Triangle $F_1 = [0, 1, 2]$ with boundary 1-chain:
  $$\partial_2 F_1 = (0, 1) + (1, 2) + (2, 0).$$
- Triangle $F_2 = [1, 0, 3]$ with boundary 1-chain:
  $$\partial_2 F_2 = (1, 0) + (0, 3) + (3, 1).$$

Notice the shared edge connecting vertices 0 and 1:
- In $F_1$, the edge is oriented from $0$ to $1$: $+(0, 1)$.
- In $F_2$, the edge is oriented from $1$ to $0$: $+(1, 0) = -(0, 1)$.

Now form the combined 2-chain $C = F_1 + F_2$. By linearity of the simplicial boundary operator:
$$\partial_2(F_1 + F_2) = \partial_2 F_1 + \partial_2 F_2 = [(0, 1) + (1, 2) + (2, 0)] + [(1, 0) + (0, 3) + (3, 1)].$$
Because $(0, 1) + (1, 0) = (0, 1) - (0, 1) = 0$, the shared internal edge **cancels identically**:
$$\partial_2(F_1 + F_2) = (1, 2) + (2, 0) + (0, 3) + (3, 1).$$
The boundary of the glued surface is the exterior 4-edge cycle surrounding both triangles. Internal boundaries disappear when orientations are matched.

## 3. Simplicial Stokes' Theorem: Additivity of Face Flux

[Pinned] Let $c \in C^1(K; \mathbb{Q})$ be an edge cochain assigning values to all edges.
The coboundary flux across the composite 2-chain $C = F_1 + F_2$ is:
$$d^1 c(F_1 + F_2) = d^1 c(F_1) + d^1 c(F_2).$$
By the duality $\langle d^1 c, C \rangle = \langle c, \partial_2 C \rangle$:
$$d^1 c(F_1) + d^1 c(F_2) = \langle c, \partial_2(F_1 + F_2) \rangle = \sum_{e \in \text{exterior}} c(e).$$
This identity is the exact discrete **Simplicial Stokes' Theorem**:
The sum of discrete fluxes across all interior 2-cells equals the circulation around the outer boundary cycle.

If triangles glue together to form a **closed, orientable 2-manifold** with coherently chosen face orientations (such as the 4 triangular faces of a regular tetrahedron), every edge is shared by exactly two faces with opposite orientations. Then $\partial_2(\sum F_i) = 0$, forming a closed **rational 2-cycle** (general non-orientable complexes or unoriented gluings do not satisfy this cancellation).

## 4. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** Two adjacent triangles $F_1 = [0, 1, 2]$ and $F_2 = [1, 0, 3]$ share the edge between 0 and 1. What is the coefficient of edge $(0, 1)$ in the boundary $\partial_2(F_1 + F_2)$?

- **A:** 2, because both triangles touch that edge.
- **B:** 0, because $F_1$ traverses $0 \to 1$ and $F_2$ traverses $1 \to 0 = -(0, 1)$, canceling out in the sum.
- **C:** $-1$, because $F_2$ reverses it.

*(Correct answer: **B**. Opposite orientations along shared interior edges cancel algebraically, leaving only the external boundary.)*

## 5. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** If you glue two triangle puzzle pieces together along their sides, can you walk across the line in the middle without leaving the combined piece? *(Answer: Yes, the middle line is inside now; only the outer edges make the border!)*
2. **Exercise 2 (Age 15):** In Python, construct the 2-chain $F_1 + F_2$ and verify that the shared edge has coefficient 0 in the combined boundary.
3. **Exercise 3 (Age 500):** Assign cochain values $c$ to the 5 edges of the two-triangle complex and verify the discrete Stokes' theorem: $d^1 c(F_1) + d^1 c(F_2) == \langle c, \partial_2(F_1 + F_2) \rangle$.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction as Q

# 1. Oriented boundaries of two adjacent triangles
f1_edges = {(0, 1): 1, (1, 2): 1, (2, 0): 1}
f2_edges = {(1, 0): 1, (0, 3): 1, (3, 1): 1}

# 2. Combine into composite 2-chain boundary
combined_boundary = {}
def add_edge(d, u, v, coeff):
    # Normalize (1, 0) as -(0, 1) if u > v
    if u > v:
        key = (v, u)
        sign = -coeff
    else:
        key = (u, v)
        sign = coeff
    d[key] = d.get(key, 0) + sign

for (u, v), coeff in f1_edges.items():
    add_edge(combined_boundary, u, v, coeff)
for (u, v), coeff in f2_edges.items():
    add_edge(combined_boundary, u, v, coeff)

# 3. Assert interior shared edge (0, 1) has cancelled to 0
assert combined_boundary[(0, 1)] == 0

# The non-zero boundary edges form the 4-edge exterior loop
exterior = {e: c for e, c in combined_boundary.items() if c != 0}
assert len(exterior) == 4
assert set(exterior.keys()) == {(1, 2), (0, 2), (0, 3), (1, 3)}

# 4. Discrete Stokes' Theorem check
# Cochain assigning values to canonical edges (u < v)
c = {
    (0, 1): Q(5),  # Interior edge
    (1, 2): Q(2),
    (0, 2): Q(-1), # Note (2, 0) in f1 has sign -1 on (0, 2)
    (0, 3): Q(4),
    (1, 3): Q(-3), # Note (3, 1) in f2 has sign -1 on (1, 3)
}

# Flux across F1: c(0, 1) + c(1, 2) - c(0, 2) = 5 + 2 - (-1) = 8
flux_F1 = c[(0, 1)] * 1 + c[(1, 2)] * 1 + c[(0, 2)] * (-1)
# Flux across F2: -c(0, 1) + c(0, 3) - c(1, 3) = -5 + 4 - (-3) = 2
flux_F2 = c[(0, 1)] * (-1) + c[(0, 3)] * 1 + c[(1, 3)] * (-1)

total_face_flux = flux_F1 + flux_F2
boundary_circulation = sum(c[e] * coeff for e, coeff in combined_boundary.items())

assert flux_F1 == Q(8)
assert flux_F2 == Q(2)
assert total_face_flux == boundary_circulation == Q(10)

print("Orientation cancellation and discrete Stokes' theorem verified successfully!")
```
</details>
