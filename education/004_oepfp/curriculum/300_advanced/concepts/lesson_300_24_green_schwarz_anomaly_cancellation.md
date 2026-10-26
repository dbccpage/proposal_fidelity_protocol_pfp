# Lesson 300.24 — Green-Schwarz Anomaly Cancellation

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_300_24_green_schwarz_anomaly_cancellation.ipynb](../notebooks/lesson_300_24_green_schwarz_anomaly_cancellation.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Counterterm coupling d_3 C = Tr(F cup F) yielding Phi_4 = 0

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of green-schwarz anomaly cancellation.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of green-schwarz anomaly cancellation over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What remains when a declared 4-cochain is cancelled by the same cochain?

- **A:** 0. This is one finite cancellation, not a Green-Schwarz theorem.
- **B:** The original cochain.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that counterterm coupling d_3 c = tr(f cup f) yielding phi_4 = 0 continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction
source = (Fraction(1), Fraction(0), Fraction(0), Fraction(0))
counterterm = (Fraction(0), Fraction(0), Fraction(0), Fraction(0))
residual = tuple(source[index] - counterterm[index] for index in range(4))
assert residual != (Fraction(0), Fraction(0), Fraction(0), Fraction(0))
print("A zero counterterm leaves the source")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `Anomaly Cancellation` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
