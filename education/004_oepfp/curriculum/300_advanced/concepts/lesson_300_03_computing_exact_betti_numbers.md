# Lesson 300.03 — Computing Exact Betti Numbers

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_300_03_computing_exact_betti_numbers.ipynb](../notebooks/lesson_300_03_computing_exact_betti_numbers.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Calculating dimensions of ker(d_k) / im(d_{k+1}) over Q and F_2

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of computing exact betti numbers.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of computing exact betti numbers over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What Betti pair (b0, b1) does this triangle graph have?

- **A:** (1, 1). One component and one independent cycle.
- **B:** (1, 0). Every connected graph is a tree.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that calculating dimensions of ker(d_k) / im(d_{k+1}) over q and f_2 continues to hold under small perturbations.

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
rank_delta = rank_over_q(path)
assert (3 - rank_delta, 2 - rank_delta) == (1, 0)
print("The path is a tree: b0 1, b1 0")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `Betti Numbers` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |

---

## Integrated System Verification

This lesson integrates the system integration test suite from `03_survivor_birth_and_death.ipynb`:
**Topic:** Track which obstruction changed, not just how many remain (Survivor Birth & Death)

### Key Verified Invariants:
- Exact rational evaluation and Cayley-Menger / determinant arithmetic under zero-float constraints.
- Fail-stop refusal testing on corrupted bounds, invalid certificates, or degenerate structures.
- Full verification of discrete invariants across topological and combinatorial models.

