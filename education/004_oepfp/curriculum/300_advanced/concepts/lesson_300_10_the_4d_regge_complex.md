# Lesson 300.10 — The 4D Regge Complex

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_300_10_the_4d_regge_complex.ipynb](../notebooks/lesson_300_10_the_4d_regge_complex.ipynb) and run the cells from top to bottom. Stop when the checks pass.

Short narrated videos of this same material go in [videos/](../videos/). Each clip teaches one idea from this page, stays short enough to finish without a break, and adds nothing beyond this page and the notebook. The folder stays empty until those clips are recorded.

If the page is long, read one section and run the matching notebook cells. Leave the next section for the next sitting.

## Sections

- 1. The Big Idea
- 2. Scope & Claim Boundary
- 3. Diagnostic Probe (2026 Micro-Attention Check)
- 4. Student Exercise
- 5. Anchors

> **Claim-typing legend**
> - **[Pinned]**: reproduced from verified checked-in Grammar 000 fixtures or papers.
> - **[Proved]**: verified by deterministic Python execution in this notebook.
> - **[Declared]**: pedagogical convention or beginner framing.
> - **[Open]**: questions left for future exploration.

## 1. The Big Idea

**Core Concept:** Regular 4-simplex metric geometry with det(CM) = -5

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of the 4d regge complex.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of the 4d regge complex over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What Cayley-Menger determinant does the orthogonal corner with legs 1 return?

- **A:** 8, which equals 288 times (1/6) squared for this tetrahedron.
- **B:** -5. Every 4-simplex uses that assigned determinant.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that regular 4-simplex metric geometry with det(cm) = -5 continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction
def det_over_q(matrix):
    size = len(matrix)
    acc = [[Fraction(entry) for entry in row] for row in matrix]
    sign = Fraction(1)
    for col in range(size):
        pivot = next((r for r in range(col, size) if acc[r][col] != 0), None)
        if pivot is None:
            return Fraction(0)
        if pivot != col:
            acc[col], acc[pivot] = acc[pivot], acc[col]
            sign = -sign
        scale = acc[col][col]
        for other in range(col + 1, size):
            factor = acc[other][col] / scale
            for cursor in range(col, size):
                acc[other][cursor] -= factor * acc[col][cursor]
    diagonal = sign
    for col in range(size):
        diagonal *= acc[col][col]
    return diagonal
assigned = Fraction(-5)
matrix = [
    [0, 1, 1, 1, 1],
    [1, 0, 1, 1, 1],
    [1, 1, 0, 2, 2],
    [1, 1, 2, 0, 2],
    [1, 1, 2, 2, 0],
]
assert det_over_q(matrix) != assigned
print("The computed determinant is not the assigned -5")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `regge_4d_fixture.md` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
