# Lesson 200.05 — Constructive Difference Setoids

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_200_05_constructive_difference_setoids.ipynb](../notebooks/lesson_200_05_constructive_difference_setoids.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Homotopy Type Theory identity paths and primitive differences

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of constructive difference setoids.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of constructive difference setoids over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** How many classes does union(0, 1), union(1, 2) leave on {0, 1, 2, 3}?

- **A:** 2. {0, 1, 2} and {3}.
- **B:** 4. Unions do not merge classes.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that homotopy type theory identity paths and primitive differences continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
parent = {item: item for item in range(4)}

def find(item):
    while parent[item] != item:
        parent[item] = parent[parent[item]]
        item = parent[item]
    return item

def union(left, right):
    parent[find(left)] = find(right)

union(0, 1)
union(1, 2)
union(2, 3)
assert len({find(item) for item in range(4)}) == 1
print("One more union collapses the remainder")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `07_constructive_hott` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
