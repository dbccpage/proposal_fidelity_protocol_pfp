# Lesson 200.11 — Primal Nearest Coboundary LP

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_200_11_primal_nearest_coboundary_lp.ipynb](../notebooks/lesson_200_11_primal_nearest_coboundary_lp.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Linear programming formulation of optimal vertex cut shifts

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of primal nearest coboundary lp.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of primal nearest coboundary lp over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What primal value does the exhaustive vertex search return for (1, 0, 0)?

- **A:** 1. This search is the primal on a three-vertex gauge slice, not a general solver.
- **B:** 0. Feasibility is free.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that linear programming formulation of optimal vertex cut shifts continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction

def defect(cochain, alpha):
    coboundary = (alpha[1] - alpha[0], alpha[2] - alpha[1], alpha[0] - alpha[2])
    return sum(abs(cochain[index] - coboundary[index]) for index in range(3))

cochain = (Fraction(2), Fraction(0), Fraction(0))
result = min(
    defect(cochain, (Fraction(0), Fraction(i), Fraction(j)))
    for i in range(-4, 5)
    for j in range(-4, 5)
)
assert result == 2
print("Doubling the edge doubles this primal value")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `LP Primal` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
