# Lesson 300.02 — Exact Boundary Operators

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_300_02_exact_boundary_operators.ipynb](../notebooks/lesson_300_02_exact_boundary_operators.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Computing boundary matrices d_k and verifying d_{k-1} d_k = 0

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of exact boundary operators.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of exact boundary operators over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What is the vertex boundary of the triangle's edge boundary?

- **A:** (0, 0, 0).
- **B:** (1, 1, 1).

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that computing boundary matrices d_k and verifying d_{k-1} d_k = 0 continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
edges = ((0, 1), (1, 2))
vertex = [0, 0, 0]
for source, target in edges:
    vertex[source] -= 1
    vertex[target] += 1
assert tuple(vertex) == (-1, 0, 1)
print("An open path is not a cycle")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `Chain Nilpotence` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
