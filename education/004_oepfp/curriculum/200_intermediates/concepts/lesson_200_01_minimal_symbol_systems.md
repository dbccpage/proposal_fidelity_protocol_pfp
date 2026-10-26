# Lesson 200.01 — Minimal Symbol Systems

## How to use this lesson

Read this page first. It is the lesson in prose.

Then open [lesson_200_01_minimal_symbol_systems.ipynb](../notebooks/lesson_200_01_minimal_symbol_systems.ipynb) and run the cells from top to bottom. Stop when the checks pass.

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

**Core Concept:** The MSS-0 to MSS-100 arity filtration and tower architecture

### The Four-Tier Perspective
- **Tangible (Age 5–10):** Physical intuition of minimal symbol systems.
- **Algorithmic (Age 11–17):** Deterministic state transitions and rule sets.
- **Discrete Math (Undergrad):** Exact rational invariants and coboundary calculus.
- **Foundational (Age 50–500):** Monotone manifold retraction and topological obstruction theory.

## 2. Scope & Claim Boundary

| CAN Show in this Lesson | CANNOT Show in this Lesson |
| :--- | :--- |
| Exact discrete calculation of minimal symbol systems over rational arithmetic. | Generalization to unconstrained continuous LLM weights. |
| Deterministic invariant verification under declared assumptions. | Universal mathematical proof outside declared finite domain. |

## 3. Diagnostic Probe (2026 Micro-Attention Check)

**Question:** How many binary applications of depth 1 do two atoms give?

- **A:** 4, from 2 times 2.
- **B:** The same count as the atoms.

## 4. Student Exercise

**Task:** Modify the input parameters in the code cell above to verify that the mss-0 to mss-100 arity filtration and tower architecture continues to hold under small perturbations.

### Hidden Solution
<details>
<summary>Click to view solution</summary>

```python
atoms = ("a", "b", "c")
depth0 = len(atoms)
depth1 = len(atoms) * len(atoms)
assert depth0 == 3
assert depth1 == 9
print("Three atoms give", depth1, "binary depth-1 words")
```
</details>

## 5. Anchors

| Anchor Type | Target Link |
| :--- | :--- |
| **Curriculum Anchor** | `NOTEBOOK_PLAN_MSSN.md` |
| **Authority Effect** | `None` |
| **Zero-Float Law** | Enforced (`fractions.Fraction` or exact integers) |
