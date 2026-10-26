# Lesson 200.22 — Monotone Descent Enforcement

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_200_22_monotone_descent_enforcement.ipynb](../notebooks/lesson_200_22_monotone_descent_enforcement.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** DefectIncrease refusal: rejecting moves that worsen defect

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of monotone descent enforcement.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of monotone descent enforcement over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What refusal does a move from defect 1 to defect 4 receive?

- **A:** DEFECT_INCREASE.
- **B:** ADMITTED, because the move is explicit.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that defectincrease refusal: rejecting moves that worsen defect continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction

def govern(current, proposed):
    if proposed > current:
        return "DEFECT_INCREASE"
    return "ADMITTED"

assert govern(Fraction(4), Fraction(4)) == "ADMITTED"
print("A tie is not an increase")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `Monotone Descent` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
