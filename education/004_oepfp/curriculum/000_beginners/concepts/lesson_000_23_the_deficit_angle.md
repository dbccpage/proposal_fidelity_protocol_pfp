# Lesson 000.23 -- The Deficit Angle: Discrete 2D Curvature vs. 4D Non-Abelian Regge Holonomy

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_23_the_deficit_angle.ipynb](../notebooks/lesson_000_23_the_deficit_angle.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea: Measuring Discrete Curvature
- 2. 2D Vertex Deficit and the Discrete Gauss-Bonnet Identity
- 3. The 2D vs. 4D Curvature Firewall: Why Scalar Sums Fail in Regge Calculus
- 4. Diagnostic Probe (2026 Micro-Attention Check)
- 5. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Regge calculus and Lean 4 specifications (`Level21DiscreteRegge.lean`).
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea: Measuring Discrete Curvature

[Declared] In smooth differential geometry, curvature is described by Riemann curvature tensors and differential forms. In discrete geometry, space is composed of flat simplices glued together.

How can flat pieces produce curved space?
The curvature does not live in the interior of the flat pieces; it concentrates entirely on **lower-dimensional hinges and boundaries**, measured by a **deficit angle**.

## 2. 2D Vertex Deficit and the Discrete Gauss-Bonnet Identity

[Pinned] On a triangulated 2-dimensional surface, curvature concentrates at **0-dimensional vertices**:
1. Around an interior vertex $v$, several flat triangles meet.
2. Let $\theta_v(\sigma)$ be the corner angle of triangle $\sigma$ at vertex $v$.
3. The **deficit angle** $\epsilon(v)$ is the shortfall from a full turn ($2\pi$ radians, or $1$ complete turn):
   $$\epsilon(v) = 2\pi - \sum_{\sigma \ni v} \theta_v(\sigma).$$

### Geometric Cases
- **Flat ($E^2$):** Exactly 6 equilateral triangles meet at a vertex: $\sum \theta = 6 \times (\pi/3) = 2\pi$. The deficit is $\epsilon(v) = 0$.
- **Convex / Spherical ($S^2$):** Fewer than 6 equilateral triangles meet. For example, in a regular tetrahedron, 3 equilateral triangles meet at each of the 4 vertices:
  $$\sum \theta_v = 3 \times \frac{\pi}{3} = \pi \implies \epsilon(v) = 2\pi - \pi = \pi \quad (\text{or } 1/2 \text{ turn}).$$
- **Discrete Gauss-Bonnet Theorem (Closed Surfaces):**
  For a closed, orientable piecewise Euclidean 2-manifold without boundary:
  $$\sum_{v \in V} \epsilon(v) = 2\pi \chi(M)$$
  where $\chi(M) = V - E + F$ is the Euler characteristic.
  For the regular tetrahedron: $V=4, E=6, F=4 \implies \chi = 2$.
  $$\sum_{v=1}^4 \epsilon(v) = 4 \times \pi = 4\pi = 2\pi(2).$$
  For surfaces with boundary (such as disks), boundary vertices carry an exterior turning angle $\kappa_g(v) = \pi - \sum \theta_v$ (or in full turns, $\frac{1}{2} - \sum \tau_v$), and Gauss-Bonnet includes the boundary sum:
  $$\sum_{v \in \text{int}} \epsilon(v) + \sum_{v \in \partial} \kappa_g(v) = 2\pi \chi(M).$$

## 3. 2D vs. 4D Curvature: Hinges, Planes, and Ordered Holonomy in Euclidean 4D Regge Geometry

[Pinned] In 2D, curvature concentrates at 0D vertices. In higher-dimensional discrete differential geometry (such as Euclidean 4D Regge calculus at Stage 21):

1. **Curvature Resides on 2D Triangular Hinges (Bones):**
   In 4-dimensional Regge simplicial geometry, curvature concentrates on 2-dimensional triangular faces (hinges or bones), around which 4-simplices meet. An individual hinge has a scalar deficit angle and a specified normal 2-plane of rotation (as formulated by Regge, and Hamber & Kagel).
2. **Rotations in $SO(4)$ and Loop Transport:**
   Transport around a single isolated hinge is a planar rotation. However, when transporting a frame around a general loop that traverses multiple hinges oriented in different planes, rotation matrices must be composed in path order.
   In 2D, all rotations commute ($SO(2)$ is abelian). In 4D, Euclidean rotations form the non-abelian group $SO(4)$. While commuting pairs exist (e.g., any rotation commutes with itself or rotations in orthogonal planes), $SO(4)$ is non-abelian in general: there exist rotations in $SO(4)$ whose ordered commutator is non-trivial despite a cancelling scalar angle list.
3. **Formal Specification (`Level21DiscreteRegge.lean`):**
   Formal Lean theorem `scalar_sum_does_not_certify_closure` establishes that a scalar sum of angles can vanish along a closed path:
   $$\theta_1 + \theta_2 - \theta_1 - \theta_2 = 0.$$
   Yet the ordered loop product of finite rotation matrices:
   $$R_2 R_1 R_2^{-1} R_1^{-1} \ne I$$
   is **not the identity matrix**!
4. **Exact Rational Educational Fixtures:**
   Generic Regge corner angles and matrix entries are irrational. In this beginner lesson, we use exact rational quarter-turn matrices in coordinate planes and regular polyhedral complexes as deterministic, machine-checkable arithmetic fixtures.

## 4. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** Why can we NOT determine whether transport around a multi-hinge loop in 4D Euclidean discrete geometry is flat by simply verifying that the scalar sum of dihedral angles around the loop equals zero?

- **A:** Because 4D simplices have no angles.
- **B:** Because rotations in $SO(4)$ do not commute in general; there exist rotations in different planes whose ordered matrix holonomy $R_2 R_1 R_2^{-1} R_1^{-1} \ne I$ remains non-trivial even when the scalar sum of angles is zero.
- **C:** Because floating-point numbers round improperly.

*(Correct answer: **B**. Multi-hinge loop holonomy in 4D Euclidean Regge geometry requires path-ordered matrix transport, because $SO(4)$ is non-abelian.)*

## 5. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** Cut out 3 paper triangles and tape their sides together at one point. Can they lie flat on the table, or do they pop up into a tent? *(Answer: They pop up like a tent! The missing space makes the pointy top!)*
2. **Exercise 2 (Age 15):** In Python, calculate the deficit angle for the 4 vertices of a regular tetrahedron and verify that the sum of deficits equals $2\pi \chi$ (or 2 complete turns).
3. **Exercise 3 (Age 500):** Construct two $4 \times 4$ rotation matrices $R_{xy}(\pi/2)$ and $R_{yz}(\pi/2)$. Demonstrate that the scalar angle sum $+1/4 + 1/4 - 1/4 - 1/4 = 0$ in turns, but the matrix commutator loop $R_{yz} R_{xy} R_{yz}^{-1} R_{xy}^{-1} \ne I_{4\times 4}$.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction as Q

# Part 1: 2D Discrete Gauss-Bonnet on Tetrahedron (in turns: 1 turn = 2*pi)
V = 4
E = 6
F = 4
chi = V - E + F
assert chi == 2

# Each equilateral triangle has corner angle 1/6 turn (60 degrees)
angle_per_corner = Q(1, 6)
triangles_per_vertex = 3
sum_angle_at_vertex = triangles_per_vertex * angle_per_corner
assert sum_angle_at_vertex == Q(1, 2)  # 1/2 turn = 180 degrees

deficit_per_vertex = Q(1, 1) - sum_angle_at_vertex
assert deficit_per_vertex == Q(1, 2)

total_deficit = V * deficit_per_vertex
assert total_deficit == Q(2, 1)  # 2 full turns = 4*pi
assert total_deficit == chi * Q(1, 1)  # Gauss-Bonnet verified!

# Part 2: 4D Non-Abelian Holonomy (Level21DiscreteRegge parity)
# Exact rational 4x4 permutation-rotation matrices for 90-degree turns (1/4 turn)
# R_xy rotates e0 -> e1, e1 -> -e0
# R_yz rotates e1 -> e2, e2 -> -e1

def mat_mult(A, B):
    n = len(A)
    return [[sum(A[i][k] * B[k][j] for k in range(n)) for j in range(n)] for i in range(n)]

def identity(n):
    return [[1 if i == j else 0 for j in range(n)] for i in range(n)]

R_xy = [
    [ 0, -1,  0,  0],
    [ 1,  0,  0,  0],
    [ 0,  0,  1,  0],
    [ 0,  0,  0,  1],
]
R_xy_inv = [
    [ 0,  1,  0,  0],
    [-1,  0,  0,  0],
    [ 0,  0,  1,  0],
    [ 0,  0,  0,  1],
]

R_yz = [
    [ 1,  0,  0,  0],
    [ 0,  0, -1,  0],
    [ 0,  1,  0,  0],
    [ 0,  0,  0,  1],
]
R_yz_inv = [
    [ 1,  0,  0,  0],
    [ 0,  0,  1,  0],
    [ 0, -1,  0,  0],
    [ 0,  0,  0,  1],
]

# Scalar angle sum along loop: +1/4 + 1/4 - 1/4 - 1/4 = 0
scalar_sum = Q(1, 4) + Q(1, 4) - Q(1, 4) - Q(1, 4)
assert scalar_sum == Q(0)

# Matrix loop product: R_yz * R_xy * R_yz_inv * R_xy_inv
loop_holonomy = mat_mult(mat_mult(mat_mult(R_yz, R_xy), R_yz_inv), R_xy_inv)
I4 = identity(4)

# Supports Lean 4 theorem: scalar_sum_does_not_certify_closure
assert loop_holonomy != I4
# Explicit non-identity element: vector e0 is transformed
e0 = [1, 0, 0, 0]
transformed_e0 = [sum(loop_holonomy[i][j] * e0[j] for j in range(4)) for i in range(4)]
assert transformed_e0 != e0  # Non-trivial holonomy!

print("2D Gauss-Bonnet and 4D non-abelian holonomy firewall verified successfully!")
```
</details>
