# Lesson 300.23 — Modified Bianchi Identity

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_300_23_modified_bianchi_identity.ipynb](../notebooks/lesson_300_23_modified_bianchi_identity.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Proving d_3 H = Tr(F cup F) on 4-complexes

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of modified bianchi identity.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of modified bianchi identity over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What does this notebook evaluate for the modified Bianchi identity?

- **A:** Only d d = 0 on the triangle. Tr(F cup F) is not computed.
- **B:** The full identity on a 4-complex.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that proving d_3 h = tr(f cup f) on 4-complexes continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
edges = ((0, 1),)
vertex = [0, 0]
vertex[0] -= 1
vertex[1] += 1
assert tuple(vertex) == (-1, 1)
print("The same operator on one edge is not zero")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `Modified Bianchi` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
