# Lesson 300.11 — Discrete Bianchi Identity in Degree 3

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_300_11_discrete_bianchi_identity_in_degree_3.ipynb](../notebooks/lesson_300_11_discrete_bianchi_identity_in_degree_3.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Proving d_2 d_1 = 0 on hollow 4-simplices S^3

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of discrete bianchi identity in degree 3.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of discrete bianchi identity in degree 3 over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** After the cancelling face orientations, what is the edge boundary?

- **A:** The zero 6-tuple.
- **B:** A nonzero 2-chain.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that proving d_2 d_1 = 0 on hollow 4-simplices s^3 continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
faces = {"012": {0: 1, 3: 1, 1: -1}}
total = {edge: 0 for edge in range(6)}
for signs in faces.values():
    for edge, sign in signs.items():
        total[edge] += sign
assert tuple(total[edge] for edge in range(6)) != (0, 0, 0, 0, 0, 0)
print("One face is not a closed surface")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `Demo 7` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
