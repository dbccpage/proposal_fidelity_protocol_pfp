# Lesson 300.16 — Fibrations and Dependent Contexts

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_300_16_fibrations_and_dependent_contexts.ipynb](../notebooks/lesson_300_16_fibrations_and_dependent_contexts.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Dependent contexts as fibred categories over discrete sites

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of fibrations and dependent contexts.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of fibrations and dependent contexts over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What are the fiber sizes of color over {{(0, a), (1, a), (2, b)}}?

- **A:** (2, 1) for a and b.
- **B:** (3, 0). Every point has the same color.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that dependent contexts as fibred categories over discrete sites continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
points = ((0, "a"), (1, "b"), (2, "c"))
fibers = {}
for _base, color in points:
    fibers[color] = fibers.get(color, 0) + 1
assert tuple(fibers[color] for color in ("a", "b", "c")) == (1, 1, 1)
print("Three singleton fibers")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `Demo 8 / MSS-22` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
