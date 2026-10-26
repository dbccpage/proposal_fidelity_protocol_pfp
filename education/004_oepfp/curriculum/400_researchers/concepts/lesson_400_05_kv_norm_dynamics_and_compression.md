# Lesson 400.05 — KV-Norm Dynamics and Compression

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_400_05_kv_norm_dynamics_and_compression.ipynb](../notebooks/lesson_400_05_kv_norm_dynamics_and_compression.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Frobenius norm invariance and 71% context memory compression

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of kv-norm dynamics and compression.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of kv-norm dynamics and compression over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What squared norm remains after dropping the last coordinate of (1, 2, 2)?

- **A:** 5. The full squared norm is 9. No percent compression is claimed.
- **B:** 9. Dropping a coordinate preserves the norm.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that frobenius norm invariance and 71% context memory compression continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction
vector = (Fraction(3), Fraction(0), Fraction(4))
assert sum(value * value for value in vector) == 25
assert sum(value * value for value in vector[:-1]) == 9
print("Dropping 4 removes 16 from the squared norm")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `KV-Norm Mechanics` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
