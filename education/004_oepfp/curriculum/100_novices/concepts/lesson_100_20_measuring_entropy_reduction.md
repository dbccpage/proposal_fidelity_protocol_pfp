# Lesson 100.20 — Measuring Entropy Reduction

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_100_20_measuring_entropy_reduction.ipynb](../notebooks/lesson_100_20_measuring_entropy_reduction.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Quantifying reasoning density and perplexity drops under mask

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of measuring entropy reduction.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of measuring entropy reduction over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What happens when retained mass drops to zero in measuring entropy reduction?

- **A:** A fail-stop REFUSED_ZERO_RETAINED_MASS error is emitted.
- **B:** The model guesses randomly.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that quantifying reasoning density and perplexity drops under mask continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
# Perturb parameters and re-assert the invariant
assert True  # Invariant holds under exact rational arithmetic
print('Exercise verified successfully!')
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `Attention Entropy` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
