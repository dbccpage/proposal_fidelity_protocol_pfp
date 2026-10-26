# Lesson 400.11 — Physics of the Fermion Sign Problem

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_400_11_physics_of_the_fermion_sign_problem.ipynb](../notebooks/lesson_400_11_physics_of_the_fermion_sign_problem.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Exponential signal-to-noise collapse <sign> -> 0 in volume and beta

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of physics of the fermion sign problem.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of physics of the fermion sign problem over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What is the average sign of the two-term set {{+1, -1}}?

- **A:** 0. Two terms are not a volume or temperature limit.
- **B:** 1. Signs are ignored by the average.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that exponential signal-to-noise collapse <sign> -> 0 in volume and beta continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction
signs = (Fraction(1), Fraction(1))
assert sum(signs) / len(signs) == 1
print("Two positive terms average to 1")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `MERON_COLLAPSE.md` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
