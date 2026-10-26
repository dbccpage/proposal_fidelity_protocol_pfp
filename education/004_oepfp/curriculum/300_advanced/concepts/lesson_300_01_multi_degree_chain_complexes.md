# Lesson 300.01 — Multi-Degree Chain Complexes

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_300_01_multi_degree_chain_complexes.ipynb](../notebooks/lesson_300_01_multi_degree_chain_complexes.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** Higher-degree chain spaces C_k -> C_{k-1} -> ... -> C_0

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of multi-degree chain complexes.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of multi-degree chain complexes over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** For one oriented triangle, what is (dim C2, dim C1, dim C0)?

- **A:** (1, 3, 3).
- **B:** (3, 3, 1), the reverse grading.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that higher-degree chain spaces c_k -> c_{k-1} -> ... -> c_0 continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
chain = {"C2": 0, "C1": 2, "C0": 3}
assert (chain["C2"], chain["C1"], chain["C0"]) == (0, 2, 3)
print("A path is a different complex")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `N3_simplices` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
