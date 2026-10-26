# Lesson 300.06 — Metric Simplices and Cayley-Menger

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_300_06_metric_simplices_and_cayley_menger.ipynb](../notebooks/lesson_300_06_metric_simplices_and_cayley_menger.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Computing exact rational Cayley-Menger determinants for simplices

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of metric simplices and cayley-menger.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of metric simplices and cayley-menger over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What is 16 times the squared area of a 3-4-5 triangle, from the Cayley-Menger determinant?

- **A:** 576. The same value is 16 times 36 from the right-triangle formula.
- **B:** -5. That constant is not this triangle.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that computing exact rational cayley-menger determinants for simplices continues to hold under small perturbations.

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
squared = (Fraction(1), Fraction(1), Fraction(1))
matrix = [
    [0, 1, 1, 1],
    [1, 0, squared[0], squared[1]],
    [1, squared[0], 0, squared[2]],
    [1, squared[1], squared[2], 0],
]
cayley = -det_over_q(matrix)
assert cayley != Fraction(576)
assert cayley > 0
print("A different triangle has 16 area^2", cayley)
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `N4_metric_simplices` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |

---

## Integrated System Verification

This lesson integrates the system integration test suite from `01_four_simplex_volume.ipynb`:
**Topic:** Compute a four-simplex volume from squared lengths (Four-Simplex Volume)

### Key Verified Invariants:
- Exact rational evaluation and Cayley-Menger / determinant arithmetic under zero-float constraints.
- Fail-stop refusal testing on corrupted bounds, invalid certificates, or degenerate structures.
- Full verification of discrete invariants across topological and combinatorial models.

