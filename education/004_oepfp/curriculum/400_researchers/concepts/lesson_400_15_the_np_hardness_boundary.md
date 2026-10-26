# Lesson 400.15 — The NP-Hardness Boundary

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_400_15_the_np_hardness_boundary.ipynb](../notebooks/lesson_400_15_the_np_hardness_boundary.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Troyer-Wiese theorem: why general sign problems remain NP-hard

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of the np-hardness boundary.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of the np-hardness boundary over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** How many sign patterns of length 3 does this notebook enumerate?

- **A:** 8. Enumeration of 8 patterns does not decide a general hardness theorem.
- **B:** All patterns of every length.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that troyer-wiese theorem: why general sign problems remain np-hard continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
patterns = [(first, second) for first in (-1, 1) for second in (-1, 1)]
assert len(patterns) == 4
print("Length 2 has four patterns")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `Troyer-Wiese 2005` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
