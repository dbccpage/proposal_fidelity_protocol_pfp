# Lesson 200.08 — Exact Subspaces B^1 and Z^1

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_200_08_exact_subspaces_b_1_and_z_1.ipynb](../notebooks/lesson_200_08_exact_subspaces_b_1_and_z_1.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Coboundaries, cocycles, and the quotient homology H^1

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of exact subspaces b^1 and z^1.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of exact subspaces b^1 and z^1 over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What is dim C1 minus rank(delta0) for the directed triangle?

- **A:** 1. Three edges, incidence rank 2.
- **B:** 0. The incidence matrix is invertible.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that coboundaries, cocycles, and the quotient homology h^1 continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
from fractions import Fraction
def rank_over_q(rows):
    acc = [[Fraction(entry) for entry in row] for row in rows]
    if not acc:
        return 0
    row_count = len(acc)
    col_count = len(acc[0])
    rank = 0
    col = 0
    while rank < row_count and col < col_count:
        pivot = next((r for r in range(rank, row_count) if acc[r][col] != 0), None)
        if pivot is None:
            col += 1
            continue
        acc[rank], acc[pivot] = acc[pivot], acc[rank]
        scale = acc[rank][col]
        for other in range(row_count):
            if other == rank or acc[other][col] == 0:
                continue
            factor = acc[other][col] / scale
            for cursor in range(col, col_count):
                acc[other][cursor] -= factor * acc[rank][cursor]
        rank += 1
        col += 1
    return rank
path = ((-1, 1, 0), (0, -1, 1))
assert rank_over_q(path) == 2
assert 2 - rank_over_q(path) == 0
print("A path of two edges has no leftover cycle dimension")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `Cohomology` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |

---

## Integrated System Verification

This lesson integrates the system integration test suite from `01_nilpotence_and_missing_boundaries.ipynb`:
**Topic:** Check a boundary before trusting a chain law (Nilpotence & Missing Boundaries)

### Key Verified Invariants:
- Deterministic boundary / primal-dual certificate verification under exact rational constraints.
- Fail-stop refusal testing on corrupted bounds, missing boundaries, or broken dual closure.
- Full parity between exact discrete representations and algorithmic solvers.

