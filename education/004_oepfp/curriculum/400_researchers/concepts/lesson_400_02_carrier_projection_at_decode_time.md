# Lesson 400.02 — Carrier Projection at Decode Time

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_400_02_carrier_projection_at_decode_time.ipynb](../notebooks/lesson_400_02_carrier_projection_at_decode_time.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Forcing 0.04% -> 100% on-carrier mass via negative infinity masking

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of carrier projection at decode time.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of carrier projection at decode time over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** After zeroing the off-carrier score, what mass does the carrier pair (1, 3) hold?

- **A:** 1. The off-carrier score is removed before normalization.
- **B:** 4/6. Masking does not change mass.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that forcing 0.04% -> 100% on-carrier mass via negative infinity masking continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction
scores = {"<a>": Fraction(1), "fluff": Fraction(1), "<b>": Fraction(1)}
carrier = {token: value for token, value in scores.items() if token.startswith("<")}
assert sum(carrier.values()) == 2
print("Masking changes which scores remain")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `CarrierProjection` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
