# Lesson 400.07 — Purity, von Neumann Entropy, Coherence

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_400_07_purity_von_neumann_entropy_coherence.ipynb](../notebooks/lesson_400_07_purity_von_neumann_entropy_coherence.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Trace-diagnostics of quantum coherence on reasoning paths

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of purity, von neumann entropy, coherence.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of purity, von neumann entropy, coherence over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What is the purity Tr(rho^2) of diagonal (1/2, 1/2), and of (1, 0)?

- **A:** 1/2 and 1. von Neumann entropy is not computed.
- **B:** Both 1.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that trace-diagnostics of quantum coherence on reasoning paths continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction

def purity(diagonal):
    return sum(value * value for value in diagonal)

assert purity((Fraction(1, 3), Fraction(1, 3), Fraction(1, 3))) == Fraction(1, 3)
print("A wider uniform diagonal is less pure")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `density_matrix.rs` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
