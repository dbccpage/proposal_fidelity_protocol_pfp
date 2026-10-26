# Lesson 200.03 — Symmetric Group Actions

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_200_03_symmetric_group_actions.ipynb](../notebooks/lesson_200_03_symmetric_group_actions.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** S_n permutation actions and diagonal element excision

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of symmetric group actions.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of symmetric group actions over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What is the order of the 3-cycle (1, 2, 0)?

- **A:** 3. The third power is the identity.
- **B:** 2. One more application returns the identity.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that s_n permutation actions and diagonal element excision continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
def compose(left, right):
    return tuple(left[right[index]] for index in range(3))

swap = (1, 0, 2)
assert compose(swap, swap) == (0, 1, 2)
assert compose(swap, (1, 2, 0)) != (0, 1, 2)
print("A transposition has order 2 and is not the 3-cycle")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `SnTower.lean` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
