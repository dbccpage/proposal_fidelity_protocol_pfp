# Lesson 000.21 -- Filling the Triangle: 2-Simplices, Boundary Nilpotence, and Coboundary Flux

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_000_21_filling_the_triangle.ipynb](../notebooks/lesson_000_21_filling_the_triangle.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea: Spanning a 1-Cycle with a 2-Simplex
- 2. Simplicial Boundary $\partial_2$ and Nilpotence $\partial_1 \partial_2 = 0$
- 3. 1-Skeleton vs. 2-Complex: Non-Cocycle Status of Circulating Cochains
- 4. Diagnostic Probe (2026 Micro-Attention Check)
- 5. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in simplicial complex specifications.
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea: Spanning a 1-Cycle with a 2-Simplex

[Declared] In lessons 000.11 through 000.19, we studied 1-dimensional graphs consisting of vertices (0-simplices) and directed edges (1-simplices). A loop of edges formed a 1-cycle $z$ with $\partial_1 z = 0$. Because the interior was hollow, circulation could not be bounded by a face.

Now we introduce the **2-simplex** $\Delta^2 = [0, 1, 2]$: a solid triangular sheet whose boundary spans the three edges.

## 2. Simplicial Boundary $\partial_2$ and Nilpotence $\partial_1 \partial_2 = 0$

[Pinned] In algebraic topology, the oriented boundary of a 2-simplex $[v_0, v_1, v_2]$ is defined by the alternating sum of its 1-simplex faces:
$$\partial_2 [v_0, v_1, v_2] = [v_1, v_2] - [v_0, v_2] + [v_0, v_1].$$
Writing this in terms of oriented cycle edges $e_0 = (0, 1)$, $e_1 = (1, 2)$, and $e_2 = (2, 0) = -(0, 2)$:
$$\partial_2 F = e_0 + e_1 + e_2.$$

Applying the 1D boundary operator $\partial_1$ to this 1-chain yields:
$$\partial_1(\partial_2 F) = \partial_1(0, 1) + \partial_1(1, 2) + \partial_1(2, 0) = (1 - 0) + (2 - 1) + (0 - 2) = 0.$$
This demonstrates fundamental **nilpotence**:
$$\partial_1 \circ \partial_2 = 0.$$
The boundary of a boundary is identically zero.

## 3. 1-Skeleton vs. 2-Complex: Non-Cocycle Status of Circulating Cochains

[Pinned] A critical mathematical distinction arises between the hollow graph (1-skeleton) and the filled triangle (2-complex):

1. **On the 1-Skeleton Graph $G$:**
   There are no 2-cells ($C^2(G) = 0$). The coboundary operator $d^1: C^1(G) \to C^2(G)$ maps into the trivial group, so $d^1 c = 0$ for *every* 1-cochain.
   Consequently, every 1-cochain is vacuously a cocycle ($\ker d^1 = C^1(G)$). Non-zero circulation $\langle c, z \rangle \ne 0$ obstructs exactness ($c \notin \text{im } d^0$), establishing a non-trivial cohomology class in $H^1(G)$.

2. **On the Filled 2-Complex $K = \Delta^2$:**
   When the 2-cell $F = [0, 1, 2]$ is attached, $C^2(K) = \text{span}(F)$. The coboundary operator $d^1: C^1(K) \to C^2(K)$ evaluates by duality:
   $$d^1 c(F) = \langle c, \partial_2 F \rangle = \sum_{e \in \partial_2 F} c(e) = \langle c, z \rangle.$$
   If the circulation around the boundary is non-zero (for instance, $\langle c, z \rangle = 1$), then:
   $$d^1 c(F) = 1 \ne 0.$$

Because $d^1 c \ne 0$, **$c$ is NOT a cocycle on the filled 2-complex** ($c \notin \ker d^1$).

The triangle $\Delta^2$ is contractible, so its first cohomology vanishes ($H^1(\Delta^2) = 0$). The non-zero value $d^1 c(F) = 1$ does not represent an unfillable hole; it represents discrete **flux / curvature** penetrating through the 2-cell sheet.

For exact cochains $c = d^0 \phi$, coboundary nilpotence $d^1 \circ d^0 = 0$ ensures:
$$d^1(d^0 \phi)(F) = \langle d^0 \phi, \partial_2 F \rangle = \langle \phi, \partial_1 \partial_2 F \rangle = \langle \phi, 0 \rangle = 0.$$
Exact cochains produce zero flux across any filled 2-cell.

## 4. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** Let $c$ be a 1-cochain with circulation $\langle c, z \rangle = 1$ around the boundary of a filled 2-simplex $F$. Is $c$ a cocycle on the filled 2-complex?

- **A:** Yes, because all 1-cochains are always cocycles.
- **B:** No. On the filled 2-complex, $d^1 c(F) = \langle c, \partial_2 F \rangle = 1 \ne 0$, so $c \notin \ker d^1$. The non-zero value is face flux, not a surviving $H^1$ cohomology class.
- **C:** Yes, because the triangle has 3 edges.

*(Correct answer: **B**. On the filled 2-complex, non-zero circulation across $\partial_2 F$ means $d^1 c(F) \ne 0$; thus $c$ fails to be a cocycle.)*

## 5. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** If you make a loop of wire, water can blow through it as a soap bubble. When you dip it in soapy water, you fill the triangle with a soapy sheet. Does the sheet cover the hole? *(Answer: Yes, the 2-cell sheet fills the hole!)*
2. **Exercise 2 (Age 15):** In Python, define the boundary of face $[0, 1, 2]$ as a dictionary of directed edges and verify that applying $\partial_1$ yields 0 at all three vertices.
3. **Exercise 3 (Age 500):** For cochain $c = (1, 0, 0)$, evaluate the coboundary $d^1 c(F)$ on face $F$, and contrast with $d^1(d^0 \phi)(F)$ for exact cochains to demonstrate $d^1 \circ d^0 = 0$.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction as Q

# 1. Oriented 2-simplex face F = [0, 1, 2]
face = (0, 1, 2)
# Oriented boundary edges: (0, 1), (1, 2), (2, 0)
boundary_2 = {(0, 1): 1, (1, 2): 1, (2, 0): 1}

# 2. Simplicial nilpotence: d_1(d_2 F) = 0
boundary_1 = {0: 0, 1: 0, 2: 0}
for (u, v), coeff in boundary_2.items():
    boundary_1[u] -= coeff
    boundary_1[v] += coeff
assert boundary_1 == {0: 0, 1: 0, 2: 0}  # Nilpotence verified!

# 3. Coboundary evaluation d^1 c(F)
c = {(0, 1): Q(1), (1, 2): Q(0), (2, 0): Q(0)}
flux_F = sum(c[e] * coeff for e, coeff in boundary_2.items())
assert flux_F == Q(1)
# Because flux_F != 0, c is NOT a cocycle on the 2-complex!
is_cocycle_on_2complex = (flux_F == 0)
assert not is_cocycle_on_2complex

# 4. Nilpotence of coboundary d^1(d^0 phi) = 0
phi = {0: Q(3), 1: Q(7), 2: Q(2)}
d0_phi = {(0, 1): phi[1] - phi[0], (1, 2): phi[2] - phi[1], (2, 0): phi[0] - phi[2]}
flux_exact = sum(d0_phi[e] * coeff for e, coeff in boundary_2.items())
assert flux_exact == Q(0)  # d^1(d^0 phi) == 0 verified!

print("2-simplex boundary, nilpotence, and coboundary flux verified successfully!")
```
</details>
