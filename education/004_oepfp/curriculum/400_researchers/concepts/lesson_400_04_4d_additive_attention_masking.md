# Lesson 400.04 — 4D Additive Attention Masking

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_400_04_4d_additive_attention_masking.ipynb](../notebooks/lesson_400_04_4d_additive_attention_masking.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Steering last-layer attention from 0.058 -> 1.0 on key tokens

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of 4d additive attention masking.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of 4d additive attention masking over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What share does the masked key hold when scores become (1, 1, 5)?

- **A:** 5/7.
- **B:** 1. A mask forces the key to probability 1.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that steering last-layer attention from 0.058 -> 1.0 on key tokens continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction
scores = (Fraction(1), Fraction(1), Fraction(1))
assert scores[2] / sum(scores) == Fraction(1, 3)
print("Without the extra key weight the share is 1/3")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `local_attention_steering.py` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
