# Lesson 300.13 — 4-Manifold Complexes on S^4

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_300_13_4_manifold_complexes_on_s_4.ipynb](../notebooks/lesson_300_13_4_manifold_complexes_on_s_4.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** C_4 -> C_3 -> C_2 -> C_1 -> C_0 on hollow 5-simplex

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of 4-manifold complexes on s^4.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of 4-manifold complexes on s^4 over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** How many 4-faces does a simplex on 6 vertices have?

- **A:** 6. Binomial(6, 5) = 6. This count is not a Betti number.
- **B:** 5. One per vertex of a smaller simplex.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that c_4 -> c_3 -> c_2 -> c_1 -> c_0 on hollow 5-simplex continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
def binomial(top, choose):
    value = 1
    for step in range(choose):
        value = value * (top - step) // (step + 1)
    return value

assert binomial(5, 4) == 5
print("A 4-simplex has 5 tetrahedral faces")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `Demo 9` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
