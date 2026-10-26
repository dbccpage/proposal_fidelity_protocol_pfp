# Lesson 400.08 — The H^1 to Density Bridge

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_400_08_the_h_1_to_density_bridge.ipynb](../notebooks/lesson_400_08_the_h_1_to_density_bridge.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** The Phi_1 residual as a density carrier rho(h) = |h><h| / <h, h>

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of the h^1 to density bridge.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of the h^1 to density bridge over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What diagonal projector does the circulation vector (1, 1, 1) determine?

- **A:** (1/3, 1/3, 1/3). The squared norm is 3.
- **B:** (1, 1, 1). Normalization is optional.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that the phi_1 residual as a density carrier rho(h) = |h><h| / <h, h> continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction
circulation = (Fraction(1), Fraction(0), Fraction(0))
squared = sum(value * value for value in circulation)
diagonal = tuple(value * value / squared for value in circulation)
assert diagonal == (Fraction(1), Fraction(0), Fraction(0))
print("A one-edge vector is already pure")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `density_from_h1.rs` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
