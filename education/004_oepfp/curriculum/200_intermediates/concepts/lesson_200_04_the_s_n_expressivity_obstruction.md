# Lesson 200.04 — The S_n Expressivity Obstruction

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_200_04_the_s_n_expressivity_obstruction.ipynb](../notebooks/lesson_200_04_the_s_n_expressivity_obstruction.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Cohomology classes o_n in H^1 bounding expressivity

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of the s_n expressivity obstruction.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of the s_n expressivity obstruction over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** Is the cochain (1, 1, 1) on a directed triangle a coboundary?

- **A:** No. Its circulation is 3, and every coboundary circulates 0.
- **B:** Yes. Equal edge values are always a vertex potential.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that cohomology classes o_n in h^1 bounding expressivity continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction
repaired = (Fraction(1), Fraction(0), Fraction(-1))
assert sum(repaired) == 0
broken = (Fraction(1), Fraction(1), Fraction(1))
assert sum(broken) != 0
print("A circulation of 0 is the coboundary obstruction test on this triangle")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `PO-032 §3.7` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |

---

## Integrated System Verification

This lesson integrates the system integration test suite from `03_quantifier_order.ipynb`:
**Topic:** Changing quantifier order changes the question (Quantifier Alternation Obstruction)

### Key Verified Invariants:
- Deterministic boundary / primal-dual certificate verification under exact rational constraints.
- Fail-stop refusal testing on corrupted bounds, missing boundaries, or broken dual closure.
- Full parity between exact discrete representations and algorithmic solvers.

