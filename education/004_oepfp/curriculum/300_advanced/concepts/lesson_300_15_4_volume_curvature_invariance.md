# Lesson 300.15 — 4-Volume Curvature Invariance

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_300_15_4_volume_curvature_invariance.ipynb](../notebooks/lesson_300_15_4_volume_curvature_invariance.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Proving d_3 d_2 = 0 on discrete 4-dimensional manifolds

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of 4-volume curvature invariance.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of 4-volume curvature invariance over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** What is d of d on the triangle edge chain?

- **A:** The zero vertex chain.
- **B:** The original edge chain.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that proving d_3 d_2 = 0 on discrete 4-dimensional manifolds continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
edges = ((0, 1),)
vertex = [0, 0]
vertex[0] -= 1
vertex[1] += 1
assert tuple(vertex) == (-1, 1)
print("d of one edge is not zero; d d is a second application")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `d3 d2 = 0` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |

---

## Integrated System Verification

This lesson integrates the system integration test suite from `04_transfer_trace_and_shadow.ipynb`:
**Topic:** Compute a finite transfer shadow without extending its meaning (Transfer Trace & Shadow)

### Key Verified Invariants:
- Exact rational evaluation and Cayley-Menger / determinant arithmetic under zero-float constraints.
- Fail-stop refusal testing on corrupted bounds, invalid certificates, or degenerate structures.
- Full verification of discrete invariants across topological and combinatorial models.

