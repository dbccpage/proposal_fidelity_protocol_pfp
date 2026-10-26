# Lesson 200.12 — Dual Circulation Certificates

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_200_12_dual_circulation_certificates.ipynb](../notebooks/lesson_200_12_dual_circulation_certificates.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Dual LP circulations certifying maximum lower bounds on defect

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of dual circulation certificates.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of dual circulation certificates over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What does the cycle (1, 1, 1) pair to against (1, 0, 0)?

- **A:** 1, and it pairs to 0 against every coboundary.
- **B:** 0, because two of the three edges are zero.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that dual lp circulations certifying maximum lower bounds on defect continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction
cycle = (Fraction(1), Fraction(1), Fraction(1))
cochain = (Fraction(2), Fraction(-1), Fraction(0))
assert sum(cycle[index] * cochain[index] for index in range(3)) == 1
print("The same cycle still sees circulation 1")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `LP Dual` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
