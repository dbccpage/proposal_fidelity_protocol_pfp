# Lesson 200.13 — Total Unimodularity of Networks

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_200_13_total_unimodularity_of_networks.ipynb](../notebooks/lesson_200_13_total_unimodularity_of_networks.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Why discrete network flow problems always have integer solutions

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of total unimodularity of networks.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of total unimodularity of networks over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** Are all 2 by 2 minors of this triangle incidence in {{-1, 0, 1}}?

- **A:** Yes. This one matrix has that minor set.
- **B:** No. Network incidence always has a minor of 2.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that why discrete network flow problems always have integer solutions continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
matrix = ((-2, 1, 0), (0, -1, 1), (1, 0, -1))
minor = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
assert minor == 2
assert minor not in (-1, 0, 1)
print("Replacing -1 by -2 produces minor", minor)
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `TUM Lemma` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
