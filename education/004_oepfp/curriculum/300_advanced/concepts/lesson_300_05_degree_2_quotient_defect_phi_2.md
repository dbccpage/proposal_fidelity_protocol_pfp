# Lesson 300.05 — Degree-2 Quotient Defect Phi_2

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_300_05_degree_2_quotient_defect_phi_2.ipynb](../notebooks/lesson_300_05_degree_2_quotient_defect_phi_2.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Phi_2(B) = min_A ||B - d_1 A||_{1, W} on 2-cochains

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of degree-2 quotient defect phi_2.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of degree-2 quotient defect phi_2 over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What L1 distance does (1, 0, 0, 0) have from the nearest multiple of (1, 1, 1, 1)?

- **A:** 1, attained at multiple 0.
- **B:** 0. One face value is a coboundary of the 3-simplex.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that phi_2(b) = min_a ||b - d_1 a||_{1, w} on 2-cochains continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction
target = (Fraction(1), Fraction(1), Fraction(1), Fraction(1))
assert sum(abs(target[index] - Fraction(1)) for index in range(4)) == 0
print("The all-ones cochain is exactly one coboundary")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `Phi_2 Calculus` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
