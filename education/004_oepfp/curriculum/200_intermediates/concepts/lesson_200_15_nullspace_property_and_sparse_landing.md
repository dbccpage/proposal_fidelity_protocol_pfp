# Lesson 200.15 — Nullspace Property and Sparse Landing

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_200_15_nullspace_property_and_sparse_landing.ipynb](../notebooks/lesson_200_15_nullspace_property_and_sparse_landing.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Weighted NSP ensuring unique sparse projection landings

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of nullspace property and sparse landing.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of nullspace property and sparse landing over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** How many coefficient vectors in {{-1, 0, 1}}^3 express (1, 0) with one nonzero coefficient?

- **A:** One: the first dictionary column.
- **B:** Three: every column can be scaled.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that weighted nsp ensuring unique sparse projection landings continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
columns = ((1, 0), (0, 1), (1, 1))
target = (1, 0)
found = False
for second in (-1, 0, 1):
    for third in (-1, 0, 1):
        produced = (
            second * columns[1][0] + third * columns[2][0],
            second * columns[1][1] + third * columns[2][1],
        )
        if produced == target and second != 0 and third != 0:
            found = True
assert found
print("A 2-sparse solution also exists, so sparsity is not every solution")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `SparseLanding.lean` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
