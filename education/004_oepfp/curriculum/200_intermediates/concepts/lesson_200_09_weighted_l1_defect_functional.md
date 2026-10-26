# Lesson 200.09 — Weighted L1 Defect Functional

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_200_09_weighted_l1_defect_functional.ipynb](../notebooks/lesson_200_09_weighted_l1_defect_functional.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Phi_1(c) = min_alpha ||c - delta^0 alpha||_{1, W}

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of weighted l1 defect functional.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of weighted l1 defect functional over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What is the minimum L1 distance from (1, 0, 0) to a triangle coboundary?

- **A:** 1. Gauge-fixed search with alpha0 = 0 attains it.
- **B:** 0. One vertex shift clears the edge.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that phi_1(c) = min_alpha ||c - delta^0 alpha||_{1, w} continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction

def defect(cochain, alpha):
    coboundary = (alpha[1] - alpha[0], alpha[2] - alpha[1], alpha[0] - alpha[2])
    return sum(abs(cochain[index] - coboundary[index]) for index in range(3))

cochain = (Fraction(1), Fraction(1), Fraction(1))
scores = [
    defect(cochain, (Fraction(0), Fraction(i), Fraction(j)))
    for i in range(-3, 4)
    for j in range(-3, 4)
]
assert min(scores) == 3
print("Circulation 3 cannot fall below L1 3")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `l1_governor.py` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
