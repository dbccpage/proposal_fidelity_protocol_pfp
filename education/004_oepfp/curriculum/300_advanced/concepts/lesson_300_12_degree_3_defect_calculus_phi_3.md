# Lesson 300.12 — Degree-3 Defect Calculus Phi_3

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_300_12_degree_3_defect_calculus_phi_3.ipynb](../notebooks/lesson_300_12_degree_3_defect_calculus_phi_3.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Quantifying degree-3 curvature defects on hyper-prisms

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of degree-3 defect calculus phi_3.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of degree-3 defect calculus phi_3 over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What is the minimum L1 residual of a 3-cochain (1, 0) against multiples of (1, 1)?

- **A:** 1.
- **B:** 0.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that quantifying degree-3 curvature defects on hyper-prisms continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction
target = (Fraction(2), Fraction(2))
assert abs(target[0] - 2) + abs(target[1] - 2) == 0
print("An exact multiple has residual 0")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `Phi_3 Calculus` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
