# Lesson 200.10 -- Holonomy on Directed Graphs: Non-Abelian Link Transports and Multi-Simplex Hinge Loops

AuthorityEffect: None.

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_200_10_holonomy_on_directed_graphs.ipynb](../notebooks/lesson_200_10_holonomy_on_directed_graphs.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea: From Scalar Circulation to Non-Abelian Holonomy
- 2. Gauge Connections on Directed Graphs and Multi-Simplex Complexes
- 3. The 4D Regge Hinge Holonomy and Lean 4 Countermodel Parity
- 4. Diagnostic Probe (2026 Micro-Attention Check)
- 5. Exercises (Ages 5 to 500)

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Regge calculus and Lean 4 specifications (`Level21DiscreteRegge.lean`, `stage_021.py`).
> - **[Executed]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea: From Scalar Circulation to Non-Abelian Holonomy

[Declared] In Track 000, we defined holonomy on a 1D graph as the scalar circulation $\langle c, z \rangle = \sum_{e \in z} c(e)$ of an edge cochain $c \in C^1(G; \mathbb{Q})$ around a cycle $z$. Because addition in $\mathbb{Q}$ is commutative, the order in which edges were traversed did not affect the sum.

In higher-degree geometric and gauge systems—such as non-abelian lattice gauge theories and 4D Regge calculus—link values are **group elements** $U_e \in G$ (such as rotation matrices in $SO(4)$) rather than scalar numbers. Traversing a loop requires **path-ordered matrix multiplication**:
$$H(\gamma) = \mathcal{P} \prod_{e \in \gamma} U_e = U_{e_k} \cdots U_{e_2} U_{e_1}.$$
Because matrix multiplication is non-abelian ($A B \ne B A$), loop holonomy is strictly sensitive to path ordering.

## 2. Gauge Connections on Directed Graphs and Multi-Simplex Complexes

[Pinned] Let $K$ be a simplicial complex. In higher dimensions, holonomy does not circle around isolated 1D vertices; it encircles **codimension-2 hinges**:
- In a 2D surface, codimension-2 hinges are **0D vertices**.
- In a 3D manifold, codimension-2 hinges are **1D edges**.
- In a 4D Regge complex, codimension-2 hinges are **2D triangular faces (bones)**, around which 4-simplices fit.

A discrete gauge connection assigns to each directed interface an element of a Lie group $G$. Reversing an edge replaces the transport with its group inverse:
$$U_{v \to u} = U_{u \to v}^{-1} = U_{u \to v}^T \quad (\text{for orthogonal groups like } SO(4)).$$

A hinge loop is flat (has zero curvature) if and only if the ordered holonomy is the identity:
$$H(\text{loop}) = I.$$

## 3. The 4D Regge Hinge Holonomy and Lean 4 Countermodel Parity

[Pinned] A critical error in naive geometric modeling is asserting loop flatness solely because the scalar sum of rotation angles around the hinge vanishes.

In formal Lean 4 kernel development [`Level21DiscreteRegge.lean`](../../../../../../lean4/Level21DiscreteRegge.lean), this misconception is refuted by an exact finite countermodel:
1. Define two quarter-turn rotation matrices in $SO(4)$ with exact integer entries:
   - $R_{yz}$: rotates in the $yz$-plane.
   - $R_{xz}$: rotates in the $xz$-plane.
2. Form the commutator loop $U = R_{yz} R_{xz} R_{yz}^{-1} R_{xz}^{-1}$.
3. The scalar angle sum of the loop in quarter-turns is:
   $$\text{scalar\_sum} = 1 + 1 - 1 - 1 = 0.$$
4. Yet the ordered product evaluates to:
   $$U = \begin{pmatrix} 0 & -1 & 0 & 0 \\ 0 & 0 & -1 & 0 \\ 1 & 0 & 0 & 0 \\ 0 & 0 & 0 & 1 \end{pmatrix} \ne I_{4\times 4}.$$

Lean 4 theorem `scalar_sum_does_not_certify_closure` confirms that $U \ne I$ despite $\text{scalar\_sum} = 0$. A governor evaluating 4D Regge complexes must inspect path-ordered matrix holonomy, not scalar projections.

## 4. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** Why does a loop of link transports in $SO(4)$ with vanishing scalar angle sum $\sum \theta_i = 0$ fail to guarantee zero curvature around a 4D Regge hinge?

- **A:** The link transports might have fractional dimensions.
- **B:** Rotations in $SO(4)$ are non-abelian; the commutator $[R_A, R_B] \ne 0$ causes the path-ordered product $R_A R_B R_A^{-1} R_B^{-1}$ to deviate from $I$ even when exponents cancel.
- **C:** The 4-simplex has 5 vertices.

*(Correct answer: **B**. Lean 4 theorem `scalar_sum_does_not_certify_closure` establishes that ordered matrix holonomy is required for non-abelian gauge groups.)*

## 5. Exercises (Ages 5 to 500)

1. **Exercise 1 (Age 5):** Turn a toy car 90 degrees right, tilt it forward, turn it 90 degrees left, and tilt it back. Is it pointing in the original direction, or did it twist? *(Answer: It twisted! Rotations in 3D and 4D do not commute!)*
2. **Exercise 2 (Age 15):** In Python, construct the $4 \times 4$ integer matrices $R_{yz}$ and $R_{xz}$, and verify that both are orthogonal with determinant 1.
3. **Exercise 3 (Age 500):** Compute the ordered loop product $U = R_{yz} R_{xz} R_{yz}^T R_{xz}^T$ and demonstrate that $U \ne I_4$, while verifying that an abelian sub-loop (e.g. $R_{yz} R_{yz}^T$) evaluates identically to $I_4$.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction as Q

def mat_mul4(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(4)) for j in range(4)] for i in range(4)]

def transpose4(A):
    return [[A[j][i] for j in range(4)] for i in range(4)]

def identity4():
    return [[1 if i == j else 0 for j in range(4)] for i in range(4)]

# 1. Exact SO(4) rotation generators from Level21DiscreteRegge.lean
R_yz = [
    [1,  0,  0, 0],
    [0,  0, -1, 0],
    [0,  1,  0, 0],
    [0,  0,  0, 1],
]

R_xz = [
    [ 0, 0, 1, 0],
    [ 0, 1, 0, 0],
    [-1, 0, 0, 0],
    [ 0, 0, 0, 1],
]

I4 = identity4()

# 2. Verify orthogonality: M * M^T == I
assert mat_mul4(R_yz, transpose4(R_yz)) == I4
assert mat_mul4(R_xz, transpose4(R_xz)) == I4

# 3. Commutator loop holonomy: R_yz * R_xz * R_yz^T * R_xz^T
loop = mat_mul4(mat_mul4(mat_mul4(R_yz, R_xz), transpose4(R_yz)), transpose4(R_xz))

# Scalar exponent sum: +1 +1 -1 -1 = 0
scalar_sum = 1 + 1 - 1 - 1
assert scalar_sum == 0

# Non-abelian holonomy refutes closure
assert loop != I4
assert loop[0] == [0, -1, 0, 0]

# 4. Genuinely closed abelian sub-loop
closed_loop = mat_mul4(R_yz, transpose4(R_yz))
assert closed_loop == I4

print("Non-abelian gauge holonomy and Lean 4 countermodel parity verified successfully!")
```
</details>

---

## Integrated System Verification

This lesson integrates the system integration test suite from `04_frustrated_spin_triangle.ipynb`:
**Topic:** Enumerate the finite obstruction independently (Frustrated Spin Triangle & Binary Holonomy)

### Key Verified Invariants:
- Deterministic boundary / primal-dual certificate verification under exact rational constraints.
- Fail-stop refusal testing on corrupted bounds, missing boundaries, or broken dual closure.
- Full parity between exact discrete representations and algorithmic solvers.

