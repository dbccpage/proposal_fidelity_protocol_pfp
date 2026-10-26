# Lesson 300.07 — 2D Apex Angles and Turn-Sixths

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_300_07_2d_apex_angles_and_turn_sixths.ipynb](../notebooks/lesson_300_07_2d_apex_angles_and_turn_sixths.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Exact rational planar angle sums and turn fractions

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of 2d apex angles and turn-sixths.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of 2d apex angles and turn-sixths over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What turn deficit remains when five sixths meet at a vertex?

- **A:** 1/6. This is a turn count, not a measured radian angle.
- **B:** 0. Five copies of 1/6 fill the turn.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that exact rational planar angle sums and turn fractions continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction
turns = tuple(Fraction(1, 6) for _ in range(6))
assert Fraction(1) - sum(turns) == 0
print("Six sixths are a flat turn")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `Apex Angles` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
